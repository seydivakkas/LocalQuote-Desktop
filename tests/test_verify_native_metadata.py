"""Independent evidence-integrity checks using synthetic native records."""
import importlib.util,json,tempfile,unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"packaging"/"verify_native_metadata.py"
spec=importlib.util.spec_from_file_location("lq_verify_native_metadata",P)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class EvidenceConsistencyTests(unittest.TestCase):
    def test_equal_hashes_pass_and_tampered_version_fails(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            source=root/"source.json";pe=root/"pe.json";manifest=root/"manifest.json"
            source.write_text(json.dumps({"native_files":[{"path":"a.dll","sha256":"a"*64}]}))
            pe.write_text(json.dumps({"files":[{"path":"a.dll","sha256":"a"*64,"file_version":"1.0","authenticode_status":"Valid"}]}))
            manifest.write_text(json.dumps({"files":[{"path":"a.dll","sha256":"a"*64},{"path":"notice.txt","sha256":"b"*64}]}))
            report=mod.validate(source,pe,manifest,root/"result.json")
            self.assertEqual(report["evidence_errors"],[])
            pe.write_text(json.dumps({"files":[{"path":"a.dll","sha256":"c"*64,"file_version":"","authenticode_status":"NotSigned"}]}))
            changed=mod.validate(source,pe,manifest,root/"changed.json")
            self.assertIn("INCONSISTENT_pe_INVENTORY",changed["evidence_errors"])
            self.assertEqual(changed["missing_version_resource_count"],1)
            self.assertEqual(changed["release_decision"],"HOLD")

if __name__=="__main__":
    unittest.main()
