#!/usr/bin/env python3
"""Build a fresh Android retest candidate using original textures and rigs."""
import argparse,json,shutil,zipfile
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
      for kind in ['pickaxe','axe','shovel']]
    names += [tier+'_sword' for tier in ['skyroot','holystone','zanite','gravitite','flaming']]
    names += ['vampire_blade','iron_ring','golden_ring','ice_ring','zanite_ring']
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
        is_ring=name.endswith('_ring')
        components={'minecraft:icon':{'textures':{'default':key}},
                    'minecraft:max_stack_size':1,
                    'minecraft:display_name':{'value':'item.'+ident+'.name'}}
        if not is_ring:
            components['minecraft:hand_equipped']=True
        catalog[ident]={'ring':is_ring}
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
    registry_path=rp/'textures/item_texture.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    for ident,source in sources.items():
        if not source.is_file():
            continue
        name=ident.replace(':','_')
        rel='textures/items/creatures/'+name
        target=rp/(rel+'.png');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        registry.setdefault('texture_data',{})[name]={'textures':rel}
        write(bp/'items/creatures'/f'{name}.json',{
          'format_version':'1.21.90','minecraft:item':{
            'description':{'identifier':ident,'menu_category':{'category':'items'}},
            'components':{'minecraft:icon':{'textures':{'default':name}},
              'minecraft:display_name':{'value':'item.'+ident+'.name'},
              'minecraft:max_stack_size':64}}})
    write(registry_path,registry)
    return len([x for x in sources.values() if x.is_file()])


def write(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(doc,indent=2)+'\n')


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
    def translated(kind,ident):
        ns,name=ident.split(':',1)
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
    creature_item_count=add_creature_items(rp,bp)
    # add_aether_accessories updates the on-disk atlas; continue with that
    # merged registry so later block/item processing cannot erase its entries.
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
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
        geo=geometries[comp['minecraft:geometry']['identifier']]
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
    shutil.copy2(ROOT/'bedrock/runtime/item_actions.js',bp/'scripts/item_actions.js')
    main=bp/'scripts/main.js';main.write_text(main.read_text()+'\nimport "./item_actions.js";\n')
    for role in ['RP','BP']:
        path=output/role/'manifest.json';doc=json.loads(path.read_text());doc['header']['name']='Minizin Correção Mobile '+role
        doc['header']['version']=[0,2,2]
        for module in doc['modules']:module['version']=[0,2,2]
        for dependency in doc.get('dependencies',[]):
            if 'uuid' in dependency:dependency['version']=[0,2,2]
        write(path,doc)
    counts=check([output]);write(output/'FIX_REPORT.json',{'structural':counts,'explicit_block_icons':block_items,
      'aether_accessories':accessory_count,'creature_items':creature_item_count,
      'fixes':['Preserved models/entity and models/blocks loader paths','Original-pixel explicit block placer icons',
        'Names from upstream language files where available','Individual spawn egg colors from original textures',
        'MCA rings: 50 affinity engagement, 100 marriage','Origins orb opens original selection menu'],
      'language_warnings':language_warnings,'android_retest_pending':True,'remaining':['Unimplemented catalog items','Full animation/AI ports','World generation and dimensions']})
    addon=output/'Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon'
    with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
        for role in ['RP','BP']:archive.writestr('Minizin_Mobile_'+role+'.mcpack',zipped(output/role))
    assert zipfile.ZipFile(addon).testzip() is None
    print(json.dumps({'file':str(addon),'validation':counts,'block_icons':block_items}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();repair(args.source,args.output)
