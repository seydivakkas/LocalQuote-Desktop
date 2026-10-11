"""Produce a source-backed, review-only license matrix for enabled Pillow codecs.

This records current runtime versions against pinned Pillow 12.3.0 upstream
notice files. A source notice is not proof that a statically linked codec's
precise binary was built from the cited source, or redistributed lawfully.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CODECS={
  "jpg": ("LIBJPEG.txt","JPEG-compatible library; exact variant may differ"),
  "libjpeg_turbo": ("LIBJPEG.txt","libjpeg-turbo; upstream reference for JPEG family"),
  "jpg_2000": ("OPENJPEG.txt","OpenJPEG"),
  "libtiff": ("LIBTIFF.txt","TIFF"),
  "freetype2": ("FREETYPE2.txt","font renderer; check embedded font rights separately"),
  "littlecms2": ("LCMS2.txt","colour profiles"),
  "webp": ("LIBWEBP.txt","WebP codec"),
  "avif": ("LIBAVIF.txt","AVIF wrapper; separate AOM/DAV1D transitive codecs possible"),
  "zlib": ("ZLIB.txt","zlib and possibly zlib-ng; exact fork version remains review"),
}
EXTRA_REQUIRED={
    "avif": ("AOM.txt","DAV1D.txt","LIBYUV.txt"),
    "jpg": (),
    "libjpeg_turbo": (),
    "webp": (),
    "freetype2": ("HARFBUZZ.txt",),
}
MICROSOFT={
    "Windows UCRT/API-set": {"distribution":"Target Windows 10/11 OS system component, not shipped in candidate",
                           "status":"SYSTEM_DEPENDENCY_CI_ONLY"},
    "VC runtime": {"distribution":"VCRUNTIME DLL retained in package",
                   "status":"REDIST_LICENSE_ENTITLEMENT_REVIEW_REQUIRED"},
}
def create(native_evidence:Path, pillow_notices:Path, variant:Path, out:Path) -> dict:
    native=json.loads(native_evidence.read_text(encoding="utf-8"))
    notices=json.loads(pillow_notices.read_text(encoding="utf-8"))
    supported={item["component"]:item for item in notices["notices"]}
    versions=native["runtime_versions"].get("pillow_codec_versions",{})
    rows=[];errors=[]
    for feature,ver in sorted(versions.items()):
        if feature not in CODECS:
            errors.append("UNMAPPED_CODEC: "+feature)
            continue
        notice,explanation=CODECS[feature]
        notice_key=notice.removesuffix(".txt")
        extras=EXTRA_REQUIRED.get(feature,())
        referenced=[notice]+list(extras)
        present=all(name.removesuffix(".txt") in supported for name in referenced)
        if not present: errors.append("MISSING_CODEC_NOTICE: "+feature)
        rows.append({"codec":feature,"runtime_reported_version":ver,
                     "reference_notices":referenced,
                     "source_commit":notices["source_commit"],
                     "notices_present":present,"explanation":explanation,
                     "rights_status":"REFERENCE_ONLY_SOURCE_AND_LICENSE_REVIEW_REQUIRED"})
    candidate=json.loads(variant.read_text(encoding="utf-8"))
    kept=[p for p in candidate["remaining_vcruntime_paths"]]
    if not kept: errors.append("VC_RUNTIME_NOT_IN_CANDIDATE")
    if candidate["release_decision"]!="HOLD": errors.append("UNEXPECTED_RELEASE_APPROVAL")
    report={"schema":"localquote-codec-and-redist-review-v1",
            "pillow_version":native["runtime_versions"].get("pillow"),
            "codec_count":len(rows),"codec_reviews":rows,
            "microsoft_groups":MICROSOFT,"retained_vcruntime_paths":kept,
            "removed_app_local_ucrt_count":candidate["removed_count"],
            "findings":errors,
            "legal_clearance":False,
            "limitations":["Enabled codec version introspection cannot prove wheel C-link provenance",
                           "AVIF may carry multiple statically linked dependencies; source notices may not match precise versions",
                           "Microsoft system UCRT does not waive separately bundled VC runtime redistribution terms",
                           "First-party customer-use contract is still a draft",
                           "A Windows runner smoke test is not real disconnected user acceptance"],
            "release_decision":"HOLD"}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"codecs":len(rows),"missing_notice_findings":errors,"release_decision":"HOLD"}))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("native","notices","variant","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    result=create(a.native,a.notices,a.variant,a.output)
    raise SystemExit(bool(result["findings"]))
