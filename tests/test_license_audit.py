"""Regression for deterministic license evidence and bundled artifact inventory."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "packaging" / "license_audit.py"
spec = importlib.util.spec_from_file_location("localquote_license_audit", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LicenseAuditTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(audit.normalized("charset_normalizer"), "charset-normalizer")
        self.assertEqual(audit.normalized("Pillow"), "pillow")

    def test_inventory_and_font_risk_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.exe").write_bytes(b"MZtest")
            (root / "font.ttf").write_bytes(b"not a licensed font")
            report = audit.inspect_bundle(root)
            self.assertEqual(report["status"], "FONT_REVIEW_REQUIRED")
            self.assertEqual(len(report["files"]), 2)
            self.assertEqual(report["fonts"][0]["path"], "font.ttf")
            self.assertEqual(len(report["files"][0]["sha256"]), 64)

    def test_empty_bundle_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "empty"):
                audit.inspect_bundle(Path(tmp))

    def test_runtime_notices_and_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = audit.audit(Path(tmp), strict=False)
            self.assertEqual(evidence["errors"], [])
            self.assertEqual(evidence["release_decision"], "HOLD")
            self.assertEqual(len(evidence["components"]), 3)
            for comp in evidence["components"]:
                self.assertTrue(comp["license_texts"])
            self.assertTrue((Path(tmp) / "license-audit.json").is_file())


if __name__ == "__main__":
    unittest.main()
