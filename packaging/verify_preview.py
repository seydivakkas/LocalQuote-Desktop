"""Offline verify a Windows preview ZIP against published SHA-256 manifests.

Does not run the executable or validate license rights. Never extracts paths.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

def hash_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def verify(archive: Path, hashfile: Path, manifest: Path) -> int:
    reference=hashfile.read_text(encoding="utf-8").strip().split()
    if len(reference)!=2 or not re.fullmatch(r"[a-f0-9]{64}",reference[0]) or reference[1]!=archive.name:
        raise ValueError("Invalid archive hash file")
    if hash_file(archive)!=reference[0]:
        raise ValueError("Archive SHA-256 mismatch")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    entries=data["files"]
    expected={x["path"]: x for x in entries}
    if len(expected)!=len(entries):
        raise ValueError("Duplicate manifest path")
    for p in expected:
        segments=p.split("/")
        if p.startswith("/") or "\\" in p or any(s in (".","..","") for s in segments):
            raise ValueError("Unsafe manifest path")
    with ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(expected):
            raise ValueError("ZIP membership mismatch")
        for name in names:
            b=z.read(name)
            x=expected[name]
            if len(b)!=x["size"] or hashlib.sha256(b).hexdigest()!=x["sha256"]:
                raise ValueError("File differs: "+name)
    return len(entries)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--hash",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    a=p.parse_args()
    print("PASS: independently verified",verify(a.zip,a.hash,a.manifest),"ZIP members")
