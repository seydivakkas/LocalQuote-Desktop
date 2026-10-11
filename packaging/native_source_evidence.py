"""Link each frozen native binary to an identical installed-Python/system file.

Byte identity to the build runner is useful evidence; it is NOT proof that the
upstream software publisher licensed redistribution of those bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import ssl
import sys
import tkinter
import zlib

EXTENSIONS = {".exe", ".dll", ".pyd"}
SOURCE_FAMILIES = {
    "CPython": "https://www.python.org/downloads/",
    "SQLite": "https://www.sqlite.org/copyright.html",
    "Tcl/Tk": "https://www.tcl-lang.org/software/tcltk/license.html",
    "OpenSSL": "https://www.openssl.org/source/license.html",
    "libffi": "https://github.com/libffi/libffi",
    "zlib": "https://zlib.net/zlib_license.html",
    "Pillow": "https://pillow.readthedocs.io/en/stable/installation/building-from-source.html",
    "Microsoft Windows runtime": "https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files",
}

def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def family(relative: str, wheel_origins: list[dict]) -> str:
    name=relative.lower().replace("\\", "/")
    base=name.rsplit("/",1)[-1]
    if wheel_origins:
        return "Python wheel native extension"
    if base == "localquote-desktop.exe":
        return "LocalQuote + PyInstaller bootloader"
    if base in ("tcl86t.dll","tk86t.dll","_tkinter.pyd"):
        return "Tcl/Tk"
    if base in ("_sqlite3.pyd","sqlite3.dll"):
        return "SQLite / CPython"
    if base.startswith(("libssl","libcrypto")):
        return "OpenSSL"
    if base.startswith("libffi"):
        return "libffi"
    if base.startswith("zlib"):
        return "zlib"
    if base.startswith(("api-ms-win-","ucrtbase","vcruntime")):
        return "Microsoft Windows runtime"
    if base.startswith("python3") or base.endswith(".pyd"):
        return "CPython / unverified extension"
    return "UNRESOLVED"

def candidate_index(python_home: Path, system_root: Path | None, needed: set[str]) -> dict[str,list[Path]]:
    """Index names only; do not hash the entire Python or Windows installation."""
    roots = [python_home]
    if system_root is not None:
        roots.append(system_root / "System32")
        roots.append(system_root / "SysWOW64")
    index = {}
    for root in roots:
        if not root.is_dir():
            continue
        # Scan Python's installed DLLs, binaries and package extensions.
        # Windows System32 does not need deep recursion.
        iterator = root.rglob("*") if root == python_home else root.iterdir()
        for file in iterator:
            if file.is_file() and file.name.casefold() in needed and file.suffix.lower() in EXTENSIONS:
                index.setdefault(file.name.casefold(), []).append(file)
    return index

def runtime_versions() -> dict:
    interpreter = tkinter.Tcl()
    info={"python":sys.version.split()[0],"openssl":ssl.OPENSSL_VERSION,
          "sqlite":sqlite3.sqlite_version,
          "tcl":interpreter.eval("info patchlevel"),
          "tk_compiled":str(tkinter.TkVersion),
          "zlib_compiled":zlib.ZLIB_VERSION,
          "zlib_runtime":zlib.ZLIB_RUNTIME_VERSION}
    try:
        import PIL
        info["pillow"]=PIL.__version__
    except ImportError:
        info["pillow"]="NOT_INSTALLED"
    return info

def collect(bundle:Path, python_home:Path, output:Path, *,
            wheel_match:Path|None=None, system_root:Path|None=None) -> dict:
    if not bundle.is_dir(): raise ValueError("Missing bundle")
    binaries=sorted(p for p in bundle.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if not binaries: raise ValueError("Bundle contains no native binaries")
    wheel_map={}
    if wheel_match:
        matches=json.loads(wheel_match.read_text(encoding="utf-8"))
        for r in matches["matched"]:
            wheel_map[(r["path"],r["sha256"])]=r["origin"]
    index=candidate_index(python_home,system_root,{p.name.casefold() for p in binaries})
    evidence=[]
    for binary in binaries:
        relative=binary.relative_to(bundle).as_posix()
        h=file_hash(binary)
        wheel=wheel_map.get((relative,h),[])
        peers=[]
        for origin in index.get(binary.name.casefold(),[]):
            if origin.resolve()==binary.resolve():
                continue
            if file_hash(origin)==h:
                peers.append({"type":"python-install" if origin.is_relative_to(python_home) else "windows-system",
                              "path":str(origin),"sha256":h})
        evidence.append({"path":relative,"sha256":h,"bytes":binary.stat().st_size,
                         "family":family(relative,wheel),
                         "wheel_origins":wheel,"local_byte_identical_sources":peers,
                         "source_match":"WHEEL_EXACT" if wheel else ("INSTALLED_COPY_EXACT" if peers else "NOT_PROVEN")})
    totals=Counter(x["source_match"] for x in evidence)
    unresolved=[x["path"] for x in evidence if x["source_match"]=="NOT_PROVEN"]
    report={"schema":"localquote-native-source-evidence-v1",
            "python_home":str(python_home),"source_reference_urls":SOURCE_FAMILIES,
            "runtime_versions":runtime_versions(),"native_files":evidence,
            "source_match_counts":dict(totals),"unresolved_origin_paths":unresolved,
            "notices_verified":False,
            "limitations":[
                "Installed Python or Windows file SHA match is not verified official distribution provenance",
                "A .pyd/.dll source match is not legal redistribution clearance",
                "DLL versions from Windows version resources/signatures are captured in a separate CI report",
                "Pillow and CPython may contain additional embedded third-party libraries",
                "Microsoft redistributable permissions require licensee and REDIST review",
            ],
            "release_decision":"HOLD"}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"native_files":len(evidence),"match_counts":dict(totals),
                      "unresolved_count":len(unresolved),"runtime_versions":report["runtime_versions"],
                      "release_decision":"HOLD"},ensure_ascii=False))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--python-home",type=Path,required=True)
    p.add_argument("--wheel-match",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--system-root",type=Path)
    a=p.parse_args()
    collect(a.bundle,a.python_home,a.output,
            wheel_match=a.wheel_match,system_root=a.system_root)
