#!/usr/bin/env python3
"""Reuse converted geometry and pinned upstream assets in independent test packs.

All derived assets remain in gitignored build/. No claim of Java feature parity.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path
from pose_sequence_to_bedrock import convert, load_geometry
from build_bedrock_packs import validate, zipped

ROOT = Path(__file__).resolve().parents[1]
CONVERSIONS = ROOT/'generated/conversions'
DRAGON_ARMOR_SLOTS = ('head', 'neck', 'body', 'tail')


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'minizin/stages23/'+name))


def manifests(folder, name, scripted):
    for role, kind in [('RP','resources'), ('BP','data')]:
        doc = {'format_version':2, 'header':{'name':'Minizin '+name+' experimental '+role,
            'description':'Original assets; adapted gameplay; Android QA pending',
            'uuid':uid(name+role), 'version':[0,2,0], 'min_engine_version':[1,21,90]},
            'modules':[{'type':kind,'uuid':uid(name+role+'module'),'version':[0,2,0]}]}
        if role == 'BP':
            doc['dependencies']=[{'uuid':uid(name+'RP'),'version':[0,2,0]}]
            if scripted:
                doc['modules'].append({'type':'script','language':'javascript','entry':'scripts/main.js',
                    'uuid':uid(name+'script'),'version':[0,2,0]})
                doc['dependencies'].append({'module_name':'@minecraft/server','version':'2.0.0'})
        write(folder/role/'manifest.json',doc)


def copy_asset(source, dest, report):
    if not source.is_file(): raise ValueError(f'Original asset missing: {source}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest)
    report.append({'source':str(source.relative_to(ROOT)), 'output':str(dest.relative_to(ROOT)),
        'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'strategy':'REUSE_DIRECT'})


def adapt_gecko(animation):
    """Keep original vectors/keys; convert GeckoLib vector wrappers to Bedrock.

    Easing curves are approximated by Bedrock linear interpolation, recorded in QA.
    """
    result=json.loads(json.dumps(animation))
    for bone in result.get('bones',{}).values():
        for channel, data in list(bone.items()):
            if not isinstance(data,dict): continue
            if 'vector' in data:
                bone[channel]=data['vector']
            else:
                bone[channel]={t:v['vector'] if isinstance(v,dict) and 'vector' in v else v for t,v in data.items()}
    return result


def add_entity(folder, name, geo, texture, kind, report, clips=None, sound=None, element=None):
    ident = 'minizin_'+folder.name+':'+name
    rp, bp = folder/'RP', folder/'BP'
    geometry = load_geometry(geo)
    geometry['description']['identifier']='geometry.'+ident.replace(':','.')
    geometry['description'].update(visible_bounds_width=24,visible_bounds_height=24,visible_bounds_offset=[0,5,0])
    write(rp/'models/entity'/f'{name}.geo.json',{'format_version':'1.12.0','minecraft:geometry':[geometry]})
    report.append({'source':str(geo.relative_to(ROOT)), 'strategy':'CONVERT', 'entity':ident,
                   'sha256':hashlib.sha256(geo.read_bytes()).hexdigest()})
    copy_asset(texture,rp/'textures/entity'/f'{name}.png',report)
    description = {'identifier':ident,'materials':{'default':'entity_alphatest'},
        'textures':{'default':f'textures/entity/{name}'}, 'geometry':{'default':geometry['description']['identifier']},
        'render_controllers':[f'controller.render.{folder.name}.{name}'],
        'spawn_egg':{'base_color':'#47382c','overlay_color':'#e1b56f'}}
    if clips:
        description['animations']={}
        description['scripts']={'animate':[]}
        for alias, animation, condition in clips:
            write(rp/'animations'/f'{name}_{alias}.animation.json',animation)
            description['animations'][alias]=next(iter(animation['animations']))
            description['scripts']['animate'].append({alias:condition})
    write(rp/'entity'/f'{name}.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{'description':description}})
    write(rp/'render_controllers'/f'{name}.json',{'format_version':'1.8.0','render_controllers':{
        f'controller.render.{folder.name}.{name}':{'geometry':'Geometry.default','materials':[{'*':'Material.default'}],
                                               'textures':['Texture.default']}}})
    hostile = kind != 'atlatitan'
    components = {'minecraft:type_family':{'family':['minizin_creature',folder.name,'mob']},
        'minecraft:health':{'value':200 if kind in ('dragon','boss') else 40,'max':200 if kind in ('dragon','boss') else 40},
        'minecraft:collision_box':{'width':2 if kind in ('dragon','boss','atlatitan') else 1,'height':3 if kind!='bluff' else 1.5},
        'minecraft:physics':{},'minecraft:pushable':{'is_pushable':True,'is_pushable_by_piston':True},
        'minecraft:movement':{'value':0.2},'minecraft:movement.basic':{},'minecraft:navigation.walk':{'can_path_over_water':True},
        'minecraft:behavior.random_stroll':{'priority':7,'speed_multiplier':0.7},
        'minecraft:behavior.look_at_player':{'priority':8,'look_distance':12},
        'minecraft:behavior.hurt_by_target':{'priority':1}}
    if hostile:
        components['minecraft:behavior.nearest_attackable_target']={'priority':2,'must_see':True,
            'entity_types':[{'filters':{'test':'is_family','subject':'other','value':'player'},'max_dist':24}]}
    components['minecraft:attack']={'damage':6}
    components['minecraft:behavior.melee_attack']={'priority':3,'speed_multiplier':1.2,'track_target':True}
    groups, events = {}, {}
    if kind=='dragon':
        # Each slot is a synchronized ordinal. The texture overlays come from
        # EnumDragonTextures.Armor in the pinned Ice and Fire source.
        armor_path = texture.parent
        transparent = ROOT/'mods/16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/textures/models/firedragon/empty.png'
        copy_asset(transparent,rp/'textures/entity'/f'{name}_armor_empty.png',report)
        for slot in DRAGON_ARMOR_SLOTS:
            description['textures'][f'armor_{slot}_0']=f'textures/entity/{name}_armor_empty'
            for ordinal in range(1,9):
                image=f'armor_{slot}_{ordinal}.png'
                copy_asset(armor_path/image,rp/'textures/entity'/f'{name}_{image}',report)
                description['textures'][f'armor_{slot}_{ordinal}']=f'textures/entity/{name}_armor_{slot}_{ordinal}'
        description['materials']['default']='entity_multitexture'
        controller_path=rp/'render_controllers'/f'{name}.json'
        controller=json.loads(controller_path.read_text())
        renderer=controller['render_controllers'][f'controller.render.{folder.name}.{name}']
        arrays=renderer.setdefault('arrays',{}).setdefault('textures',{})
        for slot in DRAGON_ARMOR_SLOTS:
            arrays[f'Array.armor_{slot}']=[f'Texture.armor_{slot}_{n}' for n in range(9)]
            renderer['textures'].append(f"Array.armor_{slot}[query.property('minizin:armor_{slot}')]" )
        write(controller_path,controller)
        write(rp/'entity'/f'{name}.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{'description':description}})
        components['minecraft:rideable']={'seat_count':1,'family_types':['player'],
            'interact_text':'action.interact.mount','seats':[{'position':[0,1.4,0]}]}
        groups['minizin:flight']={'minecraft:physics':{'has_gravity':False},'minecraft:movement.fly':{},
            'minecraft:navigation.fly':{'can_path_over_water':True}}
        groups['minizin:ground']={'minecraft:physics':{'has_gravity':True},'minecraft:movement.basic':{},'minecraft:navigation.walk':{}}
        events={'minizin:takeoff':{'remove':{'component_groups':['minizin:ground']},'add':{'component_groups':['minizin:flight']}},
                'minizin:land':{'remove':{'component_groups':['minizin:flight']},'add':{'component_groups':['minizin:ground']}}}
        for rating in range(1,17):
            key=f'minizin:dragon_armor_{rating}'
            groups[key]={'minecraft:armor':{'value':rating}}
            events[key]={'remove':{'component_groups':[f'minizin:dragon_armor_{n}' for n in range(1,17) if n!=rating]},
                         'add':{'component_groups':[key]}}
        events['minizin:dragon_armor_0']={'remove':{'component_groups':[f'minizin:dragon_armor_{n}' for n in range(1,17)]}}
    if kind=='boss':
        components['minecraft:boss']={'name':name.replace('_',' ').title(),'hud_range':48,'should_darken_sky':False}
    write(bp/'entities'/f'{name}.json',{'format_version':'1.21.0','minecraft:entity':{
        'description':{'identifier':ident,'is_spawnable':True,'is_summonable':True,'is_experimental':False,
            'properties':{**{f'minizin:{p}':{'type':'bool','default':False,'client_sync':True} for p in ['flying','attacking','enraged']},
                **({f'minizin:armor_{slot}':{'type':'int','range':[0,8],'default':0,'client_sync':True}
                    for slot in DRAGON_ARMOR_SLOTS} if kind=='dragon' else {})}},
        'components':components,'component_groups':groups,'events':events}})
    sound_id = None
    if sound:
        copy_asset(sound,rp/'sounds'/f'{name}.ogg',report)
        sound_id = f'minizin.{folder.name}.{name}.attack'
    return ident, {'kind':kind,'element':element,'sound':sound_id}


def add_dragon_egg(folder, kind, texture, report):
    """Add a placeable incubation entity for the current Ice and Fire IDs."""
    rp,bp=folder/'RP',folder/'BP'
    name=f'{kind}_dragon_egg'
    ident=f'minizin_{folder.name}:{name}'
    geometry_id=f'geometry.minizin_{folder.name}.{name}'
    geometry={'format_version':'1.12.0','minecraft:geometry':[{
        'description':{'identifier':geometry_id,'texture_width':64,'texture_height':64,
                       'visible_bounds_width':1.5,'visible_bounds_height':1.5,
                       'visible_bounds_offset':[0,0.7,0]},
        'bones':[{'name':'egg','pivot':[0,0,0],'cubes':[{'origin':[-5,0,-5],
            'size':[10,14,10],'uv':{'north':{'uv':[0,0],'uv_size':[10,14]},
            'south':{'uv':[0,0],'uv_size':[10,14]},'east':{'uv':[0,0],'uv_size':[10,14]},
            'west':{'uv':[0,0],'uv_size':[10,14]},'up':{'uv':[10,0],'uv_size':[10,10]},
            'down':{'uv':[10,0],'uv_size':[10,10]}}}]}]
    }]}
    write(rp/'models/entity'/f'{name}.geo.json',geometry)
    copy_asset(texture,rp/'textures/entity'/f'{name}.png',report)
    write(rp/'entity'/f'{name}.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{
        'description':{'identifier':ident,'materials':{'default':'entity_alphatest'},
          'textures':{'default':f'textures/entity/{name}'},'geometry':{'default':geometry_id},
          'render_controllers':[f'controller.render.{folder.name}.{name}']}}})
    write(rp/'render_controllers'/f'{name}.json',{'format_version':'1.8.0','render_controllers':{
        f'controller.render.{folder.name}.{name}':{'geometry':'Geometry.default',
          'materials':[{'*':'Material.default'}],'textures':['Texture.default']}}})
    write(bp/'entities'/f'{name}.json',{'format_version':'1.21.0','minecraft:entity':{
        'description':{'identifier':ident,'is_spawnable':False,'is_summonable':False,'is_experimental':False},
        'components':{'minecraft:type_family':{'family':['minizin_dragon_egg']},
          'minecraft:health':{'value':1,'max':1},'minecraft:collision_box':{'width':0.7,'height':0.9},
          'minecraft:physics':{'has_gravity':False},'minecraft:pushable':{'is_pushable':False,
          'is_pushable_by_piston':False}}}})
    return ident


def dragon_clips(family, rest):
    folder=CONVERSIONS/'ice_and_fire'/family
    result=[]
    for alias, suffix, duration, condition in [
        ('walk','Walk',1.2,"!query.property('minizin:flying') && query.modified_move_speed > 0.01 && !query.property('minizin:attacking')"),
        ('flight','Flight',1.0,"query.property('minizin:flying') && !query.property('minizin:attacking')"),
        ('bite','Bite',0.3,"query.property('minizin:attacking')")]:
        poses=[load_geometry(p) for p in sorted(folder.glob(f'{family}_{suffix}[0-9]*.geo.json'))]
        if not poses: raise ValueError(f'Missing original poses for {family}/{suffix}')
        result.append((alias,convert(rest,poses,f'animation.minizin.{family}.{alias}',duration,True),condition))
    return result


def blocks_pack(folder, namespace, report):
    rp,bp=folder/'RP',folder/'BP'
    terrain={}
    count=0
    for geo in sorted((CONVERSIONS/'block_atlases'/namespace).glob('*.geo.json')):
        texture=geo.with_suffix('').with_suffix('.png')
        if not texture.exists(): raise ValueError(f'Missing original atlas: {geo}')
        name=geo.name.removesuffix('.geo.json')
        geometry=load_geometry(geo)
        gid='geometry.minizin_'+namespace+'.'+name
        geometry['description']['identifier']=gid
        report.append({'source':str(geo.relative_to(ROOT)),'strategy':'CONVERT','block':'minizin_'+namespace+':'+name,
            'sha256':hashlib.sha256(geo.read_bytes()).hexdigest()})
        write(rp/'models/blocks'/geo.name,{'format_version':'1.12.0','minecraft:geometry':[geometry]})
        copy_asset(texture,rp/'textures/blocks'/texture.name,report)
        terrain[name]={'textures':'textures/blocks/'+texture.stem}
        ident='minizin_'+namespace+':'+name
        write(bp/'blocks'/f'{name}.json',{'format_version':'1.21.90','minecraft:block':{
            'description':{'identifier':ident,'menu_category':{'category':'construction'}},
            'components':{'minecraft:geometry':{'identifier':gid},
                'minecraft:material_instances':{'*':{'texture':name,'render_method':'alpha_test'}},
                'minecraft:destructible_by_mining':{'seconds_to_destroy':1.5},
                'minecraft:destructible_by_explosion':{'explosion_resistance':3},
                'minecraft:loot':f'loot_tables/blocks/{name}.json'}}})
        write(bp/'loot_tables/blocks'/f'{name}.json',{'pools':[{'rolls':1,'entries':[{'type':'item','name':ident,'weight':1}]}]})
        count+=1
    write(rp/'textures/terrain_texture.json',{'resource_pack_name':'Minizin '+namespace,'texture_name':'atlas.terrain',
        'padding':8,'num_mip_levels':4,'texture_data':terrain})
    return count


def build(output):
    if output.exists(): raise ValueError('Output already exists; use a new directory to preserve before/after')
    report=[]; results={}
    specs={
        'iceandfire':('16-ice-and-fire','iceandfire'),
        'cataclysm':('43-cataclysm','cataclysm'),
        'alexscaves':('42-alexs-caves','alexscaves'),
        'mowzies':('44-mowzies-mobs','mowziesmobs')}
    for mod,(source_name,namespace) in specs.items():
        folder=output/mod; manifests(folder,mod,True)
        assets=ROOT/'mods'/source_name/'upstream/src/main/resources/assets'/namespace
        catalog={}
        if mod=='iceandfire':
            for family,color,element in [('firedragon','red','fire'),('icedragon','blue','ice'),('lightningdragon','electric','lightning')]:
                geo=CONVERSIONS/'ice_and_fire'/family/f'{family}_Ground.geo.json'
                tex=assets/'textures/models'/family/f'{color}_1.png'
                sound=assets/'sounds/mobs/dragon'/element/'breath.ogg'
                ident,spec=add_entity(folder,family,geo,tex,'dragon',report,
                    dragon_clips(family,load_geometry(geo)),sound,element)
                catalog[ident]=spec
                for pose in sorted((CONVERSIONS/'ice_and_fire'/family).glob(f'{family}_*.geo.json')):
                    if any(f'_{clip}' in pose.name for clip in ['Walk','Flight','Bite']):
                        report.append({'source':str(pose.relative_to(ROOT)),'strategy':'CONVERT',
                            'use':'animation_keyframe','sha256':hashlib.sha256(pose.read_bytes()).hexdigest()})
                egg_texture=assets/'textures/models'/family/({'firedragon':'egg_red.png','icedragon':'egg_blue.png',
                    'lightningdragon':'egg_black.png'}[family])
                add_dragon_egg(folder,element,egg_texture,report)
        elif mod=='cataclysm':
            for name,model,tex in [('ender_guardian','Ender_Guardian_Model','ender_guardian.png'),
                ('ignis','Ignis_Model','ignis/ignis_idle_0.png'),('harbinger','The_Harbinger_Model','harbinger/the_harbinger.png')]:
                attack_sound={'ender_guardian':'ender_guardian_fist_attack.ogg','ignis':'ignis_impact.ogg','harbinger':'harbinger_laser.ogg'}[name]
                ident,spec=add_entity(folder,name,CONVERSIONS/'cataclysm'/f'{model}.geo.json',
                    assets/'textures/entity'/tex,'boss',report,sound=assets/'sounds/entity'/attack_sound)
                catalog[ident]=spec
        elif mod=='alexscaves':
            ident,spec=add_entity(folder,'atlatitan',CONVERSIONS/'alex_caves/atlatitan.geo.json',
                assets/'textures/entity/atlatitan.png','atlatitan',report,sound=assets/'sounds/mob/atlatitan/atlatitan_stomp_0.ogg')
            catalog[ident]=spec
        else:
            geo=assets/'geo/bluff.geo.json'; original=json.loads((assets/'animations/bluff.animation.json').read_text())
            # Wire only clips without unsupported Java/GeckoLib expressions.
            clips=[]
            for key,anim in original['animations'].items():
                if key.endswith('idle'):
                    serialized=json.dumps(anim)
                    if any(word in serialized for word in ['math.random','query.anim_time','query.life_time']):
                        pass  # these are native Molang functions, retained verbatim
                    if 'variable.' in serialized: continue
                    key='animation.minizin.bluff.'+key
                    clips.append(('idle',{'format_version':'1.8.0','animations':{key:adapt_gecko(anim)}},'1.0'))
            ident,spec=add_entity(folder,'bluff',geo,assets/'textures/entity/bluff.png','bluff',report,clips,
                assets/'sounds/entity/bluff/spike_explode.ogg')
            catalog[ident]=spec
        scripts=folder/'BP/scripts';scripts.mkdir(parents=True,exist_ok=True)
        for source,dest in [('creatures.js','main.js'),('combat.mjs','combat.js'),('dragon_armor.js','dragon_armor.js')]:
            shutil.copy2(ROOT/'bedrock/runtime'/source,scripts/dest)
        (scripts/'creature_catalog.js').write_text('export const CREATURES = '+json.dumps(catalog)+';\n')
        sounds={s['sound']:{'category':'hostile','sounds':['sounds/'+i.split(':')[1]]} for i,s in catalog.items() if s['sound']}
        if sounds:write(folder/'RP/sounds/sound_definitions.json',{'format_version':'1.14.0','sound_definitions':sounds})
        results[mod]={'entities':len(catalog),'blocks':0,'identifiers':list(catalog)}
    for mod in ['aether','biomesoplenty']:
        folder=output/mod;manifests(folder,mod,False)
        results[mod]={'entities':0,'blocks':blocks_pack(folder,mod,report)}
    for mod in results:
        folder=output/mod
        validate(folder)
        with zipfile.ZipFile(output/f'Minizin_{mod}_Gameplay_Experimental.mcaddon','w',zipfile.ZIP_STORED) as archive:
            for role in ['RP','BP']:archive.writestr(f'{mod}_{role}.mcpack',zipped(folder/role))
    commits={m:subprocess.check_output(['git','-C',str(ROOT/'mods'/m/'upstream'),'rev-parse','HEAD'],text=True).strip() for m in
        [*(m for m,_ in specs.values()),'41-the-aether','19-biomes-o-plenty']}
    write(output/'REPORT.json',{'results':results,'upstream_commits':commits,'assets':report,
        'android_tested':False,'limitations':['Not complete ports','Cataclysm/Atlatitan skeletal animation not ported',
        'Block variants are separately placeable; no worldgen/dimensions','Dragon pose timing adapted; rig visual QA pending',
        'Only selected entities; no full boss attack repertoire','Origins/MCA/RFTools runtime remains separate backlog']})
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output.resolve())
