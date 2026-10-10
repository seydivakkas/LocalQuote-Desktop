"""Pin downloaded Windows wheels to SHA-256 before installing the exact same bytes.

This is an *ephemeral CI lock*, NOT a pre-reviewed trusted hash lock.
The output binds audit and packaged runtime to the same local wheels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def norm(s: str) -> str:
    return s.lower().replace("_", "-").replace(".", "-")

def generate(wheels: Path, lock: Path, out: Path, inventory: Path) -> dict:
    requirements = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line or line.count("==") != 1:
            raise ValueError("Only name==version pins are allowed: " + line)
        name, ver = line.split("==", 1)
        requirements[norm(name)] = ver
    if not requirements:
        raise ValueError("Empty lock")
    found = {}
    for wheel in sorted(wheels.glob("*.whl")):
        with ZipFile(wheel) as z:
            metadata_paths = [p for p in z.namelist() if p.endswith(".dist-info/METADATA")]
            if len(metadata_paths) != 1:
                raise ValueError("Invalid wheel metadata: " + wheel.name)
            info = Parser().parsestr(z.read(metadata_paths[0]).decode("utf-8"))
            key = norm(info["Name"])
            version = info["Version"]
        if key not in requirements or requirements[key] != version or key in found:
            raise ValueError("Unexpected/duplicate wheel: " + wheel.name)
        found[key] = {"filename": wheel.name, "version": version, "sha256": digest(wheel)}
    if set(found) != set(requirements):
        raise ValueError("Missing wheels: " + repr(sorted(set(requirements) - set(found))))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(
        f"{key}=={found[key]['version']} --hash=sha256:{found[key]['sha256']}\n"
        for key in sorted(found)), encoding="utf-8")
    report = {"schema": "localquote-wheel-provenance-v1",
              "limitations": ["Hashes calculated after initial download; independent upstream trust review pending",
                              "Build-tool transitive wheels are not hash-locked"],
              "wheels": found}
    inventory.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--wheelhouse", type=Path, required=True)
    p.add_argument("--lock", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    a=p.parse_args()
    print("Pinned runtime wheels:", sorted(generate(a.wheelhouse,a.lock,a.out,a.manifest)["wheels"]))
if __name__ == "__main__":
    main()
