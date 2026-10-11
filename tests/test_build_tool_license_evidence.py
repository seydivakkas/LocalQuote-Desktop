"""Regression for collecting build wheel notices, including nested vendor notices."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
SCRIPT=Path(__file__).resolve().parents[1]/"packaging"/"build_tool_license_evidence.py"
spec=importlib.util.spec_from_file_location("build_tool_license_evidence",SCRIPT)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class BuildWheelLicenseTests(unittest.TestCase):
    def test_embedded_vendor_notice_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);w=root/"wheels";w.mkdir()
            wheel=w/"setuptools-84.0.0-py3-none-any.whl"
            with ZipFile(wheel,"w") as z:
                z.writestr("setuptools-84.0.0.dist-info/licenses/LICENSE","main terms")
                z.writestr("setuptools/_vendor/another-1.dist-info/licenses/LICENSE","vendor terms")
            digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
            manifest=root/"manifest.json"
            manifest.write_text(json.dumps({"components":{"setuptools":{"version":"84.0.0","file":wheel.name,"sha256":digest}}}))
            report=audit.collect(w,manifest,root/"out")
            self.assertEqual(report["license_file_count"],2)
            self.assertFalse(report["errors"])
            self.assertFalse(report["legal_clearance"])
            wheel.write_bytes(b"modified")
            changed=audit.collect(w,manifest,root/"bad")
            self.assertIn("WHEEL_BYTE_MISMATCH: setuptools",changed["errors"])

if __name__=="__main__":
    unittest.main()
