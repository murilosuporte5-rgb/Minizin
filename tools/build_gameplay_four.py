#!/usr/bin/env python3
"""Extend the four standalone packs, preserving generated original resources."""
import argparse,json,shutil,zipfile
from pathlib import Path
from split_next_four_packs import build_one,pack,validate_bundle
from build_bedrock_packs import validate

ROOT=Path(__file__).resolve().parents[1]


def build(output):
    if output.exists():raise ValueError('Choose a new output directory; previous build preserved')
    stage=output/'source_snapshot'
    shutil.copytree(ROOT/'generated/next_four',stage)
    for name in ['origins.js','mca.js','carryon.js','rftools.js']:
        shutil.copy2(ROOT/'bedrock/packs/next_four/BP/scripts'/name,stage/'BP/scripts'/name)
    for mod in ['mca','carryon','origins','rftools']:
        build_one(mod,stage,output)
        main=output/mod/'BP/scripts/main.js'
        main.write_text(main.read_text().replace('world.beforeEvents.chatSend.subscribe(',
            'world.beforeEvents.chatSend?.subscribe('))
    folder=output/'rftools';rp,bp=folder/'RP',folder/'BP'
    terrain={}
    machine_blocks=[
        ('machine_frame', 'geometry.minizin.rftools.machine_frame'),
        ('coalgenerator', 'geometry.minizin.rftools.coalgenerator'),
        ('powercell', 'geometry.minizin.rftools.powercell'),
        ('powercell_simple', 'geometry.minizin.rftools.powercell_simple'),
        ('powercell_advanced', 'geometry.minizin.rftools.powercell_advanced'),
        ('powercell_creative', 'geometry.minizin.rftools.powercell_creative'),
    ]
    for name,geometry in machine_blocks:
        texture='textures/entity/minizin/rftools_'+name
        terrain[name]={'textures':texture}
        doc={'format_version':'1.21.90','minecraft:block':{
            'description':{'identifier':'minizin_rftools:'+name,'menu_category':{'category':'construction'}},
            'components':{'minecraft:geometry':{'identifier':geometry},
                'minecraft:material_instances':{'*':{'texture':name,'render_method':'opaque'}},
                'minecraft:destructible_by_mining':{'seconds_to_destroy':3},
                'minecraft:loot':'loot_tables/blocks/'+name+'.json'}}}
        (bp/'blocks').mkdir(exist_ok=True)
        (bp/'blocks'/f'{name}.json').write_text(json.dumps(doc,indent=2))
        (bp/'loot_tables/blocks').mkdir(parents=True,exist_ok=True)
        (bp/'loot_tables/blocks'/f'{name}.json').write_text(json.dumps({'pools':[{'rolls':1,'entries':[
            {'type':'item','name':'minizin_rftools:'+name,'weight':1}]}]}))
    recipes={
      'machine_frame':{
        'pattern':['ili','g g','ili'],
        'key':{'i':{'item':'minecraft:iron_ingot'},'l':{'item':'minecraft:lapis_lazuli'},'g':{'item':'minecraft:gold_nugget'}},
        'result':'minizin_rftools:machine_frame'},
      'infused_diamond':{
        'pattern':['sss','sds','sss'],
        'key':{'s':{'item':'minizin:rftools_items_dimensionalsharditem'},'d':{'item':'minecraft:diamond'}},
        'result':'minizin:rftools_items_infuseddiamond'},
      'coalgenerator':{
        'pattern':['cTc','cMc','cTc'],
        'key':{'c':{'item':'minecraft:coal'},'T':{'item':'minecraft:redstone_torch'},'M':{'item':'minizin_rftools:machine_frame'}},
        'result':'minizin_rftools:coalgenerator'},
      'powercell_simple':{
        'pattern':['rdr','bMb','rdr'],
        'key':{'r':{'item':'minecraft:redstone_block'},'d':{'item':'minecraft:diamond'},'b':{'item':'minecraft:quartz'},'M':{'item':'minizin_rftools:machine_frame'}},
        'result':'minizin_rftools:powercell_simple'},
      'powercell':{
        'pattern':['rdr','bMb','rer'],
        'key':{'r':{'item':'minecraft:redstone_block'},'d':{'item':'minecraft:diamond'},'b':{'item':'minecraft:prismarine_shard'},'e':{'item':'minecraft:emerald'},'M':{'item':'minizin_rftools:machine_frame'}},
        'result':'minizin_rftools:powercell'},
      'powercell_advanced':{
        'pattern':['rir','iMi','rir'],
        'key':{'r':{'item':'minecraft:redstone_block'},'i':{'item':'minizin:rftools_items_infuseddiamond'},'M':{'item':'minizin_rftools:powercell'}},
        'result':'minizin_rftools:powercell_advanced'}
    }
    (bp/'recipes').mkdir(exist_ok=True)
    for name,spec in recipes.items():
        (bp/'recipes'/f'{name}.json').write_text(json.dumps({
          'format_version':'1.20.10','minecraft:recipe_shaped':{
            'description':{'identifier':'minizin_rftools:'+name},
            'tags':['crafting_table'],'pattern':spec['pattern'],'key':spec['key'],
            'result':{'item':spec['result'],'count':1}}},indent=2))
    (rp/'textures/terrain_texture.json').write_text(json.dumps({'resource_pack_name':'Minizin RFTools',
        'texture_name':'atlas.terrain','padding':8,'num_mip_levels':4,'texture_data':terrain},indent=2))
    shutil.copy2(ROOT/'bedrock/runtime/rftools_machines.js',bp/'scripts/rftools_machines.js')
    with (bp/'scripts/main.js').open('a') as file:file.write('\nimport "./rftools_machines.js";\n')
    for mod in ['mca','carryon','origins','rftools']:
        folder=output/mod
        for role in ['RP','BP']:
            path=folder/role/'manifest.json';doc=json.loads(path.read_text())
            doc['header']['version']=[0,2,0];doc['header']['min_engine_version']=[1,21,90]
            for module in doc['modules']:module['version']=[0,2,0]
            for dependency in doc.get('dependencies',[]):
                if 'uuid' in dependency:dependency['version']=[0,2,0]
            path.write_text(json.dumps(doc,indent=2))
        validate(folder)
        addon=folder/f'Minizin_{mod}_Standalone_Prototype.mcaddon'
        with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
            for role in ['BP','RP']:archive.writestr(f'Minizin_{mod}_{role}.mcpack',pack(folder/role))
        validate_bundle(addon,mod)
    print('Four independent packs extended. No Android game test performed.')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    build(ap.parse_args().output.resolve())
