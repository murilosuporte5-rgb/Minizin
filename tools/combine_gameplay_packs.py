#!/usr/bin/env python3
"""Combine independent staged packs without overwriting resources or scripts."""
import argparse,json,shutil,uuid,zipfile
from pathlib import Path
from build_bedrock_packs import zipped,validate
from validate_gameplay_packs import check


def combine(folders,output):
    if output.exists():raise ValueError('Choose a fresh output folder')
    registries={};catalog={};imports=[];report=[]
    for folder in folders:
        mod=folder.name;report.append(mod)
        terrain_path=folder/'RP/textures/terrain_texture.json'
        terrain=json.loads(terrain_path.read_text()).get('texture_data',{}) if terrain_path.exists() else {}
        def rewrite(value):
            if isinstance(value,list):return [rewrite(v) for v in value]
            if isinstance(value,dict):return {k:rewrite(v) for k,v in value.items()}
            if isinstance(value,str):
                for role in ['RP','BP']:
                    base=folder/role
                    if any((base/(value+suffix)).is_file() for suffix in ['', '.png','.ogg']):
                        parts=value.split('/',1)
                        if len(parts)==2:return parts[0]+'/'+mod+'/'+parts[1]
            return value
        for role in ['RP','BP']:
            for path in sorted((folder/role).rglob('*')):
                if not path.is_file():continue
                rel=path.relative_to(folder/role)
                if rel.as_posix()=='manifest.json':continue
                if rel.parts[0]=='scripts':continue
                target=output/role/rel.parts[0]/mod/Path(*rel.parts[1:])
                target.parent.mkdir(parents=True,exist_ok=True)
                if path.suffix!='.json':shutil.copy2(path,target);continue
                doc=rewrite(json.loads(path.read_text()))
                registry_key=next((k for k in ['texture_data','sound_definitions'] if k in doc),None)
                if registry_key:
                    canonical=output/role/rel
                    data=doc[registry_key]
                    if rel.name=='terrain_texture.json':data={mod+'_'+k:v for k,v in data.items()}
                    if canonical not in registries:registries[canonical]={**doc,registry_key:{}}
                    merged=registries[canonical][registry_key]
                    for key,value in data.items():
                        if key in merged and merged[key]!=value:raise ValueError('Registry conflict '+key)
                        merged[key]=value
                    continue
                block=doc.get('minecraft:block')
                if block:
                    for material in block.get('components',{}).get('minecraft:material_instances',{}).values():
                        if material.get('texture') in terrain:material['texture']=mod+'_'+material['texture']
                target.write_text(json.dumps(doc,indent=2))
        scripts=folder/'BP/scripts'
        if (scripts/'creature_catalog.js').exists():
            raw=(scripts/'creature_catalog.js').read_text().split('=',1)[1].strip().removesuffix(';')
            catalog.update(json.loads(raw))
        elif (scripts/'main.js').exists():
            shutil.copytree(scripts,output/'BP/scripts'/mod)
            imports.append(f'import "./{mod}/main.js";')
    for path,doc in registries.items():
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(doc,indent=2))
    scripts=output/'BP/scripts';scripts.mkdir(parents=True,exist_ok=True)
    if catalog:
        source=next(f/'BP/scripts' for f in folders if (f/'BP/scripts/creature_catalog.js').exists())
        for name in ['main.js','combat.js']:shutil.copy2(source/name,scripts/('creatures.js' if name=='main.js' else name))
        (scripts/'creature_catalog.js').write_text('export const CREATURES = '+json.dumps(catalog)+';\n')
        imports.insert(0,'import "./creatures.js";')
    (scripts/'main.js').write_text('\n'.join(imports)+'\n')
    rp_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'minizin/all-gameplay/rp/v1'))
    for role,kind in [('RP','resources'),('BP','data')]:
        header_uuid=rp_uuid if role=='RP' else str(uuid.uuid5(uuid.NAMESPACE_URL,'minizin/all-gameplay/bp/v1'))
        doc={'format_version':2,'header':{'name':'Minizin Todos Juntos '+role,'description':'10 mods em um pacote experimental; gameplay parcial',
            'uuid':header_uuid,'version':[0,2,1],'min_engine_version':[1,21,90]},'modules':[{'type':kind,
                'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'minizin/all-gameplay/'+role+'/module')),'version':[0,2,1]}]}
        if role=='BP':
            doc['modules'].append({'type':'script','language':'javascript','entry':'scripts/main.js',
                'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'minizin/all-gameplay/script')),'version':[0,2,1]})
            doc['dependencies']=[{'uuid':rp_uuid,'version':[0,2,1]},
                {'module_name':'@minecraft/server','version':'2.0.0'},{'module_name':'@minecraft/server-ui','version':'2.0.0'}]
        (output/role/'manifest.json').write_text(json.dumps(doc,indent=2))
    validate(output)
    counts=check([output])
    (output/'REPORT.json').write_text(json.dumps({'mods':report,'validation':counts,'android_tested':False},indent=2))
    addon=output/'Minizin_Todos_Juntos_Experimental.mcaddon'
    with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
        for role in ['RP','BP']:archive.writestr('Minizin_Todos_'+role+'.mcpack',zipped(output/role))
    assert zipfile.ZipFile(addon).testzip() is None
    print(json.dumps({'file':str(addon),'validation':counts}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('folders',type=Path,nargs='+')
    args=ap.parse_args();combine(args.folders,args.output)
