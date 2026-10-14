import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AlexEntityRigs(unittest.TestCase):
    def test_candidate_contains_source_backed_alex_rigs_and_textures(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes*'))
        if not candidates:
            self.skipTest('v93 candidate not built yet')
        root = max(candidates, key=lambda path: len(json.loads((path / 'FIX_REPORT.json').read_text()).get('alex_entities', [])))
        entries = json.loads((root / 'FIX_REPORT.json').read_text())['alex_entities']
        self.assertEqual(len(entries), 9)
        for entry in entries:
            name = entry['id'].split(':', 1)[1]
            self.assertTrue((root / 'BP/entities/alexscaves' / f'{name}.json').is_file())
            self.assertTrue((root / 'RP/entity/alexscaves' / f'{name}.entity.json').is_file())
            self.assertTrue((root / 'RP/models/entity/alexscaves' / f'{name}.geo.json').is_file())
            self.assertGreater(entry['bones'], 0)
            self.assertGreater(entry['boxes'], 0)
        catalog = (root / 'BP/scripts/creature_catalog.js').read_text()
        for name in ('beholder', 'candicorn', 'corrodent', 'grottoceratops', 'vallumraptor'):
            self.assertIn(f'minizin_alexscaves:{name}', catalog)

    def test_candidate_exposes_original_alex_inventory_icons(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes*'))
        if not candidates:
            self.skipTest('v94 candidate not built yet')
        root = max(candidates, key=lambda path: len(json.loads((path / 'FIX_REPORT.json').read_text()).get('alex_items', [])))
        report = json.loads((root / 'FIX_REPORT.json').read_text())
        self.assertEqual(len(report['alex_items']), 205)
        atlas = json.loads((root / 'RP/textures/item_texture.json').read_text())['texture_data']
        for name in ('acid_bucket', 'alex_meal', 'desolate_dagger', 'serene_salad'):
            paths = list(root.glob(f'BP/items/**/*{name}*.json'))
            if not paths:
                paths = [path for path in root.glob('BP/items/**/*.json')
                         if json.loads(path.read_text())['minecraft:item']['description']['identifier'].endswith(':' + name)]
            path = paths[0]
            doc = json.loads(path.read_text())
            icon = doc['minecraft:item']['components']['minecraft:icon']['textures']['default']
            self.assertIn(icon, atlas)
            self.assertTrue((root / 'RP/textures/items/alexscaves' / f'{name}.png').is_file())

    def test_candidate_exposes_source_backed_alex_cube_blocks(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes'))
        if not candidates:
            self.skipTest('v96 candidate not built yet')
        root = max(candidates, key=lambda path: json.loads((path / 'FIX_REPORT.json').read_text()).get('alex_blocks', {}).get('count', 0))
        report = json.loads((root / 'FIX_REPORT.json').read_text())
        self.assertEqual(report['alex_blocks']['count'], 77)
        self.assertEqual(report['alex_blocks']['loot_added'], 64)
        for name in ('limestone', 'pewen_log', 'guanostone_tiles'):
            block = json.loads((root / 'BP/blocks/alexscaves' / f'{name}.json').read_text())
            ident = block['minecraft:block']['description']['identifier']
            self.assertEqual(ident, f'minizin_alexscaves:{name}')
            self.assertIn('minecraft:geometry.full_block', block['minecraft:block']['components']['minecraft:geometry'])
            self.assertTrue((root / 'BP/items/alexscaves_blocks' / f'{name}.json').is_file())

    def test_candidate_exposes_source_backed_alex_cave_biomes_with_honest_routing_boundary(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes'))
        if not candidates:
            self.skipTest('Alex biome candidate not built yet')
        candidates = [path for path in candidates
                      if 'alex_biomes' in json.loads((path / 'FIX_REPORT.json').read_text())]
        if not candidates:
            self.skipTest('Alex biome report not built yet')
        root = max(candidates, key=lambda path: json.loads((path / 'FIX_REPORT.json').read_text())['alex_biomes']['source_count'])
        report = json.loads((root / 'FIX_REPORT.json').read_text())['alex_biomes']
        self.assertEqual(report['source_count'], 6)
        self.assertFalse(report['native_cave_routing'])
        self.assertGreaterEqual(report['configured_feature_count'], 70)
        for name in ('abyssal_chasm', 'candy_cavity', 'forlorn_hollows', 'magnetic_caves', 'primordial_caves', 'toxic_caves'):
            biome = json.loads((root / 'BP/biomes' / f'{name}.json').read_text())
            self.assertEqual(biome['minecraft:biome']['description']['identifier'], f'minizin_alexscaves:{name}')
            self.assertIn('cave', biome['minecraft:biome']['components']['minecraft:tags']['tags'])
            self.assertTrue((root / 'RP/biomes_client' / f'{name}.biome_client.json').is_file())

