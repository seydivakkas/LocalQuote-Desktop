"""Retain Pillow 12.3.0's *source build dependency* notices in preview.

The pinned official Pillow source checkout is supplied by CI. These notices
are references for potential embedded codecs, not proof that every codec
is enabled nor that its binary version matches a notice.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path

UPSTREAM_COMMIT="bb1d8e8ab8d29048624d96e3ee53cecf7c13d13d"
NAMES=("AOM","BROTLI","BZIP2","DAV1D","FREETYPE2","HARFBUZZ","LCMS2",
       "LIBAVIF","LIBJPEG","LIBLZMA","LIBPNG","LIBTIFF","LIBWEBP","LIBYUV",
       "OPENJPEG","RAQM","TCL_TK","XAU","XCB","XDMCP","ZLIB","ZSTD")

def stage(source:Path,bundle:Path,out:Path)->dict:
    if not source.is_dir() or not bundle.is_dir():
        raise ValueError("Missing Pillow source checkout or application bundle")
    notices=[]
    for name in NAMES:
        f=source/(name+".txt")
        if not f.is_file() or not f.read_bytes().strip():
            raise ValueError("Missing Pillow upstream notice: "+str(f))
        dest=bundle/"THIRD_PARTY_LICENSES"/"Pillow-UPSTREAM_REFERENCE_12.3.0"/f.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(f,dest)
        notices.append({"component":name,"package_path":dest.relative_to(bundle).as_posix(),
                        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "upstream_commit":UPSTREAM_COMMIT,
                        "verification":"UPSTREAM_SOURCE_ONLY"})
    report={"schema":"localquote-pillow-upstream-dependency-notices-v1",
            "source_commit":UPSTREAM_COMMIT,
            "source_url":"https://github.com/python-pillow/Pillow/tree/"+UPSTREAM_COMMIT+"/wheels/dependency_licenses",
            "notice_count":len(notices),"notices":notices,
            "codec_version_matches_verified":False,"release_decision":"HOLD"}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("Pillow upstream reference notices copied:",len(notices))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for field in ("source","bundle","output"):p.add_argument("--"+field,type=Path,required=True)
    a=p.parse_args()
    stage(a.source,a.bundle,a.output)
