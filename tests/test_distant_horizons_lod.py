import unittest
from tools.distant_horizons_lod import pyramid
from tools.distant_horizons_source_audit import classify
class LodTests(unittest.TestCase):
    def test_weighted_odd_heightfield(self):
        p=pyramid([[0,10,20],[30,40,50],[60,70,80]])
        c=p["levels"][-1]["cells"][0][0]
        self.assertEqual(c["samples"],9)
        self.assertEqual(c["min"],0)
        self.assertEqual(c["max"],80)
        self.assertEqual(c["mean"],40)
        self.assertEqual(len(p["levels"]),3)
    def test_invalid_input(self):
        with self.assertRaises(ValueError):pyramid([[1,2],[3]])
        with self.assertRaises(ValueError):pyramid([[float("nan")]])
    def test_classify_source(self):
        d=classify(["core/render/LodRenderer.java","core/lod/FullDataSource.java",
                    "api/interfaces/IDhApiTerrainRenderer.java","core/cache/DhDatabase.java"])
        self.assertGreaterEqual(d["categories"]["rendering"]["count"],1)
        self.assertGreaterEqual(d["categories"]["lod_data"]["count"],1)
        self.assertFalse(d["is_bedrock_renderer"])
if __name__=="__main__":unittest.main()
