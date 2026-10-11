"""Archive full license/notice files from hash-controlled *build* wheels.

Includes nested vendored distributions in setuptools. Does not conclude
PyInstaller bootloader exception or any customer redistribution license.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def collect(wheelhouse:Path, expected:Path, out:Path)->dict:
    pins=json.loads(expected.read_text(encoding="utf-8"))["components"]
    all_notices=[];errors=[]
    for name,meta in sorted(pins.items()):
        whl=wheelhouse/meta["file"]
        if not whl.is_file() or sha(whl.read_bytes())!=meta["sha256"]:
            errors.append("WHEEL_BYTE_MISMATCH: "+name)
            continue
        count=0
        with ZipFile(whl) as z:
            for path in sorted(z.namelist()):
                lower=PurePosixPath(path).name.lower()
                if not any(token in lower for token in ("license","copying","notice")):
                    continue
                if not path.endswith("/") and (".dist-info/" in path or ".dist-info/licenses/" in path):
                    data=z.read(path)
                    if not data.strip():continue
                    dest=out/"notices"/name/(sha(path.encode())[:12]+"-"+PurePosixPath(path).name)
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(data)
                    all_notices.append({"component":name,"wheel":whl.name,
                                        "member":path,"artifact":dest.relative_to(out).as_posix(),
                                        "sha256":sha(data)})
                    count+=1
        if count==0:errors.append("MISSING_BUILD_WHEEL_NOTICE: "+name)
    report={"schema":"localquote-build-wheel-license-evidence-v1","wheel_count":len(pins),
            "license_file_count":len(all_notices),"license_files":all_notices,
            "errors":errors,"legal_clearance":False,
            "note":"Wheel license files and vendored notices are evidence; actual bootloader exception and system DLL rights still need review."}
    out.mkdir(parents=True,exist_ok=True)
    (out/"build-tool-license-notices.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"wheels":len(pins),"license_files":len(all_notices),"errors":errors}))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for f in ("wheelhouse","manifest","output"):p.add_argument("--"+f,type=Path,required=True)
    a=p.parse_args()
    report=collect(a.wheelhouse,a.manifest,a.output)
    raise SystemExit(bool(report["errors"]))
