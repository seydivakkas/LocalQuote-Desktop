"""Check all final native binaries have congruent source and Windows PE evidence.

Checks evidence integrity, not redistribution rights or publisher authenticity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def validate(source:Path, pe:Path, manifest:Path, out:Path) -> dict:
    sources=json.loads(source.read_text(encoding="utf-8"))["native_files"]
    versions=json.loads(pe.read_text(encoding="utf-8"))["files"]
    files=json.loads(manifest.read_text(encoding="utf-8"))["files"]
    expected={x["path"]:x["sha256"] for x in files if x["path"].lower().endswith((".exe",".dll",".pyd"))}
    findings=[]
    for name, entries in (("source",sources),("pe",versions)):
        if len({x["path"] for x in entries})!=len(entries):
            findings.append("DUPLICATE_"+name)
        actual={x["path"]:x["sha256"].lower() for x in entries}
        if expected!=actual:
            findings.append("INCONSISTENT_"+name+"_INVENTORY")
    missing_versions=[x["path"] for x in versions if not x.get("file_version") and not x.get("product_version")]
    untrusted_signatures=[x["path"] for x in versions if x.get("authenticode_status")!="Valid"]
    result={"schema":"localquote-native-cross-evidence-v1",
            "native_file_count":len(expected),
            "evidence_errors":findings,
            "unsigned_or_nonvalid_count":len(untrusted_signatures),
            "missing_version_resource_count":len(missing_versions),
            "missing_version_resource_paths":missing_versions,
            "nonvalid_signature_paths":untrusted_signatures,
            "note":"PE missing versions or signatures are review signals, not automatic licensing violations.",
            "release_decision":"HOLD"}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    for field in ("source","pe","manifest","out"):
        a.add_argument("--"+field,required=True,type=Path)
    args=a.parse_args()
    report=validate(args.source,args.pe,args.manifest,args.out)
    print(json.dumps({k:v for k,v in report.items() if not k.endswith("_paths")},indent=2))
    raise SystemExit(bool(report["evidence_errors"]))
