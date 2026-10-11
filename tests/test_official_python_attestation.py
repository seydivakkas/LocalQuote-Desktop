"""Offline tests for SHA-attested official CPython ZIP checks."""
import hashlib,importlib.util,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
SCRIPT=Path(__file__).resolve().parents[1]/"packaging"/"official_python_attestation.py"
spec=importlib.util.spec_from_file_location("official_python_attestation",SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class OfficialPythonAttestationTests(unittest.TestCase):
    def test_attests_equal_bytes_and_rejects_changed_official_zip(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);package=root/"official.zip";bundle=root/"frozen";bundle.mkdir()
            (bundle/"python313.dll").write_bytes(b"same runtime")
            with ZipFile(package,"w") as z:z.writestr("python313.dll",b"same runtime")
            sha=hashlib.sha256(package.read_bytes()).hexdigest()
            result=mod.compare(package,bundle,root/"out.json",expected_sha=sha)
            self.assertEqual(result["exact_matches"],1)
            self.assertEqual(result["mismatches"],[])
            (bundle/"python313.dll").write_bytes(b"tampered runtime")
            changed=mod.compare(package,bundle,root/"changed.json",expected_sha=sha)
            self.assertEqual(changed["exact_matches"],0)
            self.assertEqual(changed["mismatches"],["python313.dll"])
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
                mod.compare(package,bundle,root/"bad.json",expected_sha="f"*64)

if __name__=="__main__":
    unittest.main()
