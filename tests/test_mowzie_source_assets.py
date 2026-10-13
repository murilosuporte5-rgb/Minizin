import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MowzieSourceAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = list((ROOT / 'build').glob('combined_all_*_v79_mowzie_sun_adapted/RP'))
        if not candidates:
            raise AssertionError('v79 combined build is missing')
        cls.rp = sorted(candidates, key=lambda path: path.parent.name)[-1]
        cls.bp = cls.rp.parent / 'BP'

    def test_umvuthi_and_umvuthana_use_canonical_ids_and_source_dimensions(self):
        source = ROOT / 'mods/44-mowzies-mobs/upstream/src/main/resources/assets/mowziesmobs'
        for name, dimensions in {'umvuthi': (256, 128), 'umvuthana': (64, 64)}.items():
            entity = json.loads((self.bp / f'entities/mowzies/{name}.json').read_text())
            self.assertEqual(entity['minecraft:entity']['description']['identifier'], f'minizin_mowzies:{name}')
            self.assertTrue((self.rp / f'models/entity/mowzies/{name}.geo.json').is_file())
            self.assertTrue((self.rp / f'textures/mowzies/entity/{name}.png').is_file())
            from PIL import Image
            with Image.open(self.rp / f'textures/mowzies/entity/{name}.png') as image:
                self.assertEqual((image.width, image.height), dimensions)
            for relative in [f'geo/{name}.geo.json', f'textures/entity/{name}.png']:
                original = source / relative
                generated = self.rp / ('models/entity/mowzies/' + name + '.geo.json' if relative.startswith('geo/') else 'textures/mowzies/entity/' + name + '.png')
                if relative.startswith('geo/'):
                    source_doc = json.loads(original.read_text())
                    generated_doc = json.loads(generated.read_text())
                    source_doc['minecraft:geometry'][0]['description']['identifier'] = generated_doc['minecraft:geometry'][0]['description']['identifier']
                    self.assertEqual(source_doc, generated_doc)
                else:
                    self.assertEqual(hashlib.sha256(original.read_bytes()).digest(), hashlib.sha256(generated.read_bytes()).digest())

    def test_source_animation_channels_are_bedrock_arrays_and_runtime_is_wired(self):
        for name in ('umvuthi', 'umvuthana'):
            animation = json.loads((self.rp / f'animations/mowzies/{name}.animation.json').read_text())
            raw = json.dumps(animation)
            self.assertNotIn('"vector"', raw)
            self.assertNotIn('"easing"', raw)
        runtime = (self.bp / 'scripts/mowzie_sun_bosses.js').read_text()
        main = (self.bp / 'scripts/main.js').read_text()
        self.assertIn('minizin_mowzies:umvuthi', runtime)
        self.assertIn('minizin_mowzies:umvuthana', runtime)
        self.assertIn('installMowzieSunBosses', main)


if __name__ == '__main__':
    unittest.main()
