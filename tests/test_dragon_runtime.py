import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DragonRuntime(unittest.TestCase):
    def test_independent_creature_pack_localizes_item_and_spawn_egg_keys(self):
        staged = ROOT / 'build/creatures_staged_v36/Minizin_Creatures_RP'
        self.assertTrue(staged.is_dir())
        lang = (staged / 'texts' / 'pt_BR.lang').read_text(encoding='utf-8')
        for key in (
            'item.minizin_creatures:dragon_meal.name=Comida de Dragão',
            'item.minizin_creatures:creative_dragon_meal.name=Super Comida de Dragão',
            'item.spawn_egg.entity.minizin_creatures:atlatitan.name=Atlatitan',
        ):
            self.assertIn(key, lang)
        item = json.loads((ROOT / 'build/creatures_staged_v36/Minizin_Creatures_BP/items/dragon_meal.json').read_text(encoding='utf-8'))
        self.assertEqual(item['minecraft:item']['components']['minecraft:display_name']['value'],
                         'item.minizin_creatures:dragon_meal.name')

    def test_combined_candidate_preserves_java_dragon_armor_slots_and_materials(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        self.assertTrue(candidates)
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        items = {json.loads(path.read_text(encoding='utf-8'))['minecraft:item']['description']['identifier']
                 for path in (bp / 'items').rglob('*.json')}
        materials = ('iron','gold','diamond','silver','copper',
                     'dragonsteel_fire','dragonsteel_ice','dragonsteel_lightning')
        slots = ('head','neck','body','tail')
        expected = {f'minizin_iceandfire:dragonarmor_{material}_{slot}'
                    for material in materials for slot in slots}
        self.assertTrue(expected.issubset(items))
        for ident in expected:
            doc_path = bp / 'items' / 'creatures' / (ident.replace(':','_') + '.json')
            doc = json.loads(doc_path.read_text(encoding='utf-8'))['minecraft:item']
            self.assertEqual(doc['components']['minecraft:max_stack_size'], 1)
            display_key='item.'+ident+'.name'
            self.assertEqual(doc['components']['minecraft:display_name']['value'], display_key)
            material=ident.split('dragonarmor_',1)[1].rsplit('_',1)[0]
            expected_title={
                'iron':'Armadura de Ferro para Dragão', 'gold':'Armadura de Ouro para Dragão',
                'diamond':'Armadura de Diamante para Dragão', 'silver':'Armadura de Prata para Dragão',
                'copper':'Armadura de Cobre para Dragão',
                'dragonsteel_fire':'Armadura de Aço Dracônico de Fogo',
                'dragonsteel_ice':'Armadura de Aço Dracônico de Gelo',
                'dragonsteel_lightning':'Armadura de Aço Dracônico Elétrico'
            }[material]
            lang=(bp.parent / 'RP' / 'texts' / 'pt_BR.lang').read_text(encoding='utf-8')
            self.assertIn(display_key+'='+expected_title, lang)

        runtime = (bp / 'scripts' / 'creatures.js').read_text(encoding='utf-8')
        for token in ('dragon_armor_'+ 'iron', 'armor_'+ "'+armor.slot",
                      "['head','neck','body','tail']", 'dragonsteel_lightning'):
            self.assertIn(token, runtime)

    def test_current_ice_and_fire_ids_have_mountable_dragon_and_egg_entities(self):
        pack = ROOT / 'build/creature_world_v3/iceandfire'
        self.assertTrue(pack.is_dir())
        behavior = pack / 'BP/entities'
        for name in ('firedragon', 'icedragon', 'lightningdragon'):
            doc = json.loads((behavior / f'{name}.json').read_text(encoding='utf-8'))['minecraft:entity']
            self.assertIn('minecraft:rideable', doc['components'])
            self.assertTrue(doc['description']['identifier'].startswith('minizin_iceandfire:'))
        eggs = list(behavior.glob('*_dragon_egg.json'))
        self.assertEqual(len(eggs), 3)
        for path in eggs:
            doc = json.loads(path.read_text(encoding='utf-8'))['minecraft:entity']
            self.assertEqual(doc['components']['minecraft:type_family']['family'], ['minizin_dragon_egg'])

    def test_combined_candidate_contains_current_dragon_items_and_runtime(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        self.assertTrue(candidates)
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        source = (bp / 'scripts' / 'creatures.js').read_text(encoding='utf-8')
        for value in ('minizin_iceandfire:firedragon', 'minizin_iceandfire:dragon_egg_fire',
                      'dragon_flute', 'minecraft:rideable'):
            self.assertIn(value, source)
        item_ids = {
            json.loads(path.read_text(encoding='utf-8'))['minecraft:item']['description']['identifier']
            for path in (bp / 'items').rglob('*.json')
        }
        self.assertIn('minizin_iceandfire:dragon_meal', item_ids)
        self.assertIn('minizin_iceandfire:dragon_egg_fire', item_ids)

    def test_combined_candidate_renders_source_dragon_armor_layers(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/RP'))
        self.assertTrue(candidates)
        rp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        for dragon in ('firedragon', 'icedragon', 'lightningdragon'):
            client = json.loads((rp / 'entity' / 'iceandfire' / f'{dragon}.entity.json').read_text(encoding='utf-8'))
            controllers = client['minecraft:client_entity']['description']['render_controllers']
            for slot in ('head', 'neck', 'body', 'tail'):
                self.assertIn(f'controller.render.iceandfire.{dragon}.armor_{slot}', controllers)
                source = rp / 'textures' / 'iceandfire' / 'dragon_armor' / dragon
                self.assertTrue((source / f'{slot}_8.png').is_file())
            controller = json.loads((rp / 'render_controllers' / 'iceandfire' / f'{dragon}.json').read_text(encoding='utf-8'))
            for slot in ('head', 'neck', 'body', 'tail'):
                entry = controller['render_controllers'][f'controller.render.iceandfire.{dragon}.armor_{slot}']
                self.assertEqual(len(entry['arrays']['textures'][f'Array.armor_{slot}']), 9)

        bp = rp.parent / 'BP'
        for dragon in ('firedragon', 'icedragon', 'lightningdragon'):
            props = json.loads((bp / 'entities' / 'iceandfire' / f'{dragon}.json').read_text(encoding='utf-8'))['minecraft:entity']['description']['properties']
            for slot in ('head', 'neck', 'body', 'tail'):
                self.assertEqual(props[f'minizin:armor_{slot}']['range'], [0, 8])

    def test_independent_ice_and_fire_pack_keeps_the_same_armor_layers(self):
        root = ROOT / 'build/creature_world_v6/iceandfire'
        self.assertTrue(root.is_dir())
        for dragon in ('firedragon', 'icedragon', 'lightningdragon'):
            client = json.loads((root / 'RP/entity' / f'{dragon}.entity.json').read_text(encoding='utf-8'))
            controllers = client['minecraft:client_entity']['description']['render_controllers']
            self.assertEqual(sum(any(x.endswith(f'.armor_{slot}') for x in controllers)
                                 for slot in ('head','neck','body','tail')), 4)
            for slot in ('head','neck','body','tail'):
                self.assertTrue((root / 'RP/textures/iceandfire/dragon_armor' / dragon / f'{slot}_8.png').is_file())

    def test_combined_creature_runtime_has_unique_boss_adapters(self):
        candidates = sorted((ROOT / 'build').glob('combined_all_*_final_v*/BP'))
        bp = max(candidates, key=lambda path: int(re.search(r'_v(\d+)', path.parent.name).group(1)))
        source = (bp / 'scripts' / 'creatures.js').read_text(encoding='utf-8')
        for value in ('minizin_cataclysm:ignis', 'hellfire_burst', 'laser', 'blackhole',
                      'minizin_mowzies:bluff', 'fissure'):
            self.assertIn(value, source)

    def test_latest_candidate_replaces_dragon_armor_without_item_loss(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v106*'))
        if not candidates:
            self.skipTest('v106 candidate not built yet')
        root = max(candidates, key=lambda path: (path / 'FIX_REPORT.json').stat().st_mtime)
        runtime = (root / 'BP/scripts/creatures.js').read_text(encoding='utf-8')
        self.assertIn('const old=String(dragonKey(entity', runtime)
        self.assertIn('new ItemStack(old,1)', runtime)
        self.assertIn('selected.amount!==1', runtime)


if __name__ == '__main__':
    unittest.main()
