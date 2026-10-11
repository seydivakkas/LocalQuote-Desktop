"""Unit tests for the opt-in System UCRT variant; synthetics only."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

P=Path(__file__).resolve().parents[1]/"packaging"/"system_ucrt_variant.py"
spec=importlib.util.spec_from_file_location("system_ucrt_variant",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SystemUcrtCandidateTests(unittest.TestCase):
    def test_strict_allowlist_only_direct_internal_ucrt(self):
        self.assertTrue(m.ucrt_candidate("_internal/api-ms-win-core-file-l1-1-0.dll"))
        self.assertTrue(m.ucrt_candidate("_internal/api-ms-win-crt-stdio-l1-1-0.dll"))
        self.assertTrue(m.ucrt_candidate("_internal/ucrtbase.dll"))
        for name in ("_internal/VCRUNTIME140.dll","_internal/VCRUNTIME140_1.dll",
                     "_internal/third-party/api-ms-win-crt-stdio-l1-1-0.dll",
                     "other/api-ms-win-core-foo.dll","_internal/kernel32.dll",
                     "_internal/reportlab/native.pyd","THIRD_PARTY_LICENSES/ucrtbase.dll"):
            self.assertFalse(m.ucrt_candidate(name),name)

    def build_fake(self,root):
        initial=root/"baseline";internal=initial/"_internal";internal.mkdir(parents=True)
        (initial/"LocalQuote-Desktop.exe").write_bytes(b"MZfake")
        (internal/"VCRUNTIME140.dll").write_bytes(b"retain")
        (internal/"sqlite3.dll").write_bytes(b"retain-sqlite")
        (internal/"ucrtbase.dll").write_bytes(b"ucrt")
        for i in range(12):
            (internal/f"api-ms-win-crt-fixture{i}.dll").write_bytes(f"api{i}".encode())
        system=root/"windows"/"System32"/"ucrtbase.dll";system.parent.mkdir(parents=True)
        system.write_bytes(b"os-runtime")
        return initial,system

    def test_opt_in_copy_retains_all_non_ucrt_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);orig,system=self.build_fake(root)
            evidence=m.make(orig,root/"candidate",root/"result.json",windows_major=10,system_ucrt=system)
            self.assertEqual(evidence["removed_count"],13)
            self.assertEqual(evidence["baseline_file_count"]-evidence["variant_file_count"],13)
            self.assertEqual(evidence["original_exe_sha256"],evidence["variant_exe_sha256"])
            self.assertTrue((orig/"_internal"/"ucrtbase.dll").exists())
            self.assertFalse((root/"candidate"/"_internal"/"ucrtbase.dll").exists())
            self.assertTrue((root/"candidate"/"_internal"/"VCRUNTIME140.dll").exists())
            self.assertEqual(evidence["release_decision"],"HOLD")
            with self.assertRaises(FileExistsError):
                m.make(orig,root/"candidate",root/"result2.json",windows_major=10,system_ucrt=system)

    def test_downlevel_windows_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);orig,system=self.build_fake(root)
            with self.assertRaisesRegex(RuntimeError,"Windows 10/11"):
                m.make(orig,root/"candidate",root/"evidence.json",windows_major=6,system_ucrt=system)
            self.assertFalse((root/"candidate").exists())

if __name__=="__main__":
    unittest.main()
