import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AlexEntityRigs(unittest.TestCase):
    def test_candidate_contains_source_backed_alex_rigs_and_textures(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes'))
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

