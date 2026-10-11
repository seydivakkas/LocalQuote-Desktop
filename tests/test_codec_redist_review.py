"""Regression tests for codec notice/REDIST review matrix."""
from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path
F=Path(__file__).resolve().parents[1]/"packaging"/"codec_redist_review.py"
sp=importlib.util.spec_from_file_location("codec_redist_review",F)
module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)

class CodecRedistTests(unittest.TestCase):
    def fixtures(self,root):
        a=root/"native.json";b=root/"pillow.json";c=root/"variant.json"
        a.write_text(json.dumps({"runtime_versions":{"pillow":"12.3.0","pillow_codec_versions":{"webp":"1.6.0","avif":"1.4.2"}}}))
        b.write_text(json.dumps({"source_commit":"pin","notices":[{"component":key} for key in ("LIBWEBP","LIBAVIF","AOM","DAV1D","LIBYUV")]}))
        c.write_text(json.dumps({"remaining_vcruntime_paths":["_internal/VCRUNTIME140.dll"],"removed_count":43,"release_decision":"HOLD"}))
        return a,b,c

    def test_notice_coverage_does_not_approve_releases(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);a,b,c=self.fixtures(root)
            x=module.create(a,b,c,root/"result.json")
            self.assertEqual(x["codec_count"],2)
            self.assertEqual(x["findings"],[])
            self.assertFalse(x["legal_clearance"])
            self.assertEqual(x["release_decision"],"HOLD")

    def test_unmapped_codec_or_missing_notice_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);a,b,c=self.fixtures(root)
            info=json.loads(a.read_text());info["runtime_versions"]["pillow_codec_versions"]["unknown"]="9"
            a.write_text(json.dumps(info))
            x=module.create(a,b,c,root/"result.json")
            self.assertIn("UNMAPPED_CODEC: unknown",x["findings"])
            notices=json.loads(b.read_text())
            notices["notices"]=[x for x in notices["notices"] if x["component"]!="LIBAVIF"]
            b.write_text(json.dumps(notices))
            y=module.create(a,b,c,root/"result2.json")
            self.assertIn("MISSING_CODEC_NOTICE: avif",y["findings"])

if __name__=="__main__":
    unittest.main()
