import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CataclysmItemAssets(unittest.TestCase):
    def test_latest_candidate_exposes_original_cataclysm_icons(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v91_cataclysm_items'))
        if not candidates:
            self.skipTest('v91 candidate not built yet')
        root = candidates[-1]
        items = list((root / 'BP/items/cataclysm').glob('*.json'))
        self.assertGreaterEqual(len(items), 100)
        atlas = json.loads((root / 'RP/textures/item_texture.json').read_text())['texture_data']
        for name in ('ancient_spear', 'astrape', 'ignitium_ingot', 'the_annihilator', 'void_core'):
            doc = json.loads((root / 'BP/items/cataclysm' / f'{name}.json').read_text())
            ident = f'minizin_cataclysm:{name}'
            self.assertEqual(doc['minecraft:item']['description']['identifier'], ident)
            icon = doc['minecraft:item']['components']['minecraft:icon']['textures']['default']
            self.assertIn(icon, atlas)
            self.assertTrue((root / 'RP/textures/items/cataclysm' / f'{name}.png').is_file())

