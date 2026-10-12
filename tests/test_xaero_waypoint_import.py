import tempfile,unittest
from pathlib import Path
from tools.xaero_waypoint_import import read_waypoints,parse_dimension,convert

class XaeroTests(unittest.TestCase):
    def test_real_grammar_and_optional_fields(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"waypoints.txt"
            f.write_text(
                "sets:gui.xaero_default:Other\n"
                "#waypoint:name:initials:x:y:z:color:disabled:type:set:rotate_on_tp:tp_yaw:visibility_type:destination\n"
                "waypoint:Home§§ Base:H:12:~:-38:14:false:0:gui.xaero_default:true:90:0:false\n"
                "waypoint:gui.xaero_deathpoint:D:-1:64:99:0:false:1:gui.xaero_default\n"
                "waypoint:bad:too:few\n")
            rows,summary=read_waypoints(f)
            self.assertEqual(len(rows),2)
            self.assertEqual(summary["skipped"],1)
            self.assertEqual(rows[0]["name"],"Home: Base")
            self.assertIsNone(rows[0]["y"])
            self.assertEqual(rows[0]["x"],12)
            self.assertEqual(rows[0]["color"],"#FFFF55")
            self.assertEqual(rows[0]["yaw"],90)
            self.assertEqual(rows[1]["name"],"Latest Death")
            self.assertTrue(rows[1]["destination"])
            self.assertEqual(rows[1]["visibility_type"],1)
    def test_dimension_folder_read_only(self):
        self.assertEqual(parse_dimension("dim%-1"),"minecraft:nether")
        self.assertEqual(parse_dimension("dim%example$land%forest"),"example:land/forest")
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"xaero/minimap/My%us%World/dim%0/waypoints.txt"
            f.parent.mkdir(parents=True)
            f.write_text("waypoint:Test:T:1:2:3:15:false:0:gui.xaero_default\n")
            obj=convert(Path(d))
            self.assertEqual(obj["waypoints"][0]["dimension"],"minecraft:overworld")
            self.assertEqual(obj["waypoints"][0]["world"],"My%us%World")
            self.assertEqual(len(obj["waypoints"]),1)
if __name__=="__main__":unittest.main()
