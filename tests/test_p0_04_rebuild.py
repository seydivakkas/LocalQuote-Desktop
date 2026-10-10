"""Offline evidence regressions for PR #9."""
import hashlib,importlib.util,json,tempfile,unittest,sys
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]/"packaging"
sys.path.insert(0,str(ROOT))
def load(n):
    spec=importlib.util.spec_from_file_location(n,ROOT/(n+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
native=load("wheel_native_match")
compare=load("compare_builds")

class P004Tests(unittest.TestCase):
    def test_mypyc_requires_exact_binary_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);bundle=root/"bundle";w=root/"wheelhouse"
            (bundle/"_internal").mkdir(parents=True);w.mkdir()
            name="123__mypyc.cp313-win_amd64.pyd"
            (bundle/"_internal"/name).write_bytes(b"identical")
            with ZipFile(w/"charset_normalizer-1.0-py3-none-any.whl","w") as z:z.writestr("charset_normalizer/"+name,b"identical")
            result=native.inspect(bundle,w,root/"result.json")
            self.assertFalse(result["findings"])
            self.assertEqual(len(result["matched"]),1)
            (bundle/"_internal"/name).write_bytes(b"modified")
            result=native.inspect(bundle,w,root/"result2.json")
            self.assertTrue(result["findings"])
    def test_double_build_detects_file_differences(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);a=root/"a.json";b=root/"b.json"
            a.write_text(json.dumps({"files":[{"path":"a.dll","sha256":"1"}]}))
            b.write_text(json.dumps({"files":[{"path":"a.dll","sha256":"2"}]}))
            report=compare.compare(a,b,root/"out.json")
            self.assertFalse(report["identical"])
            self.assertEqual(report["different_files"],["a.dll"])
if __name__=="__main__":unittest.main()
