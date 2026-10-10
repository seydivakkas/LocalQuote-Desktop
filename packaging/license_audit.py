"""LocalQuote release audit evidence; does not constitute legal approval.

Run using the *isolated runtime* Python interpreter to avoid build-only packages.
No network or third-party dependency is needed for this collector.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import sys

RUNTIME = {
    "reportlab": ("4.4.9", "BSD-3-Clause"),
    "pillow": ("12.3.0", "MIT-CMU"),
    "charset-normalizer": ("3.4.7", "MIT"),
}
TOOLS = {"pip", "setuptools", "wheel", "localquote-desktop"}
FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".woff", ".woff2", ".pfb", ".sfd"}


def normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def sha256(file: Path) -> str:
    digest = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_license_files(dist: metadata.Distribution, outdir: Path) -> list[dict]:
    candidates = dist.metadata.get_all("License-File", []) or []
    for file in dist.files or []:
        rel = str(file).replace("\\", "/")
        if ".dist-info/licenses/" in rel and any(term in rel.split("/")[-1].lower() for term in ("license", "copying", "notice")):
            candidates.append(rel)
    found = []
    for item in sorted(set(candidates)):
        possible = [item]
        if not ".dist-info/" in item:
            possible += [f"{dist._path.name}/licenses/{item}", f"{dist._path.name}/{item}"]
        src = next((dist.locate_file(p) for p in possible if Path(dist.locate_file(p)).is_file()), None)
        if src is None:
            continue
        dst = outdir / (Path(item).name if len(found) == 0 else f"{len(found)}-{Path(item).name}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        found.append({"name": dst.name, "sha256": sha256(dst), "bytes": dst.stat().st_size})
    return found


def inspect_bundle(bundle: Path | None) -> dict:
    if bundle is None:
        return {"status": "NOT_PROVIDED", "files": [], "fonts": []}
    if not bundle.is_dir():
        raise ValueError(f"Bundle directory does not exist: {bundle}")
    files = []
    fonts = []
    for file in sorted(bundle.rglob("*")):
        if not file.is_file():
            continue
        path = file.relative_to(bundle).as_posix()
        item = {"path": path, "size": file.stat().st_size, "sha256": sha256(file)}
        files.append(item)
        if file.suffix.lower() in FONT_SUFFIXES:
            fonts.append(item)
    if not files:
        raise ValueError("Bundle directory is empty")
    return {"status": "FONT_REVIEW_REQUIRED" if fonts else "INVENTORIED", "files": files, "fonts": fonts}


def audit(output: Path, bundle: Path | None = None, *, strict: bool = True) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    notice_root = output / "notices"
    installed = {normalized(d.metadata["Name"]): d for d in metadata.distributions() if d.metadata.get("Name")}
    errors = []
    components = []
    for name, (version, spdx) in sorted(RUNTIME.items()):
        dist = installed.get(name)
        if dist is None:
            errors.append(f"Missing runtime dependency: {name}")
            continue
        if dist.version != version:
            errors.append(f"Wrong version {name}: expected {version}, got {dist.version}")
        notices = collect_license_files(dist, notice_root / f"{name}-{dist.version}")
        if not notices:
            errors.append(f"Missing embedded license notice: {name}")
        components.append({
            "name": name, "version": dist.version, "spdx_reviewed": spdx,
            "metadata_license": dist.metadata.get("License-Expression") or dist.metadata.get("License") or "UNKNOWN",
            "license_texts": notices, "purl": f"pkg:pypi/{name}@{dist.version}",
        })
    runtime_extras = sorted(set(installed) - set(RUNTIME) - TOOLS)
    if strict and runtime_extras:
        errors.append("Unexpected packages in isolated runtime environment: " + ", ".join(runtime_extras))
    if bundle is not None:
        portable_notices = bundle / "THIRD_PARTY_LICENSES"
        for component in components:
            src = notice_root / f"{component['name']}-{component['version']}"
            dst = portable_notices / src.name
            dst.mkdir(parents=True, exist_ok=True)
            for source in src.glob("*"):
                if source.is_file():
                    shutil.copyfile(source, dst / source.name)
    bundle_report = inspect_bundle(bundle)
    (output / "bundle-manifest.json").write_text(json.dumps(bundle_report, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "schema": "localquote-license-evidence-v1", "python": sys.version.split()[0],
        "components": components, "unapproved_runtime_packages": runtime_extras,
        "errors": errors, "bundle_status": bundle_report["status"],
        "bundle_file_count": len(bundle_report["files"]),
        "bundled_fonts": [x["path"] for x in bundle_report["fonts"]],
        "manual_release_gates": [
            "CPython runtime license text and full Tcl/Tk, SQLite notices in packaged executable",
            "ReportLab bundled fonts and font embedding rights verified for exact binary",
            "Check distribution of embedded third-party C/native libraries, especially Pillow",
            "Application-owned license / commercial customer usage rights approved by owner",
            "Independent Windows offline end-user acceptance (#2 and #4)",
            "Independent reproducibility and exact signed artifact hashes",
        ],
        "release_decision": "HOLD",
    }
    (output / "license-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "components"}, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--allow-extras", action="store_true", help="Only for local development diagnostics")
    args = parser.parse_args()
    try:
        report = audit(args.output, args.bundle, strict=not args.allow_extras)
    except (ValueError, OSError) as exc:
        print(f"License audit I/O error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
