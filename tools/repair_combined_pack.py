#!/usr/bin/env python3
"""Build a fresh Android retest candidate using original textures and rigs."""
import argparse,json,re,shutil,zipfile,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image
from build_bedrock_packs import zipped
from validate_gameplay_packs import check

ROOT=Path(__file__).resolve().parents[1]

def add_dragon_armor_layers(rp,bp):
    """Render Ice and Fire's original four dragon-armor overlay layers.

    Java's LayerDragonArmor renders the dragon model again with four slot
    textures selected by the armor ordinal. Bedrock has no equivalent native
    equipment layer, so expose the same ordinal as client-synced entity
    properties and use conditional render controllers. The PNGs are copied
    from the pinned Java source; no replacement texture is generated.
    """
    source=ROOT/'mods/16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/models'
    for dragon in ['firedragon','icedragon','lightningdragon']:
        entity_path=bp/f'entities/iceandfire/{dragon}.json'
        client_path=rp/f'entity/iceandfire/{dragon}.entity.json'
        controller_path=rp/f'render_controllers/iceandfire/{dragon}.json'
        if not entity_path.exists() or not client_path.exists() or not controller_path.exists():
            continue
        entity_doc=json.loads(entity_path.read_text(encoding='utf-8'))
        desc=entity_doc['minecraft:entity']['description']
        props=desc.setdefault('properties',{})
        for slot in ['head','neck','body','tail']:
            props.setdefault('minizin:armor_'+slot,{
                'type':'int','range':[0,8],'default':0,'client_sync':True})
        write(entity_path,entity_doc)
        client_doc=json.loads(client_path.read_text(encoding='utf-8'))
        cdesc=client_doc['minecraft:client_entity']['description']
        textures=cdesc.setdefault('textures',{})
        controllers=cdesc.setdefault('render_controllers',[])
        base='textures/iceandfire/dragon_armor/'+dragon
        empty_src=source/'firedragon'/'empty.png'
        empty_rel=base+'/empty'
        empty_target=rp/(empty_rel+'.png');empty_target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(empty_src,empty_target)
        textures['armor_empty']=empty_rel
        for slot in ['head','neck','body','tail']:
            for ordinal in range(1,9):
                src=source/dragon/f'armor_{slot}_{ordinal}.png'
                if not src.exists():
                    raise FileNotFoundError(src)
                rel=base+'/'+slot+'_'+str(ordinal)
                target=rp/(rel+'.png');target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,target)
                textures[f'armor_{slot}_{ordinal}']=rel
            controller='controller.render.iceandfire.'+dragon+'.armor_'+slot
            if controller not in controllers:controllers.append(controller)
        write(client_path,client_doc)
        original=json.loads(controller_path.read_text(encoding='utf-8'))
        rendered=original.setdefault('render_controllers',{})
        geometry=next(iter(rendered.values())).get('geometry','Geometry.default')
        for slot in ['head','neck','body','tail']:
            controller='controller.render.iceandfire.'+dragon+'.armor_'+slot
            rendered[controller]={
                'geometry':geometry,
                'materials':[{'*':'Material.default'}],
                'textures':['Array.armor_'+slot],
                'arrays':{'textures':{'Array.armor_'+slot:[
                    'Texture.armor_empty',
                    *['Texture.armor_'+slot+'_'+str(i) for i in range(1,9)]
                ]}},
            }
        write(controller_path,original)


def add_aether_accessories(rp,bp):
    """Add the original Aether ring/tool icons and the non-offhand accessory UI."""
    base=ROOT/'mods/41-the-aether/upstream'
    assets=base/'src/main/resources/assets/aether'
    registry_path=rp/'textures/item_texture.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    names=[tier+'_'+kind for tier in ['skyroot','holystone','zanite','gravitite','valkyrie']
      for kind in ['pickaxe','axe','shovel','hoe']]
    names += [tier+'_sword' for tier in ['skyroot','holystone','zanite','gravitite','flaming']]
    names += [
      'vampire_blade','iron_ring','golden_ring','ice_ring','zanite_ring',
      'iron_pendant','golden_pendant','ice_pendant','zanite_pendant',
      'leather_gloves','chainmail_gloves','iron_gloves','golden_gloves',
      'diamond_gloves','netherite_gloves','zanite_gloves','gravitite_gloves',
      'valkyrie_gloves','neptune_gloves','phoenix_gloves','obsidian_gloves',
      'red_cape','blue_cape','yellow_cape','white_cape','agility_cape',
      'swet_cape','invisibility_cloak','valkyrie_cape','golden_feather',
      'regeneration_stone','iron_bubble','shield_of_repulsion'
    ]
    accessory_slots={
      **{name:'ring' for name in ['iron_ring','golden_ring','ice_ring','zanite_ring']},
      **{name:'pendant' for name in ['iron_pendant','golden_pendant','ice_pendant','zanite_pendant']},
      **{name:'gloves' for name in ['leather_gloves','chainmail_gloves','iron_gloves','golden_gloves','diamond_gloves','netherite_gloves','zanite_gloves','gravitite_gloves','valkyrie_gloves','neptune_gloves','phoenix_gloves','obsidian_gloves']},
      **{name:'cape' for name in ['red_cape','blue_cape','yellow_cape','white_cape','agility_cape','swet_cape','invisibility_cloak','valkyrie_cape']},
      **{name:'accessory' for name in ['golden_feather','regeneration_stone','iron_bubble']},
      'shield_of_repulsion':'shield'
    }
    durability={
      'zanite_ring':49,'ice_ring':125,'zanite_pendant':98,'ice_pendant':250,
      'leather_gloves':59,'chainmail_gloves':131,'iron_gloves':250,'golden_gloves':32,
      'diamond_gloves':1561,'netherite_gloves':2031,'zanite_gloves':250,
      'gravitite_gloves':1561,'valkyrie_gloves':1561,'neptune_gloves':250,
      'phoenix_gloves':1561,'obsidian_gloves':2031,'shield_of_repulsion':512
    }
    tool_tiers={
      'skyroot':{'durability':59,'speed':2.0,'bonus':0.0,'enchantability':15},
      'holystone':{'durability':131,'speed':4.0,'bonus':1.0,'enchantability':5},
      'zanite':{'durability':250,'speed':6.0,'bonus':2.0,'enchantability':14},
      'gravitite':{'durability':1561,'speed':8.0,'bonus':3.0,'enchantability':10},
      'valkyrie':{'durability':1561,'speed':8.0,'bonus':3.0,'enchantability':10},
      'flaming':{'durability':502,'speed':8.0,'bonus':3.0,'enchantability':10},
      'vampire':{'durability':2031,'speed':8.0,'bonus':3.0,'enchantability':10},
    }
    catalog={}
    for name in names:
        found=list((assets/'textures/item').rglob(name+'.png'))
        if not found:
            continue
        key='minizin_aether_equipment_'+name
        rel='textures/items/aether_equipment/'+name
        target=rp/(rel+'.png');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(found[0],target)
        registry.setdefault('texture_data',{})[key]={'textures':rel}
        ident='minizin_aether:'+name
        is_accessory=name in accessory_slots
        components={'minecraft:icon':{'textures':{'default':key}},
                    'minecraft:max_stack_size':1,
                    'minecraft:display_name':{'value':'item.'+ident+'.name'}}
        if not is_accessory:
            components['minecraft:hand_equipped']=True
            tier='vampire' if name=='vampire_blade' else name.split('_')[0]
            kind='sword' if name=='vampire_blade' else name.split('_')[-1]
            spec=tool_tiers.get(tier)
            if spec and kind in {'sword','axe','pickaxe','shovel','hoe'}:
                components['minecraft:durability']={'max_durability':spec['durability']}
                components['minecraft:damage']=int(spec['bonus']+{'sword':3,'axe':5,'pickaxe':1,'shovel':1,'hoe':1}[kind])
                components['minecraft:enchantable']={'slot':kind,'value':spec['enchantability']}
                if kind in {'pickaxe','axe','shovel'}:
                    tags={'pickaxe':'stone','axe':'wood','shovel':'dirt'}
                    components['minecraft:digger']={'use_efficiency':True,'destroy_speeds':[{'block':{'tags':"q.any_tag('"+tags[kind]+"')"},'speed':spec['speed']}]}
        if name in durability:components['minecraft:durability']={'max_durability':durability[name]}
        catalog[ident]={'accessory':is_accessory}
        if is_accessory:catalog[ident]['slot']=accessory_slots[name]
        if name=='ice_ring' or name=='ice_pendant':catalog[ident]['freezing']=True
        write(bp/'items/aether_equipment'/f'{name}.json',{
          'format_version':'1.21.90','minecraft:item':{
            'description':{'identifier':ident,'menu_category':{'category':'equipment'}},
            'components':components}})
    write(registry_path,registry)
    shutil.copy2(ROOT/'bedrock/runtime/aether_equipment_v2.js',bp/'scripts/aether_equipment.js')
    (bp/'scripts/aether_equipment_catalog.js').write_text(
        'export const EQUIPMENT = '+json.dumps(catalog,ensure_ascii=False)+';\n',encoding='utf-8')
    main=bp/'scripts/main.js';raw=main.read_text(encoding='utf-8') if main.exists() else ''
    if 'import "./aether_equipment.js";' not in raw:
        main.write_text(raw.rstrip()+'\nimport "./aether_equipment.js";\n',encoding='utf-8')
    return len(catalog)


def add_creature_items(rp,bp):
    """Stage the original Ice and Fire/Alex's Caves item icons used by the mobs."""
    root=ROOT/'mods'
    sources={
      'minizin_iceandfire:dragon_meal':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/dragon_meal.png',
      'minizin_iceandfire:creative_dragon_meal':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/creative_dragon_meal.png',
      'minizin_iceandfire:dragon_flute':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/dragon_flute.png',
      'minizin_iceandfire:dragon_armor_iron':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/dragonarmor_iron_head.png',
      'minizin_iceandfire:dragon_scale_fire':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/scales_red.png',
      'minizin_iceandfire:dragon_scale_ice':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/scales_blue.png',
      'minizin_iceandfire:dragon_scale_lightning':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item/scales_black.png',
      'minizin_iceandfire:dragon_egg_fire':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/models/firedragon/egg_red.png',
      'minizin_iceandfire:dragon_egg_ice':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/models/icedragon/egg_blue.png',
      'minizin_iceandfire:dragon_egg_lightning':root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/models/lightningdragon/egg_black.png',
      'minizin_alexscaves:serene_salad':root/'42-alexs-caves/upstream/src/main/resources/assets/alexscaves/textures/item/serene_salad.png',
    }
    # ItemDragonArmor.java registers one non-stackable item per material and
    # dragon slot. Keep those registry IDs and original pixels instead of
    # collapsing the Java inventory into one generic Bedrock item.
    armor_materials=('iron','gold','diamond','silver','copper',
                     'dragonsteel_fire','dragonsteel_ice','dragonsteel_lightning')
    armor_slots=('head','neck','body','tail')
    armor_sources={}
    for material in armor_materials:
        for slot in armor_slots:
            ident='minizin_iceandfire:dragonarmor_'+material+'_'+slot
            armor_sources[ident]=root/'16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/item'/('dragonarmor_'+material+'_'+slot+'.png')
    registry_path=rp/'textures/item_texture.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    for ident,source in {**sources,**armor_sources}.items():
        if not source.is_file():
            continue
        name=ident.replace(':','_')
        rel='textures/items/creatures/'+name
        target=rp/(rel+'.png');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[name]={'textures':rel}
        components={'minecraft:icon':{'textures':{'default':name}},
              'minecraft:display_name':{'value':'item.'+ident+'.name'},
              'minecraft:max_stack_size':1 if ident in armor_sources else 64}
        write(bp/'items/creatures'/f'{name}.json',{
          'format_version':'1.21.90','minecraft:item':{
            'description':{'identifier':ident,'menu_category':{'category':'items'}},
            'components':components}})
    write(registry_path,registry)
    return len([x for x in {**sources,**armor_sources}.values() if x.is_file()])


def add_source_backed_mowzie_sun_bosses(rp,bp):
    """Integrate Umvuthi/Umvuthana with the original Mowzie assets.

    The combined pack previously shipped only Bluff even though the pinned
    Java source includes these two entities, their Bedrock-compatible geometry,
    textures and animation timelines.  Keep the source meshes and animation
    keys intact; only the identifier namespace and the runtime property name
    are adapted for the combined pack.
    """
    source_root=ROOT/'mods/44-mowzies-mobs/upstream/src/main/resources/assets/mowziesmobs'
    legacy_root=ROOT/'bedrock/packs/creatures'
    specs={
      'umvuthi': {'health':150,'width':2.7,'height':3.8,'boss':True},
      'umvuthana': {'health':30,'width':0.75,'height':1.65,'boss':False},
    }
    added=[]
    for name,spec in specs.items():
        source_bp=legacy_root/'BP/entities'/f'{name}.json'
        if not source_bp.is_file():
            raise FileNotFoundError(source_bp)
        entity=json.loads(source_bp.read_text(encoding='utf-8'))
        entity_text=json.dumps(entity).replace('minizin_creatures:', 'minizin_mowzies:')
        entity=json.loads(entity_text)
        desc=entity['minecraft:entity']['description']
        ident=f'minizin_mowzies:{name}'
        desc['identifier']=ident
        # The Java animation controller uses this enum as its authoritative
        # attack state; the legacy standalone JSON already preserves its full
        # attack vocabulary and collision/AI values.
        prop=desc.setdefault('properties',{}).get('minizin_mowzies:attack')
        if not prop:
            raise ValueError(f'Missing attack property in source-backed {name}')
        write(bp/'entities/mowzies'/f'{name}.json',entity)

        geo=json.loads((source_root/'geo'/f'{name}.geo.json').read_text(encoding='utf-8'))
        geometry=geo['minecraft:geometry'][0]
        geometry['description']['identifier']=f'geometry.minizin_mowzies.{name}'
        write(rp/'models/entity/mowzies'/f'{name}.geo.json',{
          'format_version':'1.12.0','minecraft:geometry':[geometry]})
        texture_rel=f'textures/mowzies/entity/{name}'
        target=rp/(texture_rel+'.png');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source_root/'textures/entity'/f'{name}.png',target)

        original=json.loads((source_root/'animations'/f'{name}.animation.json').read_text(encoding='utf-8'))
        animation_map={}
        animations={}
        for animation_name,animation in original.get('animations',{}).items():
            key=f'animation.minizin.mowzies.{name}.{animation_name}'
            animations[key]=adapt_source_animation(animation)
            animation_map[animation_name]=key
        write(rp/'animations/mowzies'/f'{name}.animation.json',{
          'format_version':'1.8.0','animations':animations})
        idle='idle' if name=='umvuthi' else 'idle_neutral'
        client={
          'format_version':'1.10.0',
          'minecraft:client_entity':{'description':{
            'identifier':ident,
            'materials':{'default':'entity_alphatest'},
            'textures':{'default':texture_rel},
            'geometry':{'default':f'geometry.minizin_mowzies.{name}'},
            'render_controllers':[f'controller.render.mowzies.{name}'],
            'animations':animation_map,
            'scripts':{'animate':[
              {idle:"query.property('minizin_mowzies:attack') == 'idle'"}
            ]}
          }}
        }
        # Keep every Java animation addressable from the client entity. The
        # action property selects attack timelines without replacing geometry.
        client['minecraft:client_entity']['description']['scripts']['animate'] += [
          {animation_name:f"query.property('minizin_mowzies:attack') == '{animation_name}'"}
          for animation_name in animation_map if animation_name not in {'idle','idle_neutral'}
        ]
        image=Image.open(target).convert('RGBA')
        palette=image.getcolors(image.width*image.height) or []
        opaque=[color for _,color in sorted(palette,reverse=True) if color[3]>128]
        base='#%02x%02x%02x'%opaque[0][:3] if opaque else '#8c5a32'
        overlay='#%02x%02x%02x'%opaque[min(3,len(opaque)-1)][:3] if opaque else '#f0c15a'
        client['minecraft:client_entity']['description']['spawn_egg']={'base_color':base,'overlay_color':overlay}
        write(rp/'entity/mowzies'/f'{name}.entity.json',client)
        write(rp/'render_controllers/mowzies'/f'{name}.json',{
          'format_version':'1.8.0','render_controllers':{
            f'controller.render.mowzies.{name}':{
              'geometry':'Geometry.default','materials':[{'*':'Material.default'}],
              'textures':['Texture.default']}}})
        added.append(ident)

    # Reuse the audited standalone attack implementation, but isolate its
    # dynamic-property and entity IDs from the old legacy namespace.
    runtime=legacy_root/'BP/scripts/umvuthi.js'
    text=runtime.read_text(encoding='utf-8')
    text=text.replace('minizin_creatures:umvuthi','minizin_mowzies:umvuthi')
    text=text.replace('minizin_creatures:umvuthana','minizin_mowzies:umvuthana')
    text=text.replace('state(e,"attack",name)', 'setAttack(e,name)')
    text=text.replace('state(e,"attack","idle")', 'setAttack(e,"idle")')
    text=text.replace('const BOSS=', 'function setAttack(e,name){try{e.setProperty("minizin_mowzies:attack",name);}catch{}}\nconst BOSS=')
    text += '''\nexport function installMowzieSunBosses(){\n  system.runInterval(()=>{\n    for(const dimensionName of ["overworld","nether","the_end"]){\n      let dimension; try{dimension=world.getDimension(dimensionName);}catch{continue;}\n      for(const entity of dimension.getEntities({families:["minizin_mowzies"]})){\n        try{tickUmvuthi(entity,system.currentTick);}catch(error){\n          if(system.currentTick%600===0) console.warn("[Minizin Mowzie sun bosses] "+error);\n        }\n      }\n    }\n  },10);\n}\n'''
    # The copied module uses the same audited helper contract as the source
    # standalone implementation; place its dependency beside it.
    core=(legacy_root/'BP/scripts/core.js').read_text(encoding='utf-8')
    write(bp/'scripts/mowzie_sun_core.js',{})
    (bp/'scripts/mowzie_sun_core.js').write_text(core,encoding='utf-8')
    (bp/'scripts/mowzie_sun_math.js').write_text(
        (legacy_root/'BP/scripts/math.js').read_text(encoding='utf-8'),encoding='utf-8')
    core_path=bp/'scripts/mowzie_sun_core.js'
    core_path.write_text(core_path.read_text(encoding='utf-8').replace('from "./math.js"','from "./mowzie_sun_math.js"'),encoding='utf-8')
    text=text.replace('from "./core.js"','from "./mowzie_sun_core.js"')
    (bp/'scripts/mowzie_sun_bosses.js').write_text(text,encoding='utf-8')
    main=bp/'scripts/main.js'
    main_text=main.read_text(encoding='utf-8') if main.is_file() else ''
    import_line='import {installMowzieSunBosses} from "./mowzie_sun_bosses.js";'
    if import_line not in main_text:
        main_text=main_text.rstrip()+'\n'+import_line+'\ninstallMowzieSunBosses();\n'
    main.write_text(main_text,encoding='utf-8')
    return added


def add_source_backed_mowzie_items(rp,bp,registry):
    """Stage the Java Mowzie item catalog whose original PNGs are available.

    This deliberately does not create entity meshes for Frostmaw/Wroughtnaut
    and friends: their pinned source exposes Java model classes but no
    redistributable Bedrock geometry in this checkout.
    """
    root=ROOT/'mods/44-mowzies-mobs/upstream/src/main/resources/assets/mowziesmobs'
    specs={
      'foliaath_seed':'foliaath_seed.png','captured_grottol':'captured_grottol.png',
      'frostmaw_plushie':'frostmaw_plushie.png','glowing_jelly':'glowing_jelly.png',
      'naga_fang':'naga_fang.png','naga_fang_dagger':'naga_fang_dagger.png',
      'wrought_axe':'wrought_axe_icon.png','wrought_helmet':'wrought_helmet_icon.png',
      'earthrend_gauntlet':'earthrend_gauntlet_icon.png','sculptor_staff':'sculptor_staff_icon.png',
      'sol_visage':'sol_visage.png','spear':'spear_icon.png','blowgun':'blowgun.png',
      'dart':'dart.png','ice_crystal':'icecrystal.png','mob_remover':'mob_remover.png',
      'bluff_rod':'bluff_rod.png','grant_suns_blessing':'grant_suns_blessing.png',
      'geomancer_beads':'geomancer_beads.png','geomancer_robe':'geomancer_robe.png',
      'geomancer_belt':'geomancer_belt.png','geomancer_sandals':'geomancer_sandals.png',
    }
    item_dir=bp/'items/mowzies';texture_dir=rp/'textures/items/mowzies'
    item_dir.mkdir(parents=True,exist_ok=True);texture_dir.mkdir(parents=True,exist_ok=True)
    added=0
    for name,filename in specs.items():
        source=root/'textures/item'/filename
        if not source.is_file():continue
        ident='minizin_mowzies:'+name;icon='minizin_mowzies_'+name;rel='textures/items/mowzies/'+name
        shutil.copy2(source,rp/(rel+'.png'));registry.setdefault('texture_data',{})[icon]={'textures':rel}
        components={'minecraft:icon':{'textures':{'default':icon}},
                    'minecraft:display_name':{'value':'item.'+ident+'.name'},
                    'minecraft:max_stack_size':1 if name in {'wrought_axe','wrought_helmet','earthrend_gauntlet','sculptor_staff','sol_visage','spear','blowgun','naga_fang_dagger'} else 64}
        if name in {'wrought_axe','naga_fang_dagger','earthrend_gauntlet','sculptor_staff','blowgun'}:
            components['minecraft:hand_equipped']=True
            components['minecraft:damage']={'wrought_axe':9,'naga_fang_dagger':5,'earthrend_gauntlet':7,'sculptor_staff':5,'blowgun':1}[name]
            components['minecraft:durability']={'wrought_axe':500,'naga_fang_dagger':250,'earthrend_gauntlet':512,'sculptor_staff':200,'blowgun':300}[name]
        write(item_dir/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':components}})
        added+=1
    recipes=bp/'recipes/mowzies';recipes.mkdir(parents=True,exist_ok=True)
    write(recipes/'naga_fang_dagger.json',{'format_version':'1.20.10','minecraft:recipe_shaped':{'description':{'identifier':'minizin_mowzies:naga_fang_dagger'},'tags':['crafting_table'],'pattern':['F','I','S'],'key':{'F':{'item':'minizin_mowzies:naga_fang'},'I':{'item':'minecraft:iron_ingot'},'S':{'item':'minecraft:stick'}},'result':{'item':'minizin_mowzies:naga_fang_dagger','count':1}}})
    for kind in ('smelting','blasting'):
        write(recipes/f'grottol_{kind}.json',{'format_version':'1.20.10','minecraft:recipe_'+kind:{'description':{'identifier':'minizin_mowzies:grottol_'+kind},'tags':['furnace' if kind=='smelting' else 'blast_furnace'],'input':'minizin_mowzies:captured_grottol','output':'minecraft:diamond'}})
    return added


def add_aether_material_items(rp,bp):
    """Stage small source-backed materials required by Aether recipes."""
    assets=ROOT/'mods/41-the-aether/upstream/src/main/resources/assets/aether'
    names={'skyroot_stick':'item/materials/skyroot_stick.png'}
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    added=0
    for name,relative in names.items():
        source=assets/'textures'/relative
        if not source.is_file():continue
        ident='minizin_aether:'+name;icon='minizin_aether_'+name;texture='textures/items/aether_materials/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[icon]={'textures':texture}
        write(bp/'items/aether_materials'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},
          'components':{'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':64,
            'minecraft:display_name':{'value':'item.'+ident+'.name'}}}})
        added+=1
    write(registry_path,registry);return added


def add_aether_freezer_items(rp,bp):
    """Stage every non-vanilla item referenced by the nine Java Freezer recipes.

    The recipe runtime must never point at an item ID that the pack does not
    register: ItemStack construction would otherwise fail when a recipe
    completes. Icons are copied from the Aether source, not recreated.
    """
    assets=ROOT/'mods/41-the-aether/upstream/src/main/resources/assets/aether'
    entries={
      'skyroot_bucket':('item/miscellaneous/skyroot_bucket.png','Skyroot Bucket','Bucket used by the Aether Freezer.'),
      'skyroot_water_bucket':('item/miscellaneous/skyroot_water_bucket.png','Skyroot Water Bucket','A Skyroot Bucket filled with water.'),
      'music_disc_chinchilla':('item/miscellaneous/music_disc_chinchilla.png','Sepia Music Disc','Plays "chinchilla" by RENREN.'),
      'music_disc_high':('item/miscellaneous/music_disc_high.png','Super Music Disc','Plays "high" by RENREN.'),
    }
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    added=0
    for name,(relative,title,lore) in entries.items():
        source=assets/'textures'/relative
        if not source.is_file():
            raise FileNotFoundError(f'Missing source-backed Aether Freezer item icon: {source}')
        ident='minizin_aether:'+name;icon='minizin_aether_freezer_'+name;texture='textures/items/aether_freezer/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[icon]={'textures':texture}
        components={'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':1,
          'minecraft:display_name':{'value':'item.'+ident+'.name'},'minecraft:lore':{'value':[lore]}}
        write(bp/'items/aether_freezer'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':components}})
        for language in ('en_US','pt_BR'):
            title_pt={'skyroot_bucket':'Balde de Skyroot','skyroot_water_bucket':'Balde de Skyroot com Água',
                      'music_disc_chinchilla':'Disco de Música Sépia','music_disc_high':'Super Disco de Música'}[name]
            value=title if language=='en_US' else title_pt
            lang=rp/'texts'/f'{language}.lang';lang.parent.mkdir(parents=True,exist_ok=True)
            with lang.open('a',encoding='utf-8') as file:file.write(f'item.{ident}.name={value}\n')
        added+=1
    write(registry_path,registry);return added


def add_aether_incubator_items(rp,bp):
    """Register the exact source items consumed by IncubationRecipe."""
    assets=ROOT/'mods/41-the-aether/upstream/src/main/resources/assets/aether'
    entries={
      'black_moa_egg':('item/miscellaneous/moa_egg.png','Black Moa Egg','Ovo de Moa preto do Aether.'),
      'blue_moa_egg':('item/miscellaneous/moa_egg.png','Blue Moa Egg','Ovo de Moa azul do Aether.'),
      'white_moa_egg':('item/miscellaneous/moa_egg.png','White Moa Egg','Ovo de Moa branco do Aether.'),
      'ambrosium_torch':('block/utility/ambrosium_torch.png','Ambrosium Torch','Combustível Java do Incubator.')
    }
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));added=0
    for name,(relative,title,lore) in entries.items():
        source=assets/'textures'/relative
        if not source.is_file():raise FileNotFoundError(f'Missing source-backed Aether Incubator item icon: {source}')
        ident='minizin_aether:'+name;icon='minizin_aether_incubator_'+name;texture='textures/items/aether_incubator/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[icon]={'textures':texture}
        write(bp/'items/aether_incubator'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':{
            'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':1,
            'minecraft:display_name':{'value':'item.'+ident+'.name'},'minecraft:lore':{'value':[lore]}}}})
        titles={'black_moa_egg':('Black Moa Egg','Ovo de Moa Preto'),'blue_moa_egg':('Blue Moa Egg','Ovo de Moa Azul'),'white_moa_egg':('White Moa Egg','Ovo de Moa Branco'),'ambrosium_torch':('Ambrosium Torch','Tocha de Ambrosium')}[name]
        for language in ('en_US','pt_BR'):
            lang=rp/'texts'/f'{language}.lang';lang.parent.mkdir(parents=True,exist_ok=True)
            with lang.open('a',encoding='utf-8') as file:file.write(f'item.{ident}.name={titles[0 if language=="en_US" else 1]}\n')
        added+=1
    write(registry_path,registry);return added


def add_aether_enchanting_items(rp,bp):
    """Register every non-block item used by the ten Java altar enchanting recipes."""
    assets=ROOT/'mods/41-the-aether/upstream/src/main/resources/assets/aether'
    entries={
      'blue_berry':('item/food/blue_berry.png','Blue Berry','Blue Berry do Aether.'),
      'enchanted_berry':('item/food/enchanted_berry.png','Enchanted Berry','Enchanted Berry do Aether.'),
      'golden_dart':('item/weapons/golden_dart.png','Golden Dart','Munição do Golden Dart Shooter.'),
      'enchanted_dart':('item/weapons/enchanted_dart.png','Enchanted Dart','Munição encantada do Aether.'),
      'golden_dart_shooter':('item/weapons/golden_dart_shooter.png','Golden Dart Shooter','Dispara Golden Darts.'),
      'enchanted_dart_shooter':('item/weapons/enchanted_dart_shooter.png','Enchanted Dart Shooter','Dispara Enchanted Darts.'),
      'healing_stone':('item/food/healing_stone.png','Healing Stone','Pedra de cura do Aether.'),
      'music_disc_aether_tune':('item/miscellaneous/music_disc_aether_tune.png','Blue Music Disc','Aether Tune de Noisestorm.'),
      'skyroot_poison_bucket':('item/miscellaneous/skyroot_poison_bucket.png','Skyroot Poison Bucket','Balde Skyroot com veneno.'),
      'skyroot_remedy_bucket':('item/miscellaneous/skyroot_remedy_bucket.png','Skyroot Remedy Bucket','Balde Skyroot com remédio.')}
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));added=0
    for name,(relative,title,lore) in entries.items():
        source=assets/'textures'/relative
        if not source.is_file():raise FileNotFoundError(f'Missing source-backed Aether Enchanting item icon: {source}')
        ident='minizin_aether:'+name;icon='minizin_aether_enchanting_'+name;texture='textures/items/aether_enchanting/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[icon]={'textures':texture}
        max_stack=1 if ('shooter' in name or 'bucket' in name or 'music_disc' in name or name=='healing_stone') else 64
        write(bp/'items/aether_enchanting'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':{
            'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':max_stack,
            'minecraft:display_name':{'value':'item.'+ident+'.name'},'minecraft:lore':{'value':[lore]}}}})
        pt={'blue_berry':'Blue Berry','enchanted_berry':'Fruta Encantada','golden_dart':'Dardo Dourado','enchanted_dart':'Dardo Encantado','golden_dart_shooter':'Atirador de Dardos Dourados','enchanted_dart_shooter':'Atirador de Dardos Encantados','healing_stone':'Pedra de Cura','music_disc_aether_tune':'Disco Azul','skyroot_poison_bucket':'Balde Skyroot com Veneno','skyroot_remedy_bucket':'Balde Skyroot de Remédio'}[name]
        for language in ('en_US','pt_BR'):
            lang=rp/'texts'/f'{language}.lang';lang.parent.mkdir(parents=True,exist_ok=True)
            with lang.open('a',encoding='utf-8') as file:file.write(f'item.{ident}.name={title if language=="en_US" else pt}\n')
        added+=1
    write(registry_path,registry);return added


def add_aether_recipes(bp):
    """Convert source Aether vanilla recipes whose IDs exist in this BP.

    The Java pack also defines altar/freezing/incubation/enchanting recipes.
    Those custom serializers are intentionally skipped here; emitting them as
    crafting recipes would be a false equivalence and can make Bedrock reject
    the whole behavior pack.
    """
    source_root=ROOT/'mods/41-the-aether/upstream/src/generated/resources'
    recipe_root=source_root/'data/aether/recipe'
    tag_root=source_root/'data/aether/tags/item'
    common_tag_root=source_root/'data/c/tags/item'
    out=bp/'recipes/aether';out.mkdir(parents=True,exist_ok=True)
    registered=set()
    for path in list((bp/'items').rglob('*.json'))+list((bp/'blocks').rglob('*.json')):
        try:
            doc=json.loads(path.read_text(encoding='utf-8'))
            registered.add(doc.get('minecraft:item',{}).get('description',{}).get('identifier'))
            registered.add(doc.get('minecraft:block',{}).get('description',{}).get('identifier'))
        except (OSError,ValueError):
            continue
    registered.discard(None)
    common={
      'c:strings':['minecraft:string'],
      'c:gems/diamond':['minecraft:diamond'],
      'c:ingots/iron':['minecraft:iron_ingot'],
      'c:ingots/gold':['minecraft:gold_ingot'],
      'c:rods/wooden':['minecraft:stick','minizin_aether:skyroot_stick'],
    }
    tag_cache={}
    def ident(value):
        if not isinstance(value,str):return None
        if value.startswith('aether:'):value='minizin_aether:'+value.split(':',1)[1]
        if value.startswith('minecraft:') or value in registered:return value
        return value if value in registered else None
    def tag_values(tag,seen=()):
        if tag in common:return common[tag]
        if tag in seen:return []
        if tag in tag_cache:return tag_cache[tag]
        if not tag.startswith('aether:'):return []
        rel=tag.split(':',1)[1]+'.json';path=tag_root/rel
        if not path.is_file():return []
        try:values=json.loads(path.read_text(encoding='utf-8')).get('values',[])
        except (OSError,ValueError):return []
        result=[]
        for value in values:
            if isinstance(value,str) and value.startswith('#'):result.extend(tag_values(value[1:],seen+(tag,)))
            else:
                resolved=ident(value)
                if resolved:result.append(resolved)
        tag_cache[tag]=list(dict.fromkeys(result));return tag_cache[tag]
    def ingredient_options(entry):
        if not isinstance(entry,dict):return []
        if 'item' in entry:
            value=ident(entry['item']);return [{'item':value}] if value else []
        if 'tag' in entry:
            tag=entry['tag']
            if isinstance(tag,str) and tag.startswith('minecraft:'):
                return [{'tag':tag}]
            return [{'item':value} for value in tag_values(tag)]
        return []
    def variants(entries,limit=64):
        rows=[{}]
        for name,options in entries:
            if not options:return []
            next_rows=[]
            for row in rows:
                for option in options:
                    copy=dict(row);copy[name]=option;next_rows.append(copy)
                    if len(next_rows)>=limit:break
                if len(next_rows)>=limit:break
            rows=next_rows
        return rows
    def result_id(recipe):
        result=recipe.get('result',{})
        return ident(result.get('id') or result.get('item') or result.get('block'))
    written=[];written_by_type={};skipped={}
    def record(target,recipe_type):
        written.append(target);written_by_type[recipe_type]=written_by_type.get(recipe_type,0)+1
    for path in sorted(recipe_root.glob('*.json')):
        try:recipe=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):skipped['invalid_json']=skipped.get('invalid_json',0)+1;continue
        recipe_type=recipe.get('type','')
        output=result_id(recipe)
        if recipe_type=='minecraft:stonecutting':
            options=ingredient_options(recipe.get('ingredient'))
            count=recipe.get('result',{}).get('count',1)
            if not output or not options or count < 1:
                skipped['unresolved_ingredient']=skipped.get('unresolved_ingredient',0)+1;continue
            for ordinal,option in enumerate(options,1):
                suffix=f'_v{ordinal}' if len(options)>1 else ''
                ident_name='minizin_aether:'+path.stem+suffix
                body={'description':{'identifier':ident_name},'tags':['stonecutter'],
                  'ingredients':[option],'result':{'item':output,'count':count}}
                target=out/(ident_name.split(':',1)[1]+'.json')
                target.write_text(json.dumps({'format_version':'1.20.10','minecraft:recipe_shapeless':body},indent=2)+'\n',encoding='utf-8')
                record(target,recipe_type)
            continue
        if recipe_type in {'minecraft:smelting','minecraft:blasting'}:
            raw=recipe.get('ingredient',[])
            ingredients=raw if isinstance(raw,list) else [raw]
            options=[]
            for ingredient in ingredients:options.extend(ingredient_options(ingredient))
            count=recipe.get('result',{}).get('count',1)
            if not output or not options or count != 1:
                skipped['unresolved_ingredient']=skipped.get('unresolved_ingredient',0)+1;continue
            tag='blast_furnace' if recipe_type=='minecraft:blasting' else 'furnace'
            for ordinal,option in enumerate(options,1):
                if 'item' not in option:
                    skipped['unresolved_ingredient']=skipped.get('unresolved_ingredient',0)+1;continue
                suffix=f'_v{ordinal}' if len(options)>1 else ''
                ident_name='minizin_aether:'+path.stem+suffix
                body={'description':{'identifier':ident_name},'tags':[tag],
                  'input':option['item'],'output':output}
                target=out/(ident_name.split(':',1)[1]+'.json')
                target.write_text(json.dumps({'format_version':'1.20.10','minecraft:recipe_furnace':body},indent=2)+'\n',encoding='utf-8')
                record(target,recipe_type)
            continue
        if recipe_type not in {'minecraft:crafting_shaped','minecraft:crafting_shapeless'}:
            skipped[recipe_type]=skipped.get(recipe_type,0)+1;continue
        if not output or not output.startswith('minizin_aether:'):
            skipped['missing_output']=skipped.get('missing_output',0)+1;continue
        if recipe_type=='minecraft:crafting_shaped':
            key_entries=[]
            for key,value in recipe.get('key',{}).items():key_entries.append((key,ingredient_options(value)))
            combinations=variants(key_entries)
            if not combinations:skipped['unresolved_ingredient']=skipped.get('unresolved_ingredient',0)+1;continue
            for ordinal,combination in enumerate(combinations,1):
                body={'description':{'identifier':'minizin_aether:'+path.stem+(f'_v{ordinal}' if len(combinations)>1 else '')},'tags':['crafting_table'],
                  'pattern':recipe.get('pattern',[]),'key':combination,'result':{'item':output,'count':recipe.get('result',{}).get('count',1)}}
                target=out/(body['description']['identifier'].split(':',1)[1]+'.json');target.write_text(json.dumps({'format_version':'1.20.10','minecraft:recipe_shaped':body},indent=2)+'\n',encoding='utf-8');record(target,recipe_type)
        else:
            entries=[(str(index),ingredient_options(value)) for index,value in enumerate(recipe.get('ingredients',[]))]
            combinations=variants(entries)
            if not combinations:skipped['unresolved_ingredient']=skipped.get('unresolved_ingredient',0)+1;continue
            for ordinal,combination in enumerate(combinations,1):
                body={'description':{'identifier':'minizin_aether:'+path.stem+(f'_v{ordinal}' if len(combinations)>1 else '')},'tags':['crafting_table'],
                  'ingredients':[combination[str(index)] for index in range(len(entries))],'result':{'item':output,'count':recipe.get('result',{}).get('count',1)}}
                target=out/(body['description']['identifier'].split(':',1)[1]+'.json');target.write_text(json.dumps({'format_version':'1.20.10','minecraft:recipe_shapeless':body},indent=2)+'\n',encoding='utf-8');record(target,recipe_type)
    # The block recipe is ordinary Java crafting and is kept explicit because
    # the custom IncubationRecipe serializers above are intentionally not
    # emitted as invalid Bedrock crafting JSON.
    incubator_target=out/'incubator.json'
    incubator_body={'description':{'identifier':'minizin_aether:incubator'},'tags':['crafting_table'],
      'pattern':['HHH','HTH','HHH'],'key':{'H':{'item':'minizin_aether:holystone'},'T':{'item':'minizin_aether:ambrosium_torch'}},
      'result':{'item':'minizin_aether:incubator','count':1}}
    incubator_target.write_text(json.dumps({'format_version':'1.20.10','minecraft:recipe_shaped':incubator_body},indent=2)+'\n',encoding='utf-8');record(incubator_target,'minecraft:crafting_shaped')
    return {'written':len(written),'written_by_type':written_by_type,'skipped':skipped,'registered_ids':len(registered)}


def write(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(doc,indent=2)+'\n')


def adapt_source_animation(animation):
    """Convert the pinned Mowzie animation channel wrappers to Bedrock arrays."""
    result=json.loads(json.dumps(animation))
    for bone in result.get('bones',{}).values():
        for channel,data in list(bone.items()):
            if not isinstance(data,dict):
                continue
            if 'vector' in data:
                bone[channel]=data['vector']
            else:
                bone[channel]={
                  time:(value['vector'] if isinstance(value,dict) and 'vector' in value else value)
                  for time,value in data.items() if time!='easing' and time!='easingArgs'
                }
    return result


def add_waystone_scrolls(rp,bp,registry):
    """Stage the Java Waystones scroll family with original source icons."""
    source=ROOT/'bedrock/packs/waystones'
    names=('blank_scroll','bound_scroll','warp_scroll','return_scroll')
    item_dir=bp/'items/waystones_v2';recipe_dir=bp/'recipes/waystones_v2'
    texture_dir=rp/'textures/waystones_v2/items/waystones'
    item_dir.mkdir(parents=True,exist_ok=True);recipe_dir.mkdir(parents=True,exist_ok=True);texture_dir.mkdir(parents=True,exist_ok=True)
    count=0
    for name in names:
        item=json.loads((source/'BP/items'/f'{name}.json').read_text(encoding='utf-8'))
        icon=f'waystones_v2_minizin_{name}'
        item['minecraft:item']['components']['minecraft:icon']={'textures':{'default':icon}}
        write(item_dir/f'{name}.json',item)
        shutil.copy2(source/'RP/textures/items/waystones'/f'{name}.png',texture_dir/f'{name}.png')
        registry.setdefault('texture_data',{})[icon]={'textures':f'textures/waystones_v2/items/waystones/{name}'}
        recipe=source/'BP/recipes'/f'{name}.json'
        if recipe.is_file():shutil.copy2(recipe,recipe_dir/f'{name}.json')
        count+=1
    return count


def add_bop_worldgen(rp,bp):
    """Integrate the source-derived BOP biome layer into the combined pack.

    The Java biome router cannot be reproduced by a Bedrock script, but the
    pinned world builder produces real named biome definitions, native
    replacement rules and source-aware vegetation. Generate that layer during
    every combined build so it cannot silently depend on an ignored artifact.
    """
    with tempfile.TemporaryDirectory(prefix='minizin_bop_') as temp:
        temp_root=Path(temp)
        subprocess.run([sys.executable,str(ROOT/'bedrock/worlds/build_worlds.py'),
                        '--mod','bop','--output',str(temp_root)],
                       cwd=ROOT,check=True,capture_output=True,text=True)
        source=temp_root/'bop'
        for role,folders in ((bp,('biomes','feature_rules','features')),
                             (rp,('biomes_client',))):
            for folder in folders:
                src=source/('BP' if role is bp else 'RP')/folder
                if src.is_dir():shutil.copytree(src,role/folder,dirs_exist_ok=True)
        scripts=bp/'scripts/bop_worldgen';scripts.mkdir(parents=True,exist_ok=True)
        for name in ('main.js','native_biomes.js'):
            shutil.copy2(source/'BP/scripts'/name,scripts/name)
        main=bp/'scripts/main.js'
        lines=main.read_text(encoding='utf-8').splitlines() if main.exists() else []
        import_line='import "./bop_worldgen/main.js";'
        if import_line not in lines:lines.insert(0,import_line)
        main.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        return len(list((source/'BP/biomes').glob('*.json')))


def repair(source,output):
    if output.exists():raise ValueError('Fresh output required')
    shutil.copytree(source,output)
    for addon in output.glob('*.mcaddon'):addon.unlink()
    rp,bp=output/'RP',output/'BP'
    # Preserve all existing models and move entity meshes to the canonical loader root.
    for path in list((rp/'models').rglob('*.geo.json')):
        rel=path.relative_to(rp/'models')
        if rel.parts[0] in ['entity','blocks']:continue
        if len(rel.parts)>2 and rel.parts[1] in ['entity','blocks']:
            dest=rp/'models'/rel.parts[1]/rel.parts[0]/Path(*rel.parts[2:]);dest.parent.mkdir(parents=True,exist_ok=True)
            path.rename(dest)
    languages={'en_US':{},'pt_BR':{}}
    upstream={ 'mca':'33-mca-reborn','rftools':'54-rftools','origins':'55-origins','aether':'41-the-aether',
      'biomesoplenty':'19-biomes-o-plenty','iceandfire':'16-ice-and-fire','cataclysm':'43-cataclysm','alexscaves':'42-alexs-caves','mowziesmobs':'44-mowzies-mobs'}
    dictionaries={};language_warnings=[]
    for namespace,mod in upstream.items():
        dictionaries[namespace]={}
        for language in languages:
            lang_root=ROOT/'mods'/mod/'upstream'
            files=[]
            for extension in ('json','lang'):
                files.extend(lang_root.glob('**/assets/'+namespace+'/lang/'+language.lower()+'.'+extension))
            dictionaries[namespace][language]={}
            for file in files:
                try:
                    if file.suffix.lower()=='.json':
                        dictionaries[namespace][language].update(json.loads(file.read_text(encoding='utf-8-sig'),strict=False))
                    else:
                        for line in file.read_text(encoding='utf-8-sig',errors='replace').splitlines():
                            line=line.strip()
                            if not line or line.startswith('#') or '=' not in line:continue
                            key,value=line.split('=',1)
                            dictionaries[namespace][language][key.strip()]=value.strip()
                except (ValueError,UnicodeError) as error:language_warnings.append({'source':str(file.relative_to(ROOT)),'error':str(error)})
    def humanized_name(value):
        # Generated identifiers can contain both snake_case and Java-style
        # camelCase fragments (for example syringeitem0). Keep the fallback
        # readable without pretending it is an upstream translation.
        value=re.sub(r'([a-z])([A-Z])',r'\1 \2',str(value))
        value=re.sub(r'([A-Za-z])(\d+)$',r'\1 \2',value)
        value=re.sub(r'[_-]+',' ',value).strip()
        return value.title() or 'Unnamed'
    def valid_title(value):
        text=str(value or '').replace('\\n',' ').strip()
        return bool(text) and '\ufffd' not in text and not any(ord(char)<32 for char in text)
    def portuguese_fallback(value):
        text=humanized_name(value)
        replacements=((' Bottom',' Base'),(' Top',' Topo'),(' Slab',' Laje'),
          (' Block',' Bloco'),(' Leaves',' Folhas'),(' Leaf',' Folha'),
          (' Log',' Tronco'),(' Wood',' Madeira'),(' Planks',' Tábuas'),
          (' Sapling',' Muda'),(' Flower',' Flor'),(' Grass',' Grama'),
          (' Plant',' Planta'),(' Lit',' Aceso'),(' Alt',' Alternativo'),
          (' Light ',' Luz '),(' Dark ',' Escuro '))
        for source_text,target_text in replacements:text=text.replace(source_text,target_text)
        return text
    def rftools_fallback(value):
        text=str(value)
        for prefix in ('items_','envmodules_','modules_','storage_'):
            text=text.replace(prefix,'')
        text=re.sub(r'emoduleitem$', '_module', text)
        text=re.sub(r'moduleitem$', '_module', text)
        text=re.sub(r'iteml(\d+)$', r'_item_l\1', text)
        text=re.sub(r'item(\d+)$', r'_\1', text)
        for source_text,target_text in (
          ('advchargedporter','advanced_charged_porter'),
          ('chargedporter','charged_porter'),('elevatorbutton','elevator_button'),
          ('machineinformation','machine_information'),('networkmonitor','network_monitor'),
          ('powercellcard','power_cell_card'),('securitycard','security_card'),
          ('shapecard','shape_card'),('smartwrench','smart_wrench'),
          ('teleportprobe','teleport_probe'),('dimensionalshard','dimensional_shard'),
          ('developersdelight','developers_delight')):
            text=text.replace(source_text,target_text)
        return portuguese_fallback(text)
    def source_name_candidates(namespace,name):
        candidates=[name]
        if namespace=='rftools':
            candidate=name
            for prefix in ('items_','envmodules_','modules_','storage_'):
                if candidate.startswith(prefix):candidate=candidate[len(prefix):]
            candidates.append(candidate)
            candidates.append(re.sub(r'moduleitem$', '_module', candidate))
            candidates.append(re.sub(r'emoduleitem$', '_module', candidate))
            candidates.append(re.sub(r'iteml\d+$', '', candidate))
            candidates.append(re.sub(r'item\d+$', '', candidate))
            candidates.append(re.sub(r'item$', '', candidate))
        return list(dict.fromkeys(candidates))
    pt_overrides={
      'minizin:andesite_waystone_block':'Marco de Teleporte',
      'minizin:warp_stone':'Pedra de Teleporte',
      'minizin:blank_scroll':'Pergaminho em Branco',
      'minizin:bound_scroll':'Pergaminho Vinculado',
      'minizin:warp_scroll':'Pergaminho de Teleporte',
      'minizin:return_scroll':'Pergaminho de Retorno',
      'minizin_aether:iron_ring':'Anel de Ferro',
      'minizin_aether:golden_ring':'Anel de Ouro',
      'minizin_aether:ice_ring':'Anel de Gelo',
      'minizin_aether:zanite_ring':'Anel de Zanite',
      'minizin_iceandfire:dragon_meal':'Comida de Dragão',
      'minizin_iceandfire:creative_dragon_meal':'Comida de Dragão Criativa',
      'minizin_iceandfire:dragon_flute':'Flauta de Dragão',
      'minizin_iceandfire:dragon_armor_iron':'Armadura de Dragão de Ferro',
      'minizin_alexscaves:serene_salad':'Salada Serena',
    }
    armor_material_titles={
      'iron':'Armadura de Ferro para Dragão',
      'gold':'Armadura de Ouro para Dragão',
      'diamond':'Armadura de Diamante para Dragão',
      'silver':'Armadura de Prata para Dragão',
      'copper':'Armadura de Cobre para Dragão',
      'dragonsteel_fire':'Armadura de Aço Dracônico de Fogo',
      'dragonsteel_ice':'Armadura de Aço Dracônico de Gelo',
      'dragonsteel_lightning':'Armadura de Aço Dracônico Elétrico',
    }
    def translated(kind,ident):
        ns,name=ident.split(':',1)
        armor_match=re.fullmatch(r'minizin_iceandfire:dragonarmor_(iron|gold|diamond|silver|copper|dragonsteel_fire|dragonsteel_ice|dragonsteel_lightning)_(head|neck|body|tail)',ident)
        if kind=='item' and armor_match:
            material=armor_match.group(1)
            key='item.'+ident+'.name'
            source_key='item.iceandfire.dragonarmor_'+material
            for language in languages:
                title=dictionaries.get('iceandfire',{}).get(language,{}).get(source_key,armor_material_titles[material])
                if language=='pt_BR':title=armor_material_titles[material]
                languages[language][key]=str(title).replace('\\n',' ')
            return key
        if ns=='minizin':
            namespace,name=name.split('_',1)
            if name.startswith('item_'):name=name[5:]
        else:namespace=ns.removeprefix('minizin_')
        key=('tile.' if kind=='block' else 'item.')+ident+'.name'
        for language in languages:
            originals=dictionaries.get(namespace,{}).get(language,{})
            title=''
            for candidate in source_name_candidates(namespace,name):
                source_kind='tile' if kind=='block' else 'item'
                for source_key in (source_kind+'.'+namespace+'.'+candidate+'.name',source_kind+'.'+namespace+'.'+candidate,
                                   source_kind+'.'+candidate+'.name',source_kind+'.'+candidate,
                                   kind+'.'+namespace+'.'+candidate+'.name',kind+'.'+namespace+'.'+candidate,
                                   kind+'.'+candidate+'.name',kind+'.'+candidate):
                    title=originals.get(source_key,'')
                    if valid_title(title):break
                if valid_title(title):break
            if language=='pt_BR' and ident in pt_overrides:title=pt_overrides[ident]
            if namespace=='rftools' and re.search(r'(?:moduleitem|iteml\d*|porteritem)',str(title),re.I):
                title=rftools_fallback(name)
            if not valid_title(title):
                # A corrupt/missing upstream value must never reach Bedrock as
                # replacement glyphs or a technical identifier. If English is
                # valid, retain its source name; otherwise use a readable
                # generated fallback. This does not claim Java translation
                # parity where no source localization exists.
                english=''
                for candidate in source_name_candidates(namespace,name):
                    english_map=dictionaries.get(namespace,{}).get('en_US',{})
                    source_kind='tile' if kind=='block' else 'item'
                    for source_key in (source_kind+'.'+namespace+'.'+candidate+'.name',source_kind+'.'+namespace+'.'+candidate,
                                       source_kind+'.'+candidate+'.name',source_kind+'.'+candidate,
                                       kind+'.'+namespace+'.'+candidate+'.name',kind+'.'+namespace+'.'+candidate,
                                       kind+'.'+candidate+'.name',kind+'.'+candidate):
                        english=english_map.get(source_key,'')
                        if valid_title(english):break
                    if valid_title(english):break
                title=english if valid_title(english) else (portuguese_fallback(name) if language=='pt_BR' else humanized_name(name))
            if namespace=='rftools' and re.search(r'(?:moduleitem|iteml\d*|porteritem)',str(title),re.I):
                title=rftools_fallback(name)
            languages[language][key]=str(title).replace('\n',' ')
        return key
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    accessory_count=add_aether_accessories(rp,bp)
    aether_material_count=add_aether_material_items(rp,bp)
    aether_freezer_item_count=add_aether_freezer_items(rp,bp)
    aether_incubator_item_count=add_aether_incubator_items(rp,bp)
    aether_enchanting_item_count=add_aether_enchanting_items(rp,bp)
    creature_item_count=add_creature_items(rp,bp)
    mowzie_sun_bosses=add_source_backed_mowzie_sun_bosses(rp,bp)
    # add_aether_accessories updates the on-disk atlas; continue with that
    # merged registry so later block/item processing cannot erase its entries.
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    mowzie_item_count=add_source_backed_mowzie_items(rp,bp,registry)
    waystone_scroll_count=add_waystone_scrolls(rp,bp,registry)
    bop_biome_count=add_bop_worldgen(rp,bp)
    terrain=json.loads((rp/'textures/terrain_texture.json').read_text())['texture_data']
    geometries={}
    for path in (rp/'models').rglob('*.geo.json'):
        for geo in json.loads(path.read_text()).get('minecraft:geometry',[]):geometries[geo['description']['identifier']]=geo
    block_items=0
    for path in (bp/'blocks').rglob('*.json'):
        doc=json.loads(path.read_text());block=doc['minecraft:block'];ident=block['description']['identifier']
        comp=block['components'];display=translated('block',ident);comp['minecraft:display_name']=display
        material=comp['minecraft:material_instances']['*'];atlas_ref=terrain[material['texture']]['textures']
        atlas=Image.open(rp/(atlas_ref+'.png')).convert('RGBA')
        geometry_spec=comp.get('minecraft:geometry')
        geometry_id=geometry_spec.get('identifier') if isinstance(geometry_spec,dict) else geometry_spec
        geo=geometries.get(geometry_id,{})
        candidates=[]
        for bone in geo.get('bones',[]):
            for cube in bone.get('cubes',[]):
                faces=cube.get('uv',{})
                if not isinstance(faces,dict):continue
                for face in faces.values():
                    uv=face.get('uv',[0,0]);size=face.get('uv_size',[0,0])
                    x0,y0=uv;x1,y1=x0+size[0],y0+size[1]
                    box=(round(min(x0,x1)),round(min(y0,y1)),round(max(x0,x1)),round(max(y0,y1)))
                    if box[2]<=box[0] or box[3]<=box[1]:continue
                    image=atlas.crop(box)
                    if x1<x0:image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if y1<y0:image=image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    alpha=image.getchannel('A');score=sum(alpha.getdata())
                    if score>0:candidates.append((score,image))
        image=max(candidates,key=lambda x:x[0])[1] if candidates else atlas
        if image.getchannel('A').getbbox() is None:raise ValueError('Original atlas fully transparent '+ident)
        icon='minizin_block_icon_'+ident.replace(':','_');texture='textures/items/block_icons/'+icon
        (rp/'textures/items/block_icons').mkdir(parents=True,exist_ok=True);image.save(rp/(texture+'.png'))
        registry['texture_data'][icon]={'textures':texture}
        # A real block-placer item with an explicit original-pixel icon overrides
        # the invisible autogenerated inventory representation, preserving world geometry.
        # Do not create a second item definition when the source pack already
        # registered the block item (Waystones does this). Duplicate item IDs
        # can make Bedrock reject the whole behavior pack. Update the existing
        # definition in place so its block placer/data stays authoritative.
        existing_items=[]
        for item_path in (bp/'items').rglob('*.json'):
            item_doc=json.loads(item_path.read_text())
            if item_doc.get('minecraft:item',{}).get('description',{}).get('identifier')==ident:
                existing_items.append((item_path,item_doc))
        if len(existing_items)>1:
            # Older generated candidates may already contain the duplicate
            # created by this repair phase. The build output is disposable, so
            # retain the authoritative block-placer definition and discard
            # only the redundant generated copies before continuing.
            authoritative=next((pair for pair in existing_items
                                 if 'minecraft:block_placer' in pair[1]['minecraft:item'].get('components',{})),
                                existing_items[0])
            for duplicate_path,_ in existing_items:
                if duplicate_path != authoritative[0]:
                    duplicate_path.unlink()
            existing_items=[authoritative]
        if existing_items:
            item_path,item_doc=existing_items[0]
            item_comp=item_doc['minecraft:item'].setdefault('components',{})
            item_comp['minecraft:icon']={'textures':{'default':icon}}
            item_comp['minecraft:display_name']={'value':display}
            item_comp.setdefault('minecraft:block_placer',{'block':ident})
            write(item_path,item_doc)
        else:
            write(bp/'items/block_icons'/f'{icon}.json',{'format_version':'1.21.90','minecraft:item':{
              'description':{'identifier':ident,'menu_category':{'category':'construction'}},
              'components':{'minecraft:icon':{'textures':{'default':icon}},'minecraft:display_name':{'value':display},
                'minecraft:block_placer':{'block':ident},'minecraft:max_stack_size':64}}})
        write(path,doc);block_items+=1
    spawnable={}
    for path in (bp/'entities').rglob('*.json'):
        doc=json.loads(path.read_text(encoding='utf-8'))
        entity=doc.get('minecraft:entity',{}).get('description',{})
        if entity.get('identifier'):
            spawnable[entity['identifier']]=bool(entity.get('is_spawnable',False))
    for path in (bp/'items').rglob('*.json'):
        doc=json.loads(path.read_text());item=doc['minecraft:item'];ident=item['description']['identifier'];comp=item['components']
        if ident.startswith('minizin_') and 'minecraft:block_placer' in comp:continue
        comp['minecraft:display_name']={'value':translated('item',ident)}
        if isinstance(comp.get('minecraft:icon'),str):comp['minecraft:icon']={'textures':{'default':comp['minecraft:icon']}}
        if 'minecraft:icon' not in comp:
            candidates=[ident.replace(':','_'),path.stem]
            icon=next((candidate for candidate in candidates if candidate in registry.get('texture_data',{})),None)
            if icon:
                comp['minecraft:icon']={'textures':{'default':icon}}
        if 'ring' in ident:comp['minecraft:max_stack_size']=1
        write(path,doc)
    aether_recipe_report=add_aether_recipes(bp)
    for path in (rp/'entity').rglob('*.json'):
        doc=json.loads(path.read_text());desc=doc['minecraft:client_entity']['description'];ident=desc['identifier']
        if not spawnable.get(ident,True):
            # Migration-only entities must never regain a creative spawn egg.
            desc.pop('spawn_egg',None)
            write(path,doc)
            continue
        # Bedrock localizes the entity itself and the inventory spawn egg with
        # separate keys. Some versions/resource packs request the egg key without
        # the final .name; keep both aliases for the *same* translated entity.
        namespace,entity_name=ident.split(':',1)
        source_namespace=namespace.removeprefix('minizin_')
        original_key='entity.'+source_namespace+'.'+entity_name
        for language in languages:
            original=dictionaries.get(source_namespace,{}).get(language,{})
            title=original.get(original_key,entity_name.replace('_',' ').title())
            for key in ('entity.'+ident+'.name',
                        'item.spawn_egg.entity.'+ident+'.name',
                        'item.spawn_egg.entity.'+ident):
                languages[language][key]=str(title).replace('\\n',' ')
        tex=rp/(desc['textures']['default']+'.png');im=Image.open(tex).convert('RGBA')
        colors=sorted(im.getcolors(im.width*im.height) or [],reverse=True)
        palette=[c for _,c in colors if c[3]>128 and max(c[:3])>45]
        if not palette:raise ValueError('Entity original texture fully transparent '+ident)
        color=lambda c:'#'+''.join(f'{v:02x}' for v in c[:3])
        desc['spawn_egg']={'base_color':color(palette[0]),'overlay_color':color(palette[min(3,len(palette)-1)])}
        write(path,doc)
    # Compatibility aliases for the pre-PR creature namespace used by older
    # worlds/screenshots. Keep the canonical IDs unchanged; these keys only
    # prevent raw localization strings when Bedrock resolves legacy stacks.
    legacy_names={
      'item.minizin_creatures:dragon_meal.name':'Comida de Dragão',
      'item.minizin_creatures:creative_dragon_meal.name':'Comida de Dragão Criativa',
      'item.spawn_egg.entity.minizin_creatures:atlatitan.name':'Atlatitan',
      'item.spawn_egg.entity.minizin_creatures:atlatitan':'Atlatitan'}
    for language in languages:
        for key,value in legacy_names.items():
            languages[language].setdefault(key,value if language=='pt_BR' else {
              'item.minizin_creatures:dragon_meal.name':'Dragon Meal',
              'item.minizin_creatures:creative_dragon_meal.name':'Creative Dragon Meal',
              'item.spawn_egg.entity.minizin_creatures:atlatitan.name':'Atlatitan',
              'item.spawn_egg.entity.minizin_creatures:atlatitan':'Atlatitan'}[key])
    write(registry_path,registry)
    for language,entries in languages.items():
        target=rp/'texts'/f'{language}.lang';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text('\n'.join(k+'='+v for k,v in sorted(entries.items()))+'\n',encoding='utf-8')
    write(rp/'texts/languages.json',list(languages))
    # Refresh the shared creature runtime from source after every repair build;
    # otherwise a new combined candidate would silently keep the previous
    # dragon interaction implementation.
    shutil.copy2(ROOT/'bedrock/runtime/creatures.js',bp/'scripts/creatures.js')
    add_dragon_armor_layers(rp,bp)
    shutil.copy2(ROOT/'bedrock/runtime/item_actions.js',bp/'scripts/item_actions.js')
    # Refresh the Waystones runtime as well.  This matters because the block
    # migration/visibility fix is shared with the standalone pack and must not
    # be silently lost when the combined addon is rebuilt from an older stage.
    shutil.copy2(ROOT/'bedrock/runtime/waystones_block.js',bp/'scripts/waystones_v2/waystones_block.js')
    shutil.copy2(ROOT/'bedrock/runtime/warp_stone.js',bp/'scripts/waystones_v2/warp_stone.js')
    shutil.copy2(ROOT/'bedrock/runtime/waystone_scrolls.js',bp/'scripts/waystones_v2/waystone_scrolls.js')
    waystone_main=bp/'scripts/waystones_v2/main.js'
    waystone_lines=waystone_main.read_text(encoding='utf-8').splitlines() if waystone_main.exists() else []
    if 'import "./waystone_scrolls.js";' not in waystone_lines:
        waystone_lines.append('import "./waystone_scrolls.js";')
    waystone_main.write_text('\n'.join(dict.fromkeys(line for line in waystone_lines if line.strip()))+'\n',encoding='utf-8')
    # Refresh Origins from the audited source as well.  The combined candidate
    # previously kept a stale copy, so new Java-backed powers could pass in the
    # standalone pack while silently disappearing from the Android addon.
    origins_script=bp/'scripts/origins/origins.js'
    if origins_script.parent.is_dir():
        shutil.copy2(ROOT/'bedrock/packs/next_four/BP/scripts/origins.js',origins_script)
    # Port the source-backed Aether Freezer recipe runtime into the combined
    # pack. The old candidate only counted these custom serializers and left
    # the visible block inert.
    aether_scripts=bp/'scripts/aether_full_v3';aether_scripts.mkdir(parents=True,exist_ok=True)
    # Re-copy the authoritative world runtime before appending the machine
    # modules. This prevents the combined addon from silently retaining an
    # older Aether startup/dimension implementation.
    shutil.copy2(ROOT/'bedrock/worlds/aether/main.js',aether_scripts/'main.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer.js',aether_scripts/'aether_freezer.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer_catalog.js',aether_scripts/'aether_freezer_catalog.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_incubator.js',aether_scripts/'aether_incubator.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_incubator_catalog.js',aether_scripts/'aether_incubator_catalog.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_altar.js',aether_scripts/'aether_altar.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_altar_catalog.js',aether_scripts/'aether_altar_catalog.js')
    aether_main=aether_scripts/'main.js'
    aether_lines=aether_main.read_text(encoding='utf-8').splitlines() if aether_main.exists() else []
    if 'import "./aether_freezer.js";' not in aether_lines:aether_lines.append('import "./aether_freezer.js";')
    if 'import "./aether_incubator.js";' not in aether_lines:aether_lines.append('import "./aether_incubator.js";')
    if 'import "./aether_altar.js";' not in aether_lines:aether_lines.append('import "./aether_altar.js";')
    # Do not deduplicate Aether source lines: repeated control-flow lines are
    # meaningful JavaScript.  Only remove blank padding while keeping order
    # and every original statement intact.
    aether_main.write_text('\n'.join(line for line in aether_lines if line.strip())+'\n',encoding='utf-8')
    # Keep the entrypoint idempotent.  Re-running this repair used to append
    # item_actions.js repeatedly, producing noisy and fragile combined packs.
    main=bp/'scripts/main.js'
    lines=main.read_text(encoding='utf-8').splitlines()
    imports=[];body=[]
    for line in lines:
        if line.strip().startswith('import ') and line.strip().endswith(';'):
            if line.strip() in imports:continue
            imports.append(line.strip())
        else:body.append(line)
    if 'import "./item_actions.js";' not in imports:
        imports.append('import "./item_actions.js";')
    main.write_text('\n'.join(imports+['']+[line for line in body if line.strip()])+'\n',encoding='utf-8')
    for role in ['RP','BP']:
        path=output/role/'manifest.json';doc=json.loads(path.read_text());doc['header']['name']='Minizin Correção Mobile '+role
        doc['header']['version']=[0,2,2]
        # BOP native biome definitions use the 1.21.110 schema. Keep the
        # existing beta server dependency: Aether's registerCustomDimension
        # contract is stronger than BOP's optional getBiome decoration API.
        doc['header']['min_engine_version']=[1,21,110]
        for module in doc['modules']:module['version']=[0,2,2]
        for dependency in doc.get('dependencies',[]):
            if 'uuid' in dependency:dependency['version']=[0,2,2]
        write(path,doc)
    counts=check([output]);write(output/'FIX_REPORT.json',{'structural':counts,'explicit_block_icons':block_items,
      'aether_accessories':accessory_count,'aether_materials':aether_material_count,'creature_items':creature_item_count,
      'mowzie_sun_bosses':mowzie_sun_bosses,
      'mowzie_items':mowzie_item_count,
      'aether_freezer_items':aether_freezer_item_count,
      'aether_enchanting_items':aether_enchanting_item_count,
      'aether_incubator_items':aether_incubator_item_count,
      'waystone_scrolls':waystone_scroll_count,
      'bop_biomes':bop_biome_count,
      'aether_freezer_recipes':9,
      'aether_recipes':aether_recipe_report,
      'fixes':['Preserved models/entity and models/blocks loader paths','Original-pixel explicit block placer icons',
        'Names from upstream language files where available','Individual spawn egg colors from original textures',
         'MCA rings: 50 affinity engagement, 100 marriage','Origins orb opens original selection menu',
         'Aether vanilla recipes converted only when source IDs resolve in the BP',
         'AetherItemTiers durability, damage, enchantability and digger components preserved'],
      'language_warnings':language_warnings,'android_retest_pending':True,'remaining':['Unimplemented catalog items','Full animation/AI ports','World generation and dimensions']})
    addon=output/'Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon'
    with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
        for role in ['RP','BP']:archive.writestr('Minizin_Mobile_'+role+'.mcpack',zipped(output/role))
    assert zipfile.ZipFile(addon).testzip() is None
    print(json.dumps({'file':str(addon),'validation':counts,'block_icons':block_items}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();repair(args.source,args.output)
