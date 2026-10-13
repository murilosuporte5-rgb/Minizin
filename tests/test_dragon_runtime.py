import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DragonRuntime(unittest.TestCase):
    def test_current_ice_and_fire_ids_have_mountable_dragon_and_egg_entities(self):
        pack = ROOT / 'build/creature_world_v3/iceandfire'
        self.assertTrue(pack.is_dir())
        behavior = pack / 'BP/entities'
        for name in ('firedragon', 'icedragon', 'lightningdragon'):
            doc = json.loads((behavior / f'{name}.json').read_text(encoding='utf-8'))['minecraft:entity']
            self.assertIn('minecraft:rideable', doc['components'])
            self.assertTrue(doc['description']['identifier'].startswith('minizin_iceandfire:'))
        eggs = list(behavior.glob('*_dragon_egg.json'))
        self.assertEqual(len(eggs), 3)
        for path in eggs:
            doc = json.loads(path.read_text(encoding='utf-8'))['minecraft:entity']
            self.assertEqual(doc['components']['minecraft:type_family']['family'], ['minizin_dragon_egg'])

    def test_combined_candidate_contains_current_dragon_items_and_runtime(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        self.assertTrue(candidates)
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        source = (bp / 'scripts' / 'creatures.js').read_text(encoding='utf-8')
        for value in ('minizin_iceandfire:firedragon', 'minizin_iceandfire:dragon_egg_fire',
                      'dragon_flute', 'minecraft:rideable'):
            self.assertIn(value, source)
        item_ids = {
            json.loads(path.read_text(encoding='utf-8'))['minecraft:item']['description']['identifier']
            for path in (bp / 'items').rglob('*.json')
        }
        self.assertIn('minizin_iceandfire:dragon_meal', item_ids)
        self.assertIn('minizin_iceandfire:dragon_egg_fire', item_ids)

    def test_combined_creature_runtime_has_unique_boss_adapters(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        source = (bp / 'scripts' / 'creatures.js').read_text(encoding='utf-8')
        for value in ('minizin_cataclysm:ignis', 'hellfire_burst', 'laser', 'blackhole',
                      'minizin_mowzies:bluff', 'fissure'):
            self.assertIn(value, source)


if __name__ == '__main__':
    unittest.main()
