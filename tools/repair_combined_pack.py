#!/usr/bin/env python3
"""Build a fresh Android retest candidate using original textures and rigs."""
import argparse,json,re,shutil,zipfile
from pathlib import Path
from PIL import Image
from build_bedrock_packs import zipped
from validate_gameplay_packs import check

ROOT=Path(__file__).resolve().parents[1]


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
    return {'written':len(written),'written_by_type':written_by_type,'skipped':skipped,'registered_ids':len(registered)}


def write(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(doc,indent=2)+'\n')


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
            files=list((ROOT/'mods'/mod/'upstream').glob('**/assets/'+namespace+'/lang/'+language.lower()+'.json'))
            dictionaries[namespace][language]={}
            for file in files:
                try:dictionaries[namespace][language].update(json.loads(file.read_text(encoding='utf-8-sig'),strict=False))
                except ValueError as error:language_warnings.append({'source':str(file.relative_to(ROOT)),'error':str(error)})
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
            title=originals.get(kind+'.'+namespace+'.'+name,name.replace('_',' ').title())
            if language=='pt_BR' and ident in pt_overrides:title=pt_overrides[ident]
            languages[language][key]=str(title).replace('\n',' ')
        return key
    registry_path=rp/'textures/item_texture.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    accessory_count=add_aether_accessories(rp,bp)
    aether_material_count=add_aether_material_items(rp,bp)
    aether_freezer_item_count=add_aether_freezer_items(rp,bp)
    creature_item_count=add_creature_items(rp,bp)
    # add_aether_accessories updates the on-disk atlas; continue with that
    # merged registry so later block/item processing cannot erase its entries.
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    waystone_scroll_count=add_waystone_scrolls(rp,bp,registry)
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
    write(registry_path,registry)
    for language,entries in languages.items():
        target=rp/'texts'/f'{language}.lang';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text('\n'.join(k+'='+v for k,v in sorted(entries.items()))+'\n',encoding='utf-8')
    write(rp/'texts/languages.json',list(languages))
    # Refresh the shared creature runtime from source after every repair build;
    # otherwise a new combined candidate would silently keep the previous
    # dragon interaction implementation.
    shutil.copy2(ROOT/'bedrock/runtime/creatures.js',bp/'scripts/creatures.js')
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
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer.js',aether_scripts/'aether_freezer.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer_catalog.js',aether_scripts/'aether_freezer_catalog.js')
    aether_main=aether_scripts/'main.js'
    aether_lines=aether_main.read_text(encoding='utf-8').splitlines() if aether_main.exists() else []
    if 'import "./aether_freezer.js";' not in aether_lines:aether_lines.append('import "./aether_freezer.js";')
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
        for module in doc['modules']:module['version']=[0,2,2]
        for dependency in doc.get('dependencies',[]):
            if 'uuid' in dependency:dependency['version']=[0,2,2]
        write(path,doc)
    counts=check([output]);write(output/'FIX_REPORT.json',{'structural':counts,'explicit_block_icons':block_items,
      'aether_accessories':accessory_count,'aether_materials':aether_material_count,'creature_items':creature_item_count,
      'aether_freezer_items':aether_freezer_item_count,
      'waystone_scrolls':waystone_scroll_count,
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
