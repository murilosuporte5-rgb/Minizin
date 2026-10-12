import sys,unittest,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from combine_gameplay_packs import combine
from validate_gameplay_packs import check


class CombinedLoaderPaths(unittest.TestCase):
    def test_original_geometry_loader_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'iceandfire'
            for role,kind in [('RP','resources'),('BP','data')]:
                p=source/role;p.mkdir(parents=True)
                (p/'manifest.json').write_text(json.dumps({'format_version':2,'header':{'uuid':'dcd7a421-7ec3-4c78-aee2-b24703137ac2','version':[0,1,0]},'modules':[]}))
            path=source/'RP/models/entity/test.geo.json';path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'format_version':'1.12.0','minecraft:geometry':[{
                'description':{'identifier':'geometry.test'},'bones':[]}]}))
            output=root/'output';combine([source],output)
            self.assertTrue((output/'RP/models/entity/iceandfire/test.geo.json').is_file())
            self.assertFalse((output/'RP/models/iceandfire/entity/test.geo.json').exists())
            good=output/'RP/models/entity/iceandfire/test.geo.json'
            bad=output/'RP/models/iceandfire/entity/test.geo.json';bad.parent.mkdir(parents=True);good.rename(bad)
            with self.assertRaisesRegex(ValueError,'loader directory'):check([output])

if __name__=='__main__':unittest.main()
