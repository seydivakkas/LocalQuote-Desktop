"""Windows preview provenance: native families, actual license texts, SHA-256 and ZIP verification.

This collector is deliberately fail-closed on missing core notices and unknown
native file families. It never declares the commercial release authorized.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

NATIVE_SUFFIXES = {".exe", ".pyd", ".dll"}
FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".woff", ".woff2", ".pfb"}
SOURCE_URLS = {
    "CPython": "https://docs.python.org/3/license.html",
    "Tcl": "https://www.tcl-lang.org/software/tcltk/license.html",
    "Tk": "https://www.tcl-lang.org/software/tcltk/license.html",
    "SQLite": "https://sqlite.org/copyright.html",
    "OpenSSL": "https://www.openssl.org/source/license.html",
    "libffi": "https://github.com/libffi/libffi/blob/master/LICENSE",
    "zlib": "https://zlib.net/zlib_license.html",
    "Microsoft C runtime": "https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def family(rel: str) -> str:
    s = rel.lower().replace("\\", "/")
    base = s.split("/")[-1]
    if s.endswith(".exe"):
        return "PyInstaller bootloader / LocalQuote"
    if "/pil/" in s and s.endswith(".pyd"):
        return "Pillow native extensions"
    if "/charset_normalizer/" in s and s.endswith(".pyd"):
        return "charset-normalizer native extensions"
    if base in ("tcl86t.dll", "tk86t.dll", "_tkinter.pyd"):
        return "Tcl/Tk"
    if base in ("_sqlite3.pyd", "sqlite3.dll"):
        return "SQLite / CPython"
    if base.startswith(("libssl", "libcrypto")) and base.endswith(".dll"):
        return "OpenSSL"
    if base.startswith("libffi") and base.endswith(".dll"):
        return "libffi"
    if base.startswith("zlib") and base.endswith(".dll"):
        return "zlib"
    if base.startswith("api-ms-win-") or base.startswith("vcruntime") or base == "ucrtbase.dll":
        return "Microsoft C runtime"
    if base.startswith("python3") and base.endswith(".dll"):
        return "CPython runtime"
    if base.endswith(".pyd") and s.startswith("_internal/") and s.count("/") == 1:
        if base.startswith("_") or base in ("pyexpat.pyd", "select.pyd", "unicodedata.pyd"):
            return "CPython standard extensions"
        return "UNCLASSIFIED"
    return "UNCLASSIFIED"

def find_python_license(python_home: Path) -> Path | None:
    paths = [python_home / "LICENSE.txt", python_home / "LICENSE",
             python_home / "LICENSE.md", python_home / "Doc" / "license.rst"]
    return next((p for p in paths if p.is_file()), None)

def stage_notice(src: Path | None, dest: Path, findings: list, component: str) -> None:
    if src is None:
        findings.append("MISSING_NOTICE: " + component)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

def stage_licenses(bundle: Path, python_home: Path, findings: list) -> dict:
    notices = bundle / "THIRD_PARTY_LICENSES"
    stage_notice(find_python_license(python_home), notices / "CPython" / "LICENSE.txt", findings, "CPython")
    tk = bundle / "_internal" / "_tk_data" / "license.terms"
    stage_notice(tk if tk.is_file() else None, notices / "Tk" / "license.terms", findings, "Tk")
    tcl_candidates = [
        bundle / "_internal" / "_tcl_data" / "license.terms",
        python_home / "tcl" / "tcl8.6" / "license.terms",
        python_home / "tcl" / "tcl8.7" / "license.terms",
        python_home / "Lib" / "tkinter" / "license.terms",
    ]
    tcl = next((p for p in tcl_candidates if p.is_file()), None)
    if tcl is None:
        vendored = Path(__file__).resolve().parents[1] / "licenses" / "upstream" / "Tcl-8.6-license.terms"
        if vendored.is_file():
            tcl = vendored
            findings.append("MANUAL_PROVENANCE_REVIEW: Tcl license comes from pinned upstream source, not installed runtime")
    stage_notice(tcl, notices / "Tcl" / "license.terms", findings, "Tcl")
    return {
        "CPython": (notices / "CPython" / "LICENSE.txt").is_file(),
        "Tcl": (notices / "Tcl" / "license.terms").is_file(),
        "Tk": (notices / "Tk" / "license.terms").is_file(),
    }

def collect(bundle: Path, python_home: Path, evidence: Path, commit: str) -> dict:
    if not (bundle / "LocalQuote-Desktop.exe").is_file():
        raise ValueError("Missing EXE")
    evidence.mkdir(parents=True, exist_ok=True)
    missing = []
    notices = stage_licenses(bundle, python_home, missing)
    files = []
    native = []
    fonts = []
    for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
        rel = path.relative_to(bundle).as_posix()
        entry = {"path": rel, "size": path.stat().st_size, "sha256": sha256(path)}
        files.append(entry)
        if path.suffix.lower() in FONT_SUFFIXES:
            fonts.append(rel)
        if path.suffix.lower() in NATIVE_SUFFIXES:
            native.append(dict(entry, family=family(rel)))
    unknown = [v["path"] for v in native if v["family"] == "UNCLASSIFIED"]
    if unknown:
        missing.extend("UNKNOWN_NATIVE: " + x for x in unknown)
    report = {
        "schema": "localquote-native-provenance-v1",
        "commit": commit,
        "python": sys.version.split()[0],
        "python_home": str(python_home),
        "component_reference_urls": SOURCE_URLS,
        "collected_notices": notices,
        "file_count": len(files),
        "native_count": len(native),
        "native": native,
        "bundled_font_paths": fonts,
        "blocking_findings": missing + (["BUNDLED_FONT_RIGHTS_UNREVIEWED"] if fonts else []),
        "manual_review": [
            "Microsoft C runtime redistributable terms and precise DLL origin",
            "Pillow compiled codecs and any embedded third-party notices",
            "OpenSSL / libffi / zlib binary licensing notices and upstream provenance",
            "ReportLab bundled/embedded fonts and customer OS font embedding terms",
            "Tcl/Tk and CPython notice contents must match actual redistributables",
            "Owner-controlled commercial end-user/source license not decided",
            "Independent rebuild / reproducibility and Windows offline GUI acceptance deferred"
        ],
        "release_decision": "HOLD",
    }
    (evidence / "native-components.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence / "package-file-hashes.json").write_text(
        json.dumps({"commit":commit,"files":files},ensure_ascii=False,indent=2),encoding="utf-8")
    # Deterministic file order and ZipInfo timestamps, independent of mtimes.
    archive = evidence / "LocalQuote-Windows-preview-integrity.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for entry in files:
            info = zipfile.ZipInfo(entry["path"], date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (bundle / entry["path"]).read_bytes())
    with zipfile.ZipFile(archive) as z:
        if sorted(z.namelist()) != sorted(x["path"] for x in files):
            raise AssertionError("Archive file set differs from manifest")
        for entry in files:
            if hashlib.sha256(z.read(entry["path"])).hexdigest() != entry["sha256"]:
                raise AssertionError("Archive hash mismatch: " + entry["path"])
    (evidence / "archive-sha256.txt").write_text(
        f"{sha256(archive)}  {archive.name}\n",encoding="utf-8")
    print(json.dumps({
        "file_count":len(files),"native_count":len(native),"notices":notices,
        "unknown_native":unknown,"blocking_findings":report["blocking_findings"],
        "preview_archive_sha256":sha256(archive),"release_decision":"HOLD"},indent=2))
    return report

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--python-home",type=Path,default=Path(sys.base_prefix))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--commit",default=os.getenv("GITHUB_SHA","UNSPECIFIED"))
    p.add_argument("--strict",action="store_true")
    a=p.parse_args()
    report=collect(a.bundle,a.python_home,a.output,a.commit)
    return 1 if a.strict and report["blocking_findings"] else 0

if __name__=="__main__":
    raise SystemExit(main())
