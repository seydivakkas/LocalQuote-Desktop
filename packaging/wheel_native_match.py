"""Bind frozen native files to exact runtime wheel member bytes.

For each Python native extension, first attempt SHA-256 matching against
wheel entries. This proves byte-identical provenance, not license clearance.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from zipfile import ZipFile

def digest(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()

def inspect(bundle:Path, wheelhouse:Path, output:Path)->dict:
    wheel_entries={}
    for whl in sorted(wheelhouse.glob("*.whl")):
        with ZipFile(whl) as z:
            for name in z.namelist():
                if name.lower().endswith((".pyd",".dll")):
                    h=digest(z.read(name))
                    wheel_entries.setdefault(h,[]).append({"wheel":whl.name,"member":name})
    matched=[]; unmatched=[]
    for file in sorted(bundle.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in (".pyd",".dll"):
            continue
        path=file.relative_to(bundle).as_posix()
        h=digest(file.read_bytes())
        evidence={"path":path,"sha256":h}
        if h in wheel_entries:
            matched.append(dict(evidence,origin=wheel_entries[h]))
        else:
            unmatched.append(evidence)
    mypyc=[x for x in matched+unmatched if "__mypyc" in x["path"].lower()]
    findings=[] if mypyc and all(x in matched for x in mypyc) else ["MYPYC_WHEEL_BYTE_MATCH_NOT_PROVEN"]
    result={"schema":"localquote-wheel-native-match-v1","matched":matched,"unmatched":unmatched,
            "mypyc":mypyc,"findings":findings,"release_decision":"HOLD",
            "note":"Unmatched CPython/system DLLs are expected; native license verification remains independent."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"matched":len(matched),"unmatched":len(unmatched),"mypyc":mypyc,"findings":findings},ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--wheelhouse",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=inspect(a.bundle,a.wheelhouse,a.out)
    raise SystemExit(bool(result["findings"]))
