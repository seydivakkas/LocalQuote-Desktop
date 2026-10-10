"""Offline independent preview verifier regression."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

FILE=Path(__file__).resolve().parents[1]/"packaging"/"verify_preview.py"
spec=importlib.util.spec_from_file_location("verify_preview",FILE)
verify=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

class VerifyTests(unittest.TestCase):
    def test_accepts_correct_archive_and_rejects_modified_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); archive=root/"preview.zip"
            with ZipFile(archive,"w") as z: z.writestr("app.exe",b"MZsafe")
            manifest=root/"manifest.json"
            manifest.write_text(json.dumps({"files":[{"path":"app.exe","size":6,"sha256":hashlib.sha256(b"MZsafe").hexdigest()}]}))
            sha=root/"sha.txt"
            sha.write_text(f"{verify.hash_file(archive)}  preview.zip\n")
            self.assertEqual(verify.verify(archive,sha,manifest),1)
            with ZipFile(archive,"w") as z: z.writestr("app.exe",b"MZchanged")
            with self.assertRaisesRegex(ValueError,"Archive SHA-256"):
                verify.verify(archive,sha,manifest)

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); archive=root/"preview.zip"
            with ZipFile(archive,"w") as z: z.writestr("../outside",b"x")
            sha=root/"sha.txt"; sha.write_text(f"{verify.hash_file(archive)}  preview.zip\n")
            manifest=root/"manifest.json"
            manifest.write_text(json.dumps({"files":[{"path":"../outside","size":1,"sha256":hashlib.sha256(b"x").hexdigest()}]}))
            with self.assertRaisesRegex(ValueError,"Unsafe"):
                verify.verify(archive,sha,manifest)

if __name__=="__main__":
    unittest.main()
