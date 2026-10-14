import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CombinedBackpackTests(unittest.TestCase):
    def test_latest_candidate_contains_functional_backpack_resources(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes*'))
        candidates = [path for path in candidates
                      if 'sophisticated_backpacks' in json.loads((path / 'FIX_REPORT.json').read_text())
                      and 'depositAll' in (path / 'BP/scripts/backpack_v2.js').read_text()]
        if not candidates:
            self.skipTest('combined backpack candidate not built yet')
        root = max(candidates, key=lambda path: json.loads((path / 'FIX_REPORT.json').read_text())['sophisticated_backpacks']['items'])
        report = json.loads((root / 'FIX_REPORT.json').read_text())['sophisticated_backpacks']
        self.assertEqual(report['items'], 3)
        self.assertEqual(report['recipes'], 3)
        self.assertTrue((root / 'BP/scripts/backpack_v2.js').is_file())
        self.assertIn('import "./backpack_v2.js";', (root / 'BP/scripts/main.js').read_text())
        runtime = (root / 'BP/scripts/backpack_v2.js').read_text()
        self.assertIn('depositAll', runtime)
        self.assertIn('configureFilter', runtime)
        self.assertIn('migrateLegacy', runtime)
        for name in ('backpack.json', 'filter_upgrade.json', 'expansion_upgrade.json'):
            self.assertTrue((root / 'BP/items' / name).is_file())
        for name in ('backpack.json', 'filter_upgrade.json', 'expansion_upgrade.json'):
            self.assertTrue((root / 'BP/recipes' / name).is_file())
        self.assertIn('installExpansion', runtime)
        self.assertIn('MAX_CAPACITY=81', runtime)
