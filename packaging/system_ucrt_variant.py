"""Engineer-only Windows 10/11 System-UCRT portable variant.

Leaves the original PyInstaller bundle intact. Removes ONLY direct _internal
Windows UCRT API-set forwarders and ucrtbase.dll; no VC runtime DLLs.
Not a user acceptance or commercial-redistribution authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda:f.read(1<<20),b""): h.update(piece)
    return h.hexdigest()

def ucrt_candidate(rel:str) -> bool:
    s=rel.replace("\\","/").lower()
    if not s.startswith("_internal/") or s.count("/")!=1:
        return False
    base=s.split("/")[-1]
    return (base.startswith("api-ms-win-crt-") or base.startswith("api-ms-win-core-")) and base.endswith(".dll") or base=="ucrtbase.dll"

def snapshot(root:Path) -> dict[str,dict]:
    return {p.relative_to(root).as_posix():
            {"sha256":sha(p),"bytes":p.stat().st_size}
            for p in root.rglob("*") if p.is_file()}

def make(original:Path, output:Path, report:Path, *,
         windows_major:int|None=None, system_ucrt:Path|None=None)->dict:
    if windows_major is None:
        if sys.platform!="win32": raise RuntimeError("Only real Windows may produce this candidate")
        windows_major=sys.getwindowsversion().major
    if windows_major<10: raise RuntimeError("System UCRT candidate requires Windows 10/11")
    if system_ucrt is None:
        system_ucrt=Path(os.environ.get("SystemRoot","C:/Windows"))/"System32"/"ucrtbase.dll"
    if not system_ucrt.is_file(): raise RuntimeError("System UCRT is not present")
    original=original.resolve()
    output=output.resolve()
    if not (original/"LocalQuote-Desktop.exe").is_file(): raise ValueError("Original executable missing")
    if original==output or original in output.parents or output in original.parents:
        raise ValueError("Output must not overlap source")
    if output.exists(): raise FileExistsError("Variant output exists")
    before=snapshot(original)
    removed=sorted(p for p in before if ucrt_candidate(p))
    if not removed or "_internal/ucrtbase.dll" not in removed:
        raise ValueError("Expected app-local UCRT payload missing")
    if len(removed)<10:
        raise ValueError("Unexpectedly small API-set/UCRT list")
    if not any(p.lower().endswith("/vcruntime140.dll") for p in before):
        raise ValueError("Original VC runtime DLL not found; inspect baseline")
    shutil.copytree(original,output)
    for rel in removed:
        (output/rel).unlink()
    after=snapshot(output)
    if set(before)-set(after)!=set(removed) or set(after)-set(before):
        raise AssertionError("Unexpected variant file set change")
    changed=[p for p in after if after[p]!=before[p]]
    if changed: raise AssertionError("Non-UCRT payload modified: "+repr(changed))
    if any(ucrt_candidate(p) for p in after):
        raise AssertionError("App-local UCRT still present")
    evidence={
        "schema":"localquote-win10-system-ucrt-experiment-v1",
        "target_os":"Windows 10/11 x64 only",
        "original":str(original),"variant":str(output),
        "baseline_file_count":len(before),"variant_file_count":len(after),
        "removed_count":len(removed),
        "removed_files":[{"path":p,**before[p]} for p in removed],
        "bytes_saved":sum(before[p]["bytes"] for p in removed),
        "unexpected_added_or_changed_files":changed,
        "original_exe_sha256":before["LocalQuote-Desktop.exe"]["sha256"],
        "variant_exe_sha256":after["LocalQuote-Desktop.exe"]["sha256"],
        "remaining_vcruntime_paths":[p for p in after if p.lower().endswith("/vcruntime140.dll")],
        "system_ucrt_available":True,
        "system_ucrt_source":str(system_ucrt),
        "system_ucrt_sha256":sha(system_ucrt),
        "classification":"ENGINEERING_VARIANT_NOT_RELEASE",
        "user_windows_acceptance":"NOT_PERFORMED",
        "license_redist_approval":"NOT_GRANTED",
        "release_decision":"HOLD",
        "limitations":["GitHub runner is not a clean disconnected Windows installation",
                       "API-set contracts may be resolved by OS rather than disk files",
                       "Retained Visual C++ runtime components require independent REDIST/notice review"]
    }
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:evidence[k] for k in ("baseline_file_count","variant_file_count","removed_count","bytes_saved","release_decision")}))
    return evidence

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--variant",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    make(a.original,a.variant,a.report)
