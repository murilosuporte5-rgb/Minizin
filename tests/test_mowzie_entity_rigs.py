import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MowzieEntityRigs(unittest.TestCase):
    def test_latest_combined_candidate_contains_source_backed_entity_rigs(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v90_mowzie_attacks')) or sorted(ROOT.glob('build/combined_all_*_v89_mowzie_flight')) or sorted(ROOT.glob('build/combined_all_*_v88_mowzie_entities'))
        if not candidates:
            self.skipTest('v88 candidate not built yet')
        root = candidates[-1]
        expected = {
            'foliaath': (34, 34, (128, 64)),
            'frostmaw': (85, 52, (512, 256)),
            'grottol': (44, 43, (64, 64)),
            'naga': (97, 90, (256, 256)),
            'wroughtnaut': (74, 71, (128, 128)),
        }
        for name, (bones, boxes, texture) in expected.items():
            geo = json.loads((root / 'RP/models/entity/mowzies' / f'{name}.geo.json').read_text())
            description = geo['minecraft:geometry'][0]['description']
            self.assertEqual(description['texture_width'], texture[0], name)
            self.assertEqual(description['texture_height'], texture[1], name)
            self.assertEqual(len(geo['minecraft:geometry'][0]['bones']), bones, name)
            self.assertEqual(sum(len(bone.get('cubes', [])) for bone in geo['minecraft:geometry'][0]['bones']), boxes, name)
            entity = json.loads((root / 'BP/entities/mowzies' / f'{name}.json').read_text())
            self.assertEqual(entity['minecraft:entity']['description']['identifier'], f'minizin_mowzies:{name}')
            client = json.loads((root / 'RP/entity/mowzies' / f'{name}.entity.json').read_text())
            self.assertEqual(client['minecraft:client_entity']['description']['geometry']['default'], f'geometry.minizin_mowzies.{name}')

        naga = json.loads((root / 'BP/entities/mowzies/naga.json').read_text())['minecraft:entity']['components']
        self.assertFalse(naga['minecraft:physics']['has_gravity'])
        self.assertIn('minecraft:navigation.fly', naga)
        self.assertIn('minecraft:movement.fly', naga)
        self.assertIn('minecraft:behavior.random_fly', naga)
        grottol = json.loads((root / 'BP/entities/mowzies/grottol.json').read_text())['minecraft:entity']['components']
        self.assertIn('minecraft:behavior.avoid_mob', grottol)

