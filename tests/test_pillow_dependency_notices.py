"""Ensure missing Pillow codec notices fail closed before artifact packaging."""
import importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"packaging"/"pillow_dependency_notices.py"
spec=importlib.util.spec_from_file_location("pillow_dependency_notices",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PillowNoticeTests(unittest.TestCase):
    def test_requires_every_notice_and_copies_with_source_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"upstream";bundle=root/"bundle"
            source.mkdir();bundle.mkdir()
            with self.assertRaisesRegex(ValueError,"Missing Pillow upstream notice"):
                m.stage(source,bundle,root/"a.json")
            for name in m.NAMES:(source/(name+".txt")).write_text(name+" test notice",encoding="utf-8")
            r=m.stage(source,bundle,root/"result.json")
            self.assertEqual(r["notice_count"],len(m.NAMES))
            self.assertFalse(r["codec_version_matches_verified"])
            self.assertEqual(r["release_decision"],"HOLD")
            self.assertTrue((bundle/"THIRD_PARTY_LICENSES"/"Pillow-UPSTREAM_REFERENCE_12.3.0"/"LIBAVIF.txt").is_file())
if __name__=="__main__":
    unittest.main()
