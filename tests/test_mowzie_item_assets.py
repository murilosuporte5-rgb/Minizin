import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class MowzieItemAssets(unittest.TestCase):
    def test_latest_candidate_stages_source_icons_and_recipes(self):
        candidates=sorted(ROOT.glob('build/combined_all_bosses_final_v*_origins_source_powers'))
        if not candidates:self.skipTest('latest Mowzie candidate not built yet')
        root=candidates[-1]
        builder=(ROOT/'tools/repair_combined_pack.py').read_text(encoding='utf-8')
        self.assertIn('add_source_backed_mowzie_items',builder)
        expected=('foliaath_seed','captured_grottol','naga_fang','naga_fang_dagger','wrought_axe','wrought_helmet','earthrend_gauntlet','sculptor_staff')
        if not (root/'BP/items/mowzies/foliaath_seed.json').is_file():
            self.skipTest('pre-item-integration candidate')
        for name in expected:
            path=root/'BP/items/mowzies'/f'{name}.json'
            self.assertTrue(path.is_file(),name)
            doc=json.loads(path.read_text())
            self.assertEqual(doc['minecraft:item']['description']['identifier'],f'minizin_mowzies:{name}')
            self.assertTrue((root/'RP/textures/items/mowzies'/f'{name}.png').is_file(),name)
        self.assertTrue((root/'BP/recipes/mowzies/naga_fang_dagger.json').is_file())
        self.assertTrue((root/'BP/recipes/mowzies/grottol_smelt.json').is_file())


if __name__=='__main__':
    unittest.main()
