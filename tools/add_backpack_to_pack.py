#!/usr/bin/env python3
"""Add privately adapted original Sophisticated Backpack mesh and personal storage."""
import argparse,json,shutil,hashlib,subprocess,zipfile
from pathlib import Path
from PIL import Image,ImageDraw
from block_atlas_to_bedrock import convert
from build_bedrock_packs import zipped
from validate_gameplay_packs import check

ROOT=Path(__file__).resolve().parents[1]
NS='sophisticatedbackpacks'


def add(source,upstream,output):
    if output.exists():raise ValueError('Fresh output required')
    shutil.copytree(source,output)
    for p in output.glob('*.mcaddon'):p.unlink()
    rp,bp=output/'RP',output/'BP'
    stage=output/'source_reference';assets=upstream/'src/main/resources/assets'/NS
    target=stage/'src/main/resources/assets'/NS
    # All static pieces share source model coordinates; collapse into a single
    # source model before conversion, avoiding the atlas converter's part offsets.
    pieces=['backpack_base','backpack_front_pouch','backpack_left_pouch','backpack_right_pouch','backpack_straps']
    textures={};elements=[];provenance=[]
    (target/'textures').mkdir(parents=True,exist_ok=True);shutil.copytree(assets/'textures',target/'textures',dirs_exist_ok=True)
    for name in pieces:
        path=assets/'models/block'/f'{name}.json';doc=json.loads(path.read_text())
        provenance.append({'path':str(path.relative_to(upstream)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        for key,value in doc.get('textures',{}).items():textures[name+'_'+key]=value
        for element in doc.get('elements',[]):
            for face in element['faces'].values():
                if face['texture'].startswith('#'):face['texture']='#'+name+'_'+face['texture'][1:]
            elements.append(element)
    merged=target/'models/block/merged_backpack.json';merged.parent.mkdir(parents=True,exist_ok=True)
    merged.write_text(json.dumps({'textures':textures,'elements':elements}))
    # Apply the exact original default tints to original grayscale texture pixels.
    for filename,tint in [('backpack_cloth.png',(204,97,58)),('backpack_border.png',(98,46,26))]:
        path=target/'textures/block'/filename;image=Image.open(path).convert('RGBA')
        image.putdata([(round(r*tint[0]/255),round(g*tint[1]/255),round(b*tint[2]/255),a) for r,g,b,a in image.getdata()]);image.save(path)
    geometry,atlas,issues=convert(stage,NS,['block/merged_backpack'],'geometry.minizin.backpack')
    model=rp/'models/entity/backpack.geo.json';model.parent.mkdir(parents=True,exist_ok=True);model.write_text(json.dumps(geometry,indent=2))
    texture=rp/'textures/entity/backpack.png';texture.parent.mkdir(parents=True,exist_ok=True);atlas.save(texture)
    # Orthographic front icon assembled from the actual front-facing source UVs.
    # No generic replacement art; original textured cuboids remain in the model.
    icon=Image.new('RGBA',(128,128));geo=geometry['minecraft:geometry'][0]
    cubes=[c for b in geo['bones'] for c in b.get('cubes',[]) if 'north' in c.get('uv',{})]
    for cube in sorted(cubes,key=lambda c:c['origin'][2],reverse=True):
        x,y,z=cube['origin'];w,h,d=cube['size'];face=cube['uv']['north'];u,v=face['uv'];uw,vh=face['uv_size']
        patch=atlas.crop((u,v,u+uw,v+vh)).resize((max(1,round(w*7)),max(1,round(h*7))),Image.Resampling.NEAREST)
        icon.alpha_composite(patch,(round(64+x*7),round(116-(y+h)*7)))
    if icon.getchannel('A').getbbox() is None:raise ValueError('Backpack original mesh icon empty')
    itemtex=rp/'textures/items/backpack.png';itemtex.parent.mkdir(parents=True,exist_ok=True);icon.save(itemtex)
    registry=rp/'textures/item_texture.json';doc=json.loads(registry.read_text());doc['texture_data']['minizin_backpack']={'textures':'textures/items/backpack'};registry.write_text(json.dumps(doc,indent=2))
    for name,original in [('filter_upgrade','filter_upgrade'),('expansion_upgrade','upgrade_base')]:
        shutil.copy2(assets/'textures/item'/f'{original}.png',rp/'textures/items'/f'backpack_{name}.png')
        doc['texture_data'][f'minizin_backpack_{name}']={'textures':f'textures/items/backpack_{name}'}
    registry.write_text(json.dumps(doc,indent=2))
    definition={'format_version':'1.21.90','minecraft:item':{'description':{'identifier':'minizin:backpack','menu_category':{'category':'items'}},
        'components':{'minecraft:icon':{'textures':{'default':'minizin_backpack'}},'minecraft:max_stack_size':1,
            'minecraft:display_name':{'value':'item.minizin:backpack.name'}}}}
    item=bp/'items/backpack.json';item.parent.mkdir(parents=True,exist_ok=True);item.write_text(json.dumps(definition,indent=2))
    recipe=bp/'recipes/backpack.json';recipe.parent.mkdir(parents=True,exist_ok=True)
    recipe.write_text(json.dumps({'format_version':'1.12','minecraft:recipe_shaped':{'description':{'identifier':'minizin:backpack'},
      'tags':['crafting_table'],'pattern':['LSL','LCL','LLL'],'key':{'L':{'item':'minecraft:leather'},'S':{'item':'minecraft:string'},'C':{'item':'minecraft:chest'}},'result':{'item':'minizin:backpack','count':1}}},indent=2))
    for language,title in [('pt_BR','Mochila — 27 espaços pessoais'),('en_US','Backpack — 27 personal slots')]:
        with (rp/'texts'/f'{language}.lang').open('a') as f:f.write('item.minizin:backpack.name='+title+'\n')
    # The old per-player runtime silently discards independent bag identity
    # and the filter/sort/deposit upgrades. Keep the audited item-bound pack
    # implementation that is already present in the systems workstream.
    shutil.copy2(ROOT/'bedrock/packs/sophisticated_backpacks/BP/scripts/main.js',
                 bp/'scripts/backpack.js')
    for name in ('filter_upgrade.json','expansion_upgrade.json'):
        shutil.copy2(ROOT/'bedrock/packs/sophisticated_backpacks/BP/items'/name,
                     bp/'items'/name)
        shutil.copy2(ROOT/'bedrock/packs/sophisticated_backpacks/BP/recipes'/name,
                     bp/'recipes'/name)
        item_path=bp/'items'/name
        item_def=json.loads(item_path.read_text())
        item_def['minecraft:item']['components']['minecraft:icon']={
            'textures':{'default':'minizin_backpack_'+name.removesuffix('.json')}}
        item_path.write_text(json.dumps(item_def,indent=2))
    with (bp/'scripts/main.js').open('a') as f:f.write('\nimport "./backpack.js";\n')
    for role in ['RP','BP']:
        path=output/role/'manifest.json';doc=json.loads(path.read_text());doc['header']['version']=[0,2,3]
        doc['header']['name']='Minizin Correção + Mochila '+role
        for module in doc['modules']:module['version']=[0,2,3]
        for dep in doc.get('dependencies',[]):
            if 'uuid' in dep:dep['version']=[0,2,3]
        path.write_text(json.dumps(doc,indent=2))
    counts=check([output]);commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
    shutil.copy2(upstream/'LICENSE.md',output/'SOPHISTICATED_BACKPACKS_LICENSE.md')
    (output/'BACKPACK_REPORT.json').write_text(json.dumps({'upstream':'https://github.com/P3pp3rF1y/SophisticatedBackpacks','commit':commit,
        'provenance':provenance,'issues':issues,'capacity':27,'storage':'persistent per-backpack item identity (v2)',
        'limits':['Filter/sort/deposit present; other Java upgrades, wearable attachment and native menu remain pending',
                  'Containers cannot be nested','Inventory transfer crash consistency not Android-tested'],
        'android_retest_pending':True,'structural':counts},indent=2))
    addon=output/'Minizin_Todos_Juntos_Correcao_e_Mochila_v0.2.3.mcaddon'
    with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as archive:
        for role in ['RP','BP']:archive.writestr('Minizin_Mobile_'+role+'.mcpack',zipped(output/role))
    assert zipfile.ZipFile(addon).testzip() is None
    print(json.dumps({'file':str(addon),'validation':counts,'backpack_cubes':len(cubes)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('upstream',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();add(args.source,args.upstream,args.output)
