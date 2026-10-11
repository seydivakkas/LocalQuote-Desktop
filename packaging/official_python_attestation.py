"""Compare frozen CPython DLLs with a checksum-verified official embeddable ZIP.

Trusted SHA-256 is copied from the Python.org 3.13.15 release file table.
The official ZIP is downloaded by CI (NEVER by the customer's offline app).
"""
from __future__ import annotations
import argparse,hashlib,json,tempfile,urllib.request
from pathlib import Path
from zipfile import ZipFile

URL="https://www.python.org/ftp/python/3.13.15/python-3.13.15-embed-amd64.zip"
OFFICIAL_SHA256="d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def compare(package:Path,bundle:Path,output:Path,*,expected_sha:str=OFFICIAL_SHA256)->dict:
    package_hash=sha(package.read_bytes())
    if package_hash.lower()!=expected_sha.lower():
        raise ValueError("OFFICIAL_PYTHON_ZIP_SHA_MISMATCH")
    files=[p for p in bundle.rglob("*") if p.is_file() and p.suffix.lower() in (".dll",".pyd",".exe")]
    compare_list=[]
    with ZipFile(package) as z:
        inside={}
        for entry in z.namelist():
            name=Path(entry).name.casefold()
            if name and name.endswith((".dll",".pyd",".exe")):
                inside.setdefault(name,[]).append({"member":entry,"sha256":sha(z.read(entry))})
        for binary in files:
            basename=binary.name.casefold()
            if basename not in inside: continue
            frozen_sha=sha(binary.read_bytes())
            candidates=inside[basename]
            good=[x for x in candidates if x["sha256"]==frozen_sha]
            compare_list.append({"frozen_path":binary.relative_to(bundle).as_posix(),
                                 "sha256":frozen_sha,"official_members":candidates,
                                 "byte_identical_to_official":bool(good)})
    report={"schema":"localquote-official-python-binary-attestation-v1",
            "official_release":"CPython 3.13.15 x64 embeddable",
            "official_download":URL,"release_reference":"https://www.python.org/downloads/release/python-31315/",
            "official_zip_sha256":package_hash,"compared":compare_list,
            "exact_matches":sum(x["byte_identical_to_official"] for x in compare_list),
            "mismatches":[x["frozen_path"] for x in compare_list if not x["byte_identical_to_official"]],
            "release_decision":"HOLD",
            "limits":["Hash confirms official ZIP bytes, not third-party redistribution rights",
                      "Python embeddable ZIP may omit Tcl/Tk and Windows CRT files"]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"official_sha_verified":True,"compared":len(compare_list),
                      "matches":report["exact_matches"],"mismatches":report["mismatches"]}))
    return report

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="localquote-official-cpython-") as d:
        package=Path(d)/"python-3.13.15-embed-amd64.zip"
        with urllib.request.urlopen(URL,timeout=120) as stream,package.open("wb") as output:
            import shutil
            shutil.copyfileobj(stream,output)
        report=compare(package,args.bundle,args.output)
    if not report["compared"]:
        raise SystemExit("No CPython binary was compared")
if __name__=="__main__":
    main()
