import tempfile,unittest,json
from pathlib import Path
from tools.build_next_four_pack import BASE,PASSIVES,pack
class NextFourPackTests(unittest.TestCase):
    def test_pack_manifests_and_js(self):
        rp=json.loads((BASE/"RP/manifest.json").read_text())
        bp=json.loads((BASE/"BP/manifest.json").read_text())
        self.assertEqual(bp["dependencies"][0]["uuid"],rp["header"]["uuid"])
        script=bp["modules"][1]["entry"]
        self.assertTrue((BASE/"BP"/script).is_file())
        self.assertEqual(len(PASSIVES),4)
    def test_zip_preserves_paths(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"manifest.json").write_text("{}")
            data=pack(p)
            import zipfile,io
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                self.assertEqual(z.namelist(),["manifest.json"])
if __name__=="__main__":unittest.main()
