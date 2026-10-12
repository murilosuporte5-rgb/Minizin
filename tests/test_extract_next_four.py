import tempfile,unittest
from pathlib import Path
from tools.extract_next_four import category,permitted,extract
class ExtractionTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(category("src/main/resources/data/origins/powers/elytra.json"),"origin_power")
        self.assertEqual(category("art/powercell.blend"),"mesh")
        self.assertEqual(category("Common/src/main/resources/data/carryon/tags/blocks/block_blacklist.json"),"tag_json")
        self.assertEqual(category("common/src/main/resources/assets/mca/skins/skin/female/1.png"),"png_texture")
    def test_paths_are_scoped(self):
        self.assertTrue(permitted("art/powercell.blend","rftools"))
        self.assertTrue(permitted("Common/src/main/resources/data/carryon/tags/blocks/block_blacklist.json","carryon"))
        self.assertFalse(permitted("src/other/unrelated.key","rftools"))
    def test_extract_hash_and_stage(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p)/"upstream"
            f=root/"src/main/resources/data/origins/powers/flight.json"
            f.parent.mkdir(parents=True);f.write_text('{"type":"origins:active_self"}')
            ttf=root/"src/main/resources/assets/origins/fonts/secret.ttf"
            ttf.parent.mkdir(parents=True);ttf.write_bytes(b"x")
            out=Path(p)/"out"
            doc=extract(root,"origins",out)
            self.assertEqual(doc["file_count"],1)
            self.assertEqual(doc["files"][0]["category"],"origin_power")
            self.assertTrue((out/doc["files"][0]["staged"]).exists())
if __name__=="__main__":unittest.main()
