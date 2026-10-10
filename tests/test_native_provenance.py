"""Offline tests for wheel hashes and Windows native evidence."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1] / "packaging"

def load(name: str):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

native=load("native_provenance")
wheels=load("wheel_provenance")

class NativeEvidenceTests(unittest.TestCase):
    def test_classifications(self):
        self.assertEqual(native.family("_internal/sqlite3.dll"),"SQLite / CPython")
        self.assertEqual(native.family("_internal/libcrypto-3.dll"),"OpenSSL")
        self.assertEqual(native.family("_internal/tk86t.dll"),"Tcl/Tk")
        self.assertEqual(native.family("_internal/PIL/_imaging.cp313-win_amd64.pyd"),"Pillow native extensions")
        self.assertEqual(native.family("_internal/unknown-vendor.dll"),"UNCLASSIFIED")

    def test_archive_verified_and_missing_notice_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle=root/"bundle"
            home=root/"python"
            out=root/"evidence"
            (bundle/"_internal"/"_tk_data").mkdir(parents=True)
            home.mkdir()
            (home/"LICENSE.txt").write_text("Python license fixture")
            (bundle/"_internal"/"_tk_data"/"license.terms").write_text("Tk license fixture")
            (bundle/"LocalQuote-Desktop.exe").write_bytes(b"MZfake")
            report=native.collect(bundle,home,out,"deadbeef")
            self.assertEqual(report["release_decision"],"HOLD")
            self.assertTrue(report["collected_notices"]["CPython"])
            self.assertTrue(report["collected_notices"]["Tcl"])
            self.assertIn("MANUAL_PROVENANCE_REVIEW: Tcl license comes from pinned upstream source, not installed runtime", report["blocking_findings"])
            with ZipFile(out/"LocalQuote-Windows-preview-integrity.zip") as z:
                self.assertIn("THIRD_PARTY_LICENSES/CPython/LICENSE.txt",z.namelist())
                self.assertIn("LocalQuote-Desktop.exe",z.namelist())
            self.assertEqual(len((out/"archive-sha256.txt").read_text().split()[0]),64)

class NativeWheelAttributionTests(unittest.TestCase):
    def test_mypyc_requires_matching_sha_and_named_wheel(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bundle=root/"bundle"; home=root/"python"
            (bundle/"_internal"/"_tk_data").mkdir(parents=True)
            (bundle/"LocalQuote-Desktop.exe").write_bytes(b"MZsynthetic")
            (bundle/"_internal"/"_tk_data"/"license.terms").write_text("Tk terms")
            (home/"LICENSE.txt").parent.mkdir(parents=True,exist_ok=True)
            (home/"LICENSE.txt").write_text("Python terms")
            binary=b"wheel-native"
            path="_internal/123__mypyc.cp313-win_amd64.pyd"
            (bundle/path).write_bytes(binary)
            good=hashlib.sha256(binary).hexdigest()
            match=root/"match.json"
            match.write_text(json.dumps({"matched":[{"path":path,"sha256":good,"origin":[{"wheel":"charset_normalizer-3.4.7-cp313-win_amd64.whl","member":"123__mypyc.cp313-win_amd64.pyd"}]}]}))
            report=native.collect(bundle,home,root/"evidence-a","synthetic",match)
            self.assertNotIn("UNKNOWN_NATIVE: "+path,report["blocking_findings"])
            self.assertTrue(any(x["family"].startswith("charset-normalizer") for x in report["native"]))
            (bundle/path).write_bytes(b"different")
            report=native.collect(bundle,home,root/"evidence-b","synthetic",match)
            self.assertIn("UNKNOWN_NATIVE: "+path,report["blocking_findings"])


class WheelProvenanceTests(unittest.TestCase):
    def test_hash_lock_from_wheel_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); w=p/"wheels"; w.mkdir()
            with ZipFile(w/"sample-1.2.3-py3-none-any.whl","w") as z:
                z.writestr("sample-1.2.3.dist-info/METADATA","Metadata-Version: 2.1\nName: sample\nVersion: 1.2.3\n")
            (p/"in.lock").write_text("sample==1.2.3\n")
            report=wheels.generate(w,p/"in.lock",p/"hashed.txt",p/"manifest.json")
            self.assertEqual(set(report["wheels"]),{"sample"})
            self.assertIn("--hash=sha256:",(p/"hashed.txt").read_text())
            self.assertEqual(len(json.loads((p/"manifest.json").read_text())["wheels"]),1)
    def test_unexpected_wheel_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); w=p/"wheels"; w.mkdir()
            (p/"in.lock").write_text("sample==1.2.3\n")
            with self.assertRaisesRegex(ValueError,"Missing wheels"):
                wheels.generate(w,p/"in.lock",p/"hashed.txt",p/"manifest.json")

if __name__=="__main__":
    unittest.main()
