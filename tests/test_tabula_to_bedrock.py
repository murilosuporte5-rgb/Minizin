import json
import unittest
from tools.tabula_to_bedrock import export_tabula

class ConverterTests(unittest.TestCase):
    def test_cuboids_and_hierarchy(self):
        raw={"modelName":"X","textureWidth":256,"textureHeight":128,
             "cubes":[{"name":"BodyUpper","dimensions":[6,7,7],
                       "position":[0,11.6,-10],"offset":[-3,-1.8,0],
                       "rotation":[5.22,0,0],"txOffset":[67,47],
                       "children":[{"name":"head","dimensions":[2,2,2],
                                    "position":[0,-1,4],"offset":[-1,-1,-1],
                                    "rotation":[0,10,0],"txOffset":[0,0]}]}]}
        obj,report=export_tabula(raw,"geometry.minizin.dragon")
        bones=obj["minecraft:geometry"][0]["bones"]
        self.assertEqual(report["bones"],2)
        self.assertEqual(report["model_boxes"],2)
        self.assertEqual(bones[1]["parent"],"BodyUpper")
        self.assertEqual(bones[0]["cubes"][0]["size"],[6,7,7])
        self.assertEqual(bones[0]["cubes"][0]["uv"],[67,47])
        self.assertEqual(obj["minecraft:geometry"][0]["description"]["texture_width"],256)
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            export_tabula({"textureWidth":128,"textureHeight":128,"cubes":[]})

if __name__=="__main__":unittest.main()
