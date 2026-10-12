import unittest
from tools.citadel_java_to_bedrock import recover_models

class CitadelModelTests(unittest.TestCase):
    def test_parent_and_child_from_separate_classes(self):
        base="""class Base {
          public Base() {
           texWidth = 256; texHeight = 128;
           root = new AdvancedModelBox(this);
           root.setRotationPoint(0F, 24F, 0F);
           chest = new AdvancedModelBox(this);
           root.addChild(chest);
           chest.setRotationPoint(0F, -3F, 1F);
           chest.setTextureOffset(10,20).addBox(-2F, -2F, -1F, 4F, 4F, 2F, 0F, false);
           this.updateDefaultPose();
          }
        }"""
        child="""class Creature extends Base {
          public Creature(){
            super();
            horn = new AdvancedModelBox(this);
            horn.setRotationPoint(1F, -4F, 2F);
            chest.addChild(horn);
            setRotateAngle(horn, 0F, 0F, 0.7854F);
            horn.setTextureOffset(40,15).addBox(0F, 0F, 0F, 1F, 4F, 1F, 0F, true);
            this.updateDefaultPose();
          }
        }"""
        geom,report=recover_models([base,child])
        bones=geom["minecraft:geometry"][0]["bones"]
        self.assertEqual(len(bones),3)
        self.assertEqual(report["box_total"],2)
        self.assertEqual(geom["minecraft:geometry"][0]["description"]["texture_width"],256)
        self.assertEqual(bones[-1]["parent"],"chest")
        self.assertEqual(bones[-1]["cubes"][0]["uv"],[40,15])
    def test_missing_texture_dimension_is_error(self):
        with self.assertRaises(ValueError):
            recover_models(["root = new AdvancedModelBox(this);"])

if __name__=="__main__":
    unittest.main()
