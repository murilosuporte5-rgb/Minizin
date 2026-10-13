import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AetherCombinedRuntime(unittest.TestCase):
    def test_world_builder_preserves_functional_aether_scope(self):
        pack = ROOT / 'build/worlds_v3/aether'
        self.assertTrue(pack.is_dir(), 'run the Aether world builder before this test')
        blocks = list((pack / 'BP/blocks').glob('*.json'))
        entities = list((pack / 'BP/entities').glob('*.json'))
        structures = list((pack / 'BP/structures/minizin_aether').rglob('*.mcstructure'))
        loot = list((pack / 'BP/loot_tables/minizin_aether').rglob('*.json'))
        models = list((pack / 'RP/models/entity').glob('*.geo.json'))
        self.assertEqual(len(blocks), 46)
        self.assertEqual(len(entities), 21)
        self.assertEqual(len(structures), 21)
        self.assertEqual(len(loot), 40)
        self.assertEqual(len(models), 16)
        self.assertTrue((pack / 'BP/scripts/main.js').is_file())
        self.assertTrue((pack / 'BP/scripts/bosses.js').is_file())
        self.assertTrue((pack / 'BP/scripts/wildlife.js').is_file())
        self.assertTrue((pack / 'BP/scripts/whirlwinds.js').is_file())

    def test_combined_candidate_contains_aether_runtime_and_beta_api(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        self.assertTrue(candidates, 'build the corrected combined Aether candidate before this test')
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        root = bp.parent
        scripts = next(path.parent for path in (bp / 'scripts').glob('*/main.js'))
        for name in ('main.js', 'biome_profiles.js', 'dungeon_loot.js', 'bosses.js', 'wildlife.js'):
            self.assertTrue((scripts / name).is_file(), name)
        manifest = json.loads((bp / 'manifest.json').read_text(encoding='utf-8'))
        server = next(x for x in manifest['dependencies'] if x.get('module_name') == '@minecraft/server')
        self.assertEqual(server['version'], 'beta')
        aether_ids = {
            json.loads(path.read_text(encoding='utf-8'))['minecraft:entity']['description']['identifier']
            for path in (bp / 'entities').rglob('*.json')
            if 'minizin_aether:' in path.read_text(encoding='utf-8')
        }
        self.assertEqual(len([x for x in aether_ids if x.startswith('minizin_aether:')]), 21)
        pack_namespace = scripts.name
        self.assertEqual(len(list((bp / 'structures' / pack_namespace / 'minizin_aether').rglob('*.mcstructure'))), 21)
        self.assertEqual(len(list((bp / 'loot_tables' / pack_namespace / 'minizin_aether').rglob('*.json'))), 40)
        self.assertTrue((root / 'RP/models/entity' / pack_namespace).is_dir())
        aether_main = (scripts / 'main.js').read_text(encoding='utf-8')
        self.assertIn('system.beforeEvents?.startup', aether_main)
        self.assertIn('startup dimension registry is unavailable', aether_main)


if __name__ == '__main__':
    unittest.main()
