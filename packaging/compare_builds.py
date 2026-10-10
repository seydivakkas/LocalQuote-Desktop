"""Compare two independent Windows builds, never assume byte-for-byte reproducibility."""
import argparse,json
from pathlib import Path
from native_provenance import sha256

def compare(a:Path,b:Path,out:Path):
    left={x["path"]:x["sha256"] for x in json.loads(a.read_text(encoding="utf-8"))["files"]}
    right={x["path"]:x["sha256"] for x in json.loads(b.read_text(encoding="utf-8"))["files"]}
    changed=[p for p in sorted(left.keys() & right.keys()) if left[p]!=right[p]]
    report={"schema":"localquote-double-build-v1","identical":not(changed or left.keys()!=right.keys()),
            "first_count":len(left),"second_count":len(right),
            "only_first":sorted(left.keys()-right.keys()),"only_second":sorted(right.keys()-left.keys()),
            "different_files":changed,"decision":"PASS" if not(changed or left.keys()!=right.keys()) else "DIFFERENCES_REVIEW_REQUIRED",
            "note":"Two GitHub runners, same commit; matching hashes prove this run, not supply-chain security."}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for field in ("first","second","out"):p.add_argument("--"+field,type=Path,required=True)
    a=p.parse_args()
    report=compare(a.first,a.second,a.out)
    # difference should remain visible; fail the reproducibility gate, not suppress it
    raise SystemExit(0 if report["identical"] else 1)
