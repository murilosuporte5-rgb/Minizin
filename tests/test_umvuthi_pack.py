"""Assert the Umvuthi attack animations, reward, and wearer model are wired."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class UmvuthiPack(unittest.TestCase):
    def test_source_rig_attacks_and_reward(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            subprocess.run([sys.executable,str(ROOT/'tools/build_creature_world_packs.py'),
                            '--output',str(Path(tmp)/'staged')],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
            stage=Path(tmp)/'staged/mowzies'
            read=lambda path:json.loads((stage/path).read_text())
            client=read('RP/entity/umvuthi.entity.json')['minecraft:client_entity']['description']
            mob=read('BP/entities/umvuthi.json')['minecraft:entity']
            self.assertEqual(mob['components']['minecraft:health']['value'],150)
            self.assertNotIn('minecraft:behavior.melee_attack',mob['components'])
            self.assertEqual(mob['description']['properties']['minizin:attack_mode']['range'],[0,4])
            bones={bone['name'] for bone in read('RP/models/entity/umvuthi.geo.json')
                   ['minecraft:geometry'][0]['bones']}
            for mode in ('mask_twitch','sun_strike','flare','solar_beam','supernova'):
                animation=next(iter(read(f'RP/animations/umvuthi_{mode}.animation.json')['animations'].values()))
                self.assertFalse(set(animation.get('bones',{}))-bones)
                self.assertIn(mode,client['animations'])
            with Image.open(stage/'RP/textures/entity/umvuthi.png') as image:
                self.assertGreater(image.width,64)
            item=read('BP/items/sol_visage.json')['minecraft:item']
            self.assertEqual(item['components']['minecraft:wearable']['slot'],'slot.armor.head')
            attachable=read('RP/attachables/sol_visage.json')['minecraft:attachable']['description']
            self.assertEqual(attachable['identifier'],item['description']['identifier'])
            self.assertEqual(attachable['geometry']['default'],
                read('RP/models/entity/sol_visage.geo.json')['minecraft:geometry'][0]['description']['identifier'])
            self.assertEqual(read('RP/models/entity/sol_visage.geo.json')['minecraft:geometry'][0]
                             ['bones'][0]['binding'],'head')
            loot=read('BP/loot_tables/entities/umvuthi.json')['pools'][0]
            self.assertEqual(loot['conditions'][0]['condition'],'killed_by_player')
            self.assertEqual(loot['entries'][0]['name'],item['description']['identifier'])
            self.assertEqual(mob['components']['minecraft:loot']['table'],'loot_tables/entities/umvuthi.json')


if __name__=='__main__':
    unittest.main()
