import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CataclysmRecipeAssets(unittest.TestCase):
    def test_latest_candidate_contains_only_resolved_source_recipes(self):
        candidates = [path for path in sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes'))
                      if 'cataclysm_recipes' in json.loads((path / 'FIX_REPORT.json').read_text())]
        if not candidates:
            self.skipTest('v92 candidate not built yet')
        root = candidates[-1]
        recipes = list((root / 'BP/recipes/cataclysm').glob('*.json'))
        self.assertEqual(len(recipes), 47)
        ids = set()
        for path in (root / 'BP/items').rglob('*.json'):
            doc = json.loads(path.read_text())
            ids.add(doc['minecraft:item']['description']['identifier'])
        for path in (root / 'BP/blocks').rglob('*.json'):
            doc = json.loads(path.read_text())
            ids.add(doc['minecraft:block']['description']['identifier'])
        for path in recipes:
            doc = json.loads(path.read_text())
            recipe = next(value for key, value in doc.items() if key.startswith('minecraft:recipe_'))
            output = recipe['result']['item'] if 'result' in recipe and isinstance(recipe['result'], dict) else recipe['output']
            self.assertIn(output, ids)
            if 'key' in recipe:
                values = recipe['key'].values()
            elif 'ingredients' in recipe:
                values = recipe['ingredients']
            else:
                values = [{'item': recipe['input']}]
            for value in values:
                self.assertTrue(value['item'].startswith('minecraft:') or value['item'] in ids)

    def test_report_records_skipped_source_recipes(self):
        candidates = [path for path in sorted(ROOT.glob('build/combined_all_*_v92*cataclysm_recipes'))
                      if 'cataclysm_recipes' in json.loads((path / 'FIX_REPORT.json').read_text())]
        if not candidates:
            self.skipTest('v92 candidate not built yet')
        report = json.loads((candidates[-1] / 'FIX_REPORT.json').read_text())
        self.assertEqual(report['cataclysm_recipes']['written'], 47)
        self.assertGreater(report['cataclysm_recipes']['skipped']['missing_output'], 0)
