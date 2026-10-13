import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class DragonArmorVisuals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'build').mkdir(exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'build')
        cls.stage=Path(cls.temp.name)/'staged/iceandfire'
        subprocess.run([sys.executable,str(ROOT/'tools/build_creature_world_packs.py'),
                        '--output',str(cls.stage.parent)],cwd=ROOT,check=True,
                       stdout=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_source_layers_reach_synced_bedrock_render_controllers(self):
        stage=self.stage
        for family in ('firedragon', 'icedragon', 'lightningdragon'):
            entity = json.loads((stage/'BP/entities'/f'{family}.json').read_text())['minecraft:entity']
            client = json.loads((stage/'RP/entity'/f'{family}.entity.json').read_text())['minecraft:client_entity']['description']
            controller = json.loads((stage/'RP/render_controllers'/f'{family}.json').read_text())['render_controllers'][
                f'controller.render.iceandfire.{family}']
            self.assertEqual(client['materials']['default'], 'entity_multitexture')
            self.assertEqual(len(controller['textures']), 5)
            self.assertEqual(len([k for k in entity['events'] if k.startswith('minizin:dragon_armor_')]), 17)
            for slot in ('head', 'neck', 'body', 'tail'):
                prop=entity['description']['properties'][f'minizin:armor_{slot}']
                self.assertTrue(prop['client_sync'])
                self.assertEqual(prop['range'],[0,8])
                names=controller['arrays']['textures'][f'Array.armor_{slot}']
                self.assertEqual(len(names),9)
                for n in range(9):
                    path=stage/'RP'/f'textures/entity/{family}_armor_{slot}_{n}.png'
                    # The transparent zero slot shares one source PNG.
                    if n==0:path=stage/'RP'/f'textures/entity/{family}_armor_empty.png'
                    self.assertTrue(path.is_file(),path)
                    with Image.open(path) as image:
                        self.assertEqual(image.size,(512,256))


if __name__ == '__main__':
    unittest.main()
