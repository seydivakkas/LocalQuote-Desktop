"""Regression tests for native-source identity; never claim license clearance."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"packaging"/"native_source_evidence.py"
spec=importlib.util.spec_from_file_location("native_source_evidence",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceEvidenceTests(unittest.TestCase):
    def test_exact_installation_byte_identity_and_changed_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bundle=root/"bundle"; home=root/"python"
            (bundle/"_internal").mkdir(parents=True);(home/"DLLs").mkdir(parents=True)
            (bundle/"_internal"/"sqlite3.dll").write_bytes(b"same DLL")
            (home/"DLLs"/"sqlite3.dll").write_bytes(b"same DLL")
            origin=root/"match.json"
            origin.write_text('{"matched":[]}',encoding="utf-8")
            first=module.collect(bundle,home,root/"first.json",wheel_match=origin)
            self.assertEqual(first["source_match_counts"],{"INSTALLED_COPY_EXACT":1})
            self.assertEqual(first["native_files"][0]["family"],"SQLite / CPython")
            self.assertEqual(first["release_decision"],"HOLD")
            (bundle/"_internal"/"sqlite3.dll").write_bytes(b"altered DLL")
            second=module.collect(bundle,home,root/"second.json",wheel_match=origin)
            self.assertEqual(second["source_match_counts"],{"NOT_PROVEN":1})
            self.assertEqual(second["unresolved_origin_paths"],["_internal/sqlite3.dll"])
    def test_wheel_origin_requires_both_matching_path_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bundle=root/"bundle"; home=root/"python"
            bundle.mkdir();home.mkdir()
            path="vendor.pyd";(bundle/path).write_bytes(b"frozen")
            hash=module.file_hash(bundle/path)
            wheel=root/"wheel.json"
            wheel.write_text(json.dumps({"matched":[{"path":path,"sha256":hash,"origin":[{"wheel":"example-1.whl","member":"vendor.pyd"}]}]}),encoding="utf-8")
            r=module.collect(bundle,home,root/"result.json",wheel_match=wheel)
            self.assertEqual(r["native_files"][0]["source_match"],"WHEEL_EXACT")
            self.assertFalse(r["notices_verified"])

if __name__=="__main__":
    unittest.main()
