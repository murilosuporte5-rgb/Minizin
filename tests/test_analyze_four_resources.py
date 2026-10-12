import json,tempfile,unittest
from pathlib import Path
from tools.analyze_four_resources import parse_obj,origins_analysis,carryon_analysis
class FourModsAuditTests(unittest.TestCase):
    def test_obj_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"powercell.obj"
            path.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nusemtl basic\nf 1/1 2/1 3/1\n")
            stats=parse_obj(path)
            self.assertEqual(stats["vertices"],3)
            self.assertEqual(stats["faces"],1)
            self.assertEqual(stats["bounds"]["max"],[1.0,1.0,0.0])
    def test_origins_power_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rel="src/main/resources/data/origins/"
            files=[]
            for sub,name,obj in [("powers","flight",{"type":"origins:active_self"}),
                                  ("origins","flyer",{"powers":["origins:flight"],"icon":{"item":"minecraft:elytra"}})]:
                path=root/"original"/rel/sub/(name+".json")
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(obj))
                files.append({"source":rel+sub+"/"+name+".json","category":"json_data"})
            report=origins_analysis(root,files)
            self.assertEqual(len(report["origins"]),1)
            self.assertEqual(len(report["powers"]),1)
            self.assertEqual(report["missing_local_power_json"],[])
    def test_empty_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rel="Common/src/main/resources/data/carryon/tags/blocks/block_blacklist.json"
            file=root/"original"/rel;file.parent.mkdir(parents=True)
            file.write_text('{"replace":false,"values":[]}')
            report=carryon_analysis(root,[{"source":rel,"category":"tag_json"}])
            self.assertEqual(report["tags"][0]["entries"],0)
if __name__=="__main__":unittest.main()
