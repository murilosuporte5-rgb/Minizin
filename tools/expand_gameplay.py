#!/usr/bin/env python3
"""Incremental functional items and Waystones, preserving the tested combined pack."""
import argparse,json,re,shutil,zipfile,hashlib
from pathlib import Path
from validate_gameplay_packs import check
from build_bedrock_packs import zipped
from upgrade_waystone_block import upgrade as upgrade_waystone

ROOT=Path(__file__).resolve().parents[1]


def expand(source,output):
    if output.exists():raise ValueError('Fresh directory required')
    shutil.copytree(source,output)
    for p in output.glob('*.mcaddon'):p.unlink()
    rp,bp=output/'RP',output/'BP';provenance=[]
    def write(path,doc):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(doc,indent=2)+'\n')
    registry=json.loads((rp/'textures/item_texture.json').read_text());catalog={}
    base=ROOT/'mods/41-the-aether/upstream';assets=base/'src/main/resources/assets/aether'
    tiers={m[0].lower():{'durability':int(m[1]),'speed':float(m[2]),'bonus':float(m[3]),'enchantability':int(m[4])} for m in
      re.findall(r'([A-Z_]+)\(BlockTags\.[^,]+, (\d+), ([\d.]+)F, ([\d.]+)F, (\d+),',
      (base/'src/main/java/com/aetherteam/aether/item/combat/AetherItemTiers.java').read_text())}
    names=[tier+'_'+kind for tier in ['skyroot','holystone','zanite','gravitite','valkyrie'] for kind in ['pickaxe','axe','shovel']]
    names += [tier+'_sword' for tier in ['skyroot','holystone','zanite','gravitite','flaming']]+['vampire_blade']
    names+=['iron_ring','golden_ring','ice_ring','zanite_ring','iron_pendant','golden_pendant','ice_pendant','zanite_pendant',
      'leather_gloves','chainmail_gloves','iron_gloves','golden_gloves','diamond_gloves','netherite_gloves','zanite_gloves',
      'gravitite_gloves','valkyrie_gloves','neptune_gloves','phoenix_gloves','obsidian_gloves','red_cape','blue_cape',
      'yellow_cape','white_cape','agility_cape','swet_cape','invisibility_cloak','valkyrie_cape','golden_feather',
      'regeneration_stone','iron_bubble','shield_of_repulsion']
    accessory_slots={
      **{name:'ring' for name in ['iron_ring','golden_ring','ice_ring','zanite_ring']},
      **{name:'pendant' for name in ['iron_pendant','golden_pendant','ice_pendant','zanite_pendant']},
      **{name:'gloves' for name in ['leather_gloves','chainmail_gloves','iron_gloves','golden_gloves','diamond_gloves','netherite_gloves','zanite_gloves','gravitite_gloves','valkyrie_gloves','neptune_gloves','phoenix_gloves','obsidian_gloves']},
      **{name:'cape' for name in ['red_cape','blue_cape','yellow_cape','white_cape','agility_cape','swet_cape','invisibility_cloak','valkyrie_cape']},
      **{name:'accessory' for name in ['golden_feather','regeneration_stone','iron_bubble']},
      'shield_of_repulsion':'shield'}
    accessory_durability={'zanite_ring':49,'ice_ring':125,'zanite_pendant':98,'ice_pendant':250,
      'leather_gloves':59,'chainmail_gloves':131,'iron_gloves':250,'golden_gloves':32,'diamond_gloves':1561,
      'netherite_gloves':2031,'zanite_gloves':250,'gravitite_gloves':1561,'valkyrie_gloves':1561,
      'neptune_gloves':250,'phoenix_gloves':1561,'obsidian_gloves':2031,'shield_of_repulsion':512}
    translations={}
    for lang in ['en_US','pt_BR']:
        translations[lang]={}
        for path in base.glob('**/assets/aether/lang/'+lang.lower()+'.json'):
            translations[lang].update(json.loads(path.read_text()))
    for name in names:
        found=list((assets/'textures/item').rglob(name+'.png'))
        if not found:raise ValueError('Original icon missing '+name)
        png=found[0];dest=rp/'textures/items/aether_equipment'/png.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(png,dest)
        ident='minizin_aether:'+name;icon='minizin_aether_equipment_'+name
        registry['texture_data'][icon]={'textures':'textures/items/aether_equipment/'+name}
        comp={'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':1,
          'minecraft:display_name':{'value':'item.'+ident+'.name'}}
        spec={'accessory':name in accessory_slots}
        if spec['accessory']:
            spec['slot']=accessory_slots[name]
            if name in accessory_durability:comp['minecraft:durability']={'max_durability':accessory_durability[name]}
        else:
            tier='vampire' if name=='vampire_blade' else name.split('_')[0];kind='sword' if name=='vampire_blade' else name.split('_')[-1]
            values=tiers[tier];comp['minecraft:durability']={'max_durability':values['durability']}
            comp['minecraft:damage']=int(values['bonus']+{'sword':3,'axe':5,'pickaxe':1,'shovel':1.5}[kind])
            comp['minecraft:hand_equipped']=True;comp['minecraft:enchantable']={'slot':kind,'value':values['enchantability']}
            if kind in ['pickaxe','axe','shovel']:
                tags={'pickaxe':'stone','axe':'wood','shovel':'dirt'}
                comp['minecraft:digger']={'use_efficiency':True,'destroy_speeds':[{'block':{'tags':"q.any_tag('"+tags[kind]+"')"},'speed':values['speed']}]}
            if name=='flaming_sword':spec['power']='flaming'
            if name=='vampire_blade':spec['power']='vampire'
        catalog[ident]=spec
        write(bp/'items/aether_equipment'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'equipment'}},'components':comp}})
        for language in translations:
            title=translations[language].get('item.aether.'+name,name.replace('_',' ').title())
            with (rp/'texts'/f'{language}.lang').open('a') as f:f.write('item.'+ident+'.name='+title+'\n')
        provenance.append({'source':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'identifier':ident})
    # The Java Freezer also consumes four source-backed Aether items that are
    # not equipment. Register them here so completion never targets an absent
    # ItemStack ID in the independent gameplay addon.
    freezer_items={
      'skyroot_bucket':'item/miscellaneous/skyroot_bucket.png',
      'skyroot_water_bucket':'item/miscellaneous/skyroot_water_bucket.png',
      'music_disc_chinchilla':'item/miscellaneous/music_disc_chinchilla.png',
      'music_disc_high':'item/miscellaneous/music_disc_high.png',
    }
    freezer_titles={'skyroot_bucket':('Skyroot Bucket','Balde de Skyroot'),
      'skyroot_water_bucket':('Skyroot Water Bucket','Balde de Skyroot com Água'),
      'music_disc_chinchilla':('Sepia Music Disc','Disco de Música Sépia'),
      'music_disc_high':('Super Music Disc','Super Disco de Música')}
    for name,relative in freezer_items.items():
        png=assets/'textures'/relative
        if not png.is_file():raise ValueError('Original Freezer item icon missing '+name)
        ident='minizin_aether:'+name;icon='minizin_aether_freezer_'+name;texture='textures/items/aether_freezer/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(png,target)
        registry['texture_data'][icon]={'textures':texture}
        write(bp/'items/aether_freezer'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},
          'components':{'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':1,
            'minecraft:display_name':{'value':'item.'+ident+'.name'}}}})
        for language in translations:
            title=freezer_titles[name][0 if language=='en_US' else 1]
            with (rp/'texts'/f'{language}.lang').open('a') as f:f.write('item.'+ident+'.name='+title+'\n')
        provenance.append({'source':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'identifier':ident})
    incubator_items={
      'black_moa_egg':'item/miscellaneous/moa_egg.png','blue_moa_egg':'item/miscellaneous/moa_egg.png',
      'white_moa_egg':'item/miscellaneous/moa_egg.png','ambrosium_torch':'block/utility/ambrosium_torch.png'}
    incubator_titles={'black_moa_egg':('Black Moa Egg','Ovo de Moa Preto'),'blue_moa_egg':('Blue Moa Egg','Ovo de Moa Azul'),
      'white_moa_egg':('White Moa Egg','Ovo de Moa Branco'),'ambrosium_torch':('Ambrosium Torch','Tocha de Ambrosium')}
    for name,relative in incubator_items.items():
        png=assets/'textures'/relative
        if not png.is_file():raise ValueError('Original Incubator item icon missing '+name)
        ident='minizin_aether:'+name;icon='minizin_aether_incubator_'+name;texture='textures/items/aether_incubator/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(png,target)
        registry['texture_data'][icon]={'textures':texture}
        write(bp/'items/aether_incubator'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':{
            'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':1,
            'minecraft:display_name':{'value':'item.'+ident+'.name'}}}})
        for language in translations:
            title=incubator_titles[name][0 if language=='en_US' else 1]
            with (rp/'texts'/f'{language}.lang').open('a') as f:f.write('item.'+ident+'.name='+title+'\n')
        provenance.append({'source':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'identifier':ident})
    enchanting_items={
      'blue_berry':'item/food/blue_berry.png','enchanted_berry':'item/food/enchanted_berry.png',
      'golden_dart':'item/weapons/golden_dart.png','enchanted_dart':'item/weapons/enchanted_dart.png',
      'golden_dart_shooter':'item/weapons/golden_dart_shooter.png','enchanted_dart_shooter':'item/weapons/enchanted_dart_shooter.png',
      'healing_stone':'item/food/healing_stone.png','music_disc_aether_tune':'item/miscellaneous/music_disc_aether_tune.png',
      'skyroot_poison_bucket':'item/miscellaneous/skyroot_poison_bucket.png','skyroot_remedy_bucket':'item/miscellaneous/skyroot_remedy_bucket.png'}
    enchanting_titles={'blue_berry':('Blue Berry','Blue Berry'),'enchanted_berry':('Enchanted Berry','Fruta Encantada'),
      'golden_dart':('Golden Dart','Dardo Dourado'),'enchanted_dart':('Enchanted Dart','Dardo Encantado'),
      'golden_dart_shooter':('Golden Dart Shooter','Atirador de Dardos Dourados'),'enchanted_dart_shooter':('Enchanted Dart Shooter','Atirador de Dardos Encantados'),
      'healing_stone':('Healing Stone','Pedra de Cura'),'music_disc_aether_tune':('Blue Music Disc','Disco Azul'),
      'skyroot_poison_bucket':('Skyroot Poison Bucket','Balde Skyroot com Veneno'),'skyroot_remedy_bucket':('Skyroot Remedy Bucket','Balde Skyroot de Remédio')}
    for name,relative in enchanting_items.items():
        png=assets/'textures'/relative
        if not png.is_file():raise ValueError('Original Enchanting item icon missing '+name)
        ident='minizin_aether:'+name;icon='minizin_aether_enchanting_'+name;texture='textures/items/aether_enchanting/'+name
        target=rp/(texture+'.png');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(png,target)
        registry['texture_data'][icon]={'textures':texture}
        max_stack=1 if ('shooter' in name or 'bucket' in name or 'music_disc' in name or name=='healing_stone') else 64
        write(bp/'items/aether_enchanting'/f'{name}.json',{'format_version':'1.21.90','minecraft:item':{
          'description':{'identifier':ident,'menu_category':{'category':'items'}},'components':{
            'minecraft:icon':{'textures':{'default':icon}},'minecraft:max_stack_size':max_stack,
            'minecraft:display_name':{'value':'item.'+ident+'.name'}}}})
        for language in translations:
            title=enchanting_titles[name][0 if language=='en_US' else 1]
            with (rp/'texts'/f'{language}.lang').open('a') as f:f.write('item.'+ident+'.name='+title+'\n')
        provenance.append({'source':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'identifier':ident})
    # Reuse the existing independent Waystones implementation, not a new model.
    ws=ROOT/'bedrock/packs/waystones'
    for role in ['RP','BP']:
        for p in (ws/role).rglob('*'):
            if not p.is_file() or p.name=='manifest.json':continue
            rel=p.relative_to(ws/role)
            target=output/role/rel
            if rel.parts[0]=='scripts':target=bp/'scripts/waystones'/Path(*rel.parts[1:])
            if target.exists():
                # The Aether base already owns the language files. Merge the
                # Waystones keys instead of aborting or overwriting Aether
                # names; all other collisions remain hard failures.
                if rel.parts[0]=='texts' and target.suffix=='.lang':
                    # Older staged packs contain localized bytes in a legacy
                    # single-byte encoding; preserve their characters while
                    # normalizing the merged file to UTF-8.
                    existing=target.read_bytes().decode('utf-8',errors='replace')
                    incoming=p.read_bytes().decode('utf-8',errors='replace')
                    target.write_text(existing.rstrip()+'\n'+incoming.lstrip(),encoding='utf-8')
                    continue
                if rel.as_posix()=='textures/item_texture.json':
                    base_registry=json.loads(target.read_text(encoding='utf-8'))
                    waystone_registry=json.loads(p.read_text(encoding='utf-8'))
                    base_registry.setdefault('texture_data',{}).update(waystone_registry.get('texture_data',{}))
                    target.write_text(json.dumps(base_registry,indent=2)+'\n',encoding='utf-8')
                    continue
                if rel.as_posix()=='textures/terrain_texture.json':
                    base_registry=json.loads(target.read_text(encoding='utf-8'))
                    waystone_registry=json.loads(p.read_text(encoding='utf-8'))
                    base_registry.setdefault('texture_data',{}).update(waystone_registry.get('texture_data',{}))
                    target.write_text(json.dumps(base_registry,indent=2)+'\n',encoding='utf-8')
                    continue
                raise ValueError('Waystone path conflicts '+str(target))
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    # The merge above may have added Waystones item icons; refresh the local
    # registry before the later Aether/warp-stone writes so those icons are
    # not accidentally dropped again.
    merged_registry=json.loads((rp/'textures/item_texture.json').read_text(encoding='utf-8'))
    registry.setdefault('texture_data',{}).update(merged_registry.get('texture_data',{}))
    client=rp/'entity/andesite_waystone.entity.json';doc=json.loads(client.read_text())
    doc['minecraft:client_entity']['description']['spawn_egg']={'base_color':'#8b8d89','overlay_color':'#68b27b'};write(client,doc)
    texture=ROOT/'mods/15-waystones/upstream/common/src/main/resources/assets/waystones/textures/item/warp_stone.png'
    target=rp/'textures/items/warp_stone.png';shutil.copy2(texture,target)
    registry['texture_data']['minizin_warp_stone']={'textures':'textures/items/warp_stone'}
    write(bp/'items/warp_stone.json',{'format_version':'1.21.90','minecraft:item':{'description':{'identifier':'minizin:warp_stone','menu_category':{'category':'items'}},
      'components':{'minecraft:icon':{'textures':{'default':'minizin_warp_stone'}},'minecraft:max_stack_size':1,'minecraft:display_name':{'value':'item.minizin:warp_stone.name'}}}})
    for lang,title in [('pt_BR','Pedra de teleporte — Waystones'),('en_US','Warp Stone — Waystones')]:
        with (rp/'texts'/f'{lang}.lang').open('a') as file:file.write('item.minizin:warp_stone.name='+title+'\nentity.minizin:andesite_waystone.name=Waystone\n')
    write(rp/'textures/item_texture.json',registry)
    write(bp/'recipes/incubator.json',{'format_version':'1.20.10','minecraft:recipe_shaped':{
      'description':{'identifier':'minizin_aether:incubator'},'tags':['crafting_table'],'pattern':['HHH','HTH','HHH'],
      'key':{'H':{'item':'minizin_aether:holystone'},'T':{'item':'minizin_aether:ambrosium_torch'}},
      'result':{'item':'minizin_aether:incubator','count':1}}})
    for name in ['aether_equipment.js','warp_stone.js','aether_incubator.js','aether_incubator_catalog.js','aether_altar.js','aether_altar_catalog.js']:shutil.copy2(ROOT/'bedrock/runtime'/name,bp/'scripts'/name)
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer.js',bp/'scripts/aether_freezer.js')
    shutil.copy2(ROOT/'bedrock/runtime/aether_freezer_catalog.js',bp/'scripts/aether_freezer_catalog.js')
    (bp/'scripts/aether_equipment_catalog.js').write_text('export const EQUIPMENT = '+json.dumps(catalog)+';\n')
    with (bp/'scripts/main.js').open('a') as f:f.write('\nimport "./waystones/main.js";\nimport "./warp_stone.js";\nimport "./aether_equipment.js";\nimport "./aether_freezer.js";\nimport "./aether_incubator.js";\nimport "./aether_altar.js";\n')
    for role in ['RP','BP']:
        path=output/role/'manifest.json';doc=json.loads(path.read_text());doc['header']['version']=[0,2,5]
        doc['header']['name']='Minizin Gameplay + Waystones '+role
        for m in doc['modules']:m['version']=[0,2,5]
        for d in doc.get('dependencies',[]):
            if 'uuid' in d:d['version']=[0,2,5]
        write(path,doc)
    # Convert the old summonable prototype into a placeable block while keeping
    # the entity definition solely for existing-world migration.
    # Some staged Aether locales were exported as Windows-1252. Normalize them
    # before the Waystone upgrader reads/writes locale keys.
    for locale in (rp/'texts').glob('*.lang'):
        raw=locale.read_bytes()
        try:decoded=raw.decode('utf-8')
        except UnicodeDecodeError:decoded=raw.decode('cp1252')
        locale.write_text(decoded,encoding='utf-8')
    waystone_report=upgrade_waystone(output)
    # The v0.2.4 input is still backed by per-player shared storage. Preserve
    # that source, but install the v2 item-bound runtime in the new candidate.
    if not (bp/'scripts/backpack.js').is_file():
        # Aether-only staged sources do not carry the optional backpack
        # runtime. Install the audited item-bound implementation rather than
        # aborting the independent pack build; the item is added by the
        # dedicated Sophisticated Backpacks pack when that pack is selected.
        shutil.copy2(ROOT/'bedrock/runtime/backpack_v2.js',bp/'scripts/backpack.js')
        with (bp/'scripts/main.js').open('a') as f:f.write('\nimport "./backpack.js";\n')
    shutil.copy2(ROOT/'bedrock/runtime/backpack_v2.js',bp/'scripts/backpack.js')
    # Accessory slots are virtual but no longer hijack the native offhand.
    shutil.copy2(ROOT/'bedrock/runtime/aether_equipment_v2.js',bp/'scripts/aether_equipment.js')
    counts=check([output]);write(output/'EXPANSION_REPORT.json',{'items_added':len(names)+5,'structural':counts,'provenance':provenance,
      'new_mod':'Waystones custom block with migration path','waystone_block':waystone_report,'backpack_storage':'item-bound v2; legacy migrated once; native container UI not supported','aether_rings':'two persistent virtual slots; not native equipment slots', 'android_retest_pending':True,
      'limits':['Zanite bonus, Gravitite block lifting and Valkyrie reach pending','Golden/iron rings are ornamental accessories in source',
        'Tool harvesting tier and all special drops require Android QA','Weapons/tools currently creative acquisition; Java recipes pending',
        'Immersive Portals renderer, Xaero minimap renderer and Distant Horizons LOD remain unavailable through current BP/RP',
        'Other original mod systems remain incomplete']})
    addon=output/'Minizin_Gameplay_Waystones_Aether_v0.2.5_EXPERIMENTAL.mcaddon'
    with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
        for role in ['RP','BP']:archive.writestr('Minizin_Gameplay_'+role+'.mcpack',zipped(output/role))
    assert zipfile.ZipFile(addon).testzip() is None
    print(json.dumps({'file':str(addon),'new_items':len(names)+1,'validation':counts}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();expand(args.source,args.output)
