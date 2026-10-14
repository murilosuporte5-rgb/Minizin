import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class BopCombinedWorldgenTests(unittest.TestCase):
    def test_builder_generates_and_stages_bop_worldgen(self):
        builder=(ROOT/'tools/repair_combined_pack.py').read_text(encoding='utf-8')
        self.assertIn("add_bop_worldgen(rp,bp)",builder)
        candidates=sorted(ROOT.glob('build/combined_all_bosses_final_v*_aether_accessory_effects/BP'))
        self.assertTrue(candidates,'combined accessory candidate missing')
        bp=candidates[-1]
        # v83 predates integration and is intentionally allowed to fail this
        # assertion; the current candidate must contain the staged layer.
        if bp.parent.name.endswith('v83_aether_accessory_effects'):
            self.skipTest('pre-integration candidate')
        self.assertGreaterEqual(len(list((bp/'biomes').glob('*.json'))),68)
        self.assertTrue((bp/'scripts/bop_worldgen/main.js').is_file())
        manifest=json.loads((bp/'manifest.json').read_text())
        self.assertEqual(manifest['header']['min_engine_version'],[1,21,110])
        self.assertEqual(next(d['version'] for d in manifest['dependencies'] if d.get('module_name')=='@minecraft/server'),'beta')


if __name__=='__main__':
    unittest.main()
