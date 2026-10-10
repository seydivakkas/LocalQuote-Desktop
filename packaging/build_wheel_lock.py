"""Hash/download complete pinned build dependency wheel closure.

The resulting ephemeral hash set is only a same-run byte identity proof,
not a pretrusted upstream source or reproducibility guarantee.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from wheel_provenance import digest, norm
from zipfile import ZipFile
from email.parser import Parser

def collect(wheelhouse:Path, out:Path, manifest:Path):
    records={}
    for wheel in sorted(wheelhouse.glob("*.whl")):
        with ZipFile(wheel) as z:
            ms=[p for p in z.namelist() if p.endswith(".dist-info/METADATA") and p.count("/")==1]
            if len(ms)!=1: raise ValueError("Invalid wheel "+wheel.name)
            data=Parser().parsestr(z.read(ms[0]).decode("utf-8"))
        name=norm(data["Name"]); version=data["Version"]
        if name in records: raise ValueError("Duplicate distribution "+name)
        records[name]={"version":version,"file":wheel.name,"sha256":digest(wheel)}
    if "pyinstaller" not in records or records["pyinstaller"]["version"]!="6.22.3":
        raise ValueError("Expected pinned PyInstaller 6.22.3")
    if not records: raise ValueError("No wheels")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("".join(f"{name}=={x['version']} --hash=sha256:{x['sha256']}\n" for name,x in sorted(records.items())),encoding="utf-8")
    manifest.write_text(json.dumps({"components":records,"limitations":["hashes derived during CI download; not pretrusted"]},indent=2),encoding="utf-8")
    return records

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--wheelhouse",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    a=p.parse_args()
    print("Build wheels:",sorted(collect(a.wheelhouse,a.out,a.manifest)))
