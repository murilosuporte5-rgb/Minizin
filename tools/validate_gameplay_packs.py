#!/usr/bin/env python3
"""Cross-pack reference and JavaScript parse gate, independent of Minecraft QA."""
import argparse,json,re,subprocess,uuid
from pathlib import Path
from build_bedrock_packs import validate


def check(folders):
    builtin_item_icons={'chest','hopper'}
    uuids=set();identifiers=set();counts={'packs':0,'entities':0,'blocks':0,'scripts':0,'animations':0,'sounds':0}
    for folder in folders:
        rp,bp,n=validate(folder);counts['packs']+=1;counts['entities']+=n
        geometries={
            # These are supplied by Bedrock itself and need not be packaged
            # as custom geometry files.
            'minecraft:geometry.full_block': {},
            'geometry.cow.v2': {},
            'geometry.pig.v3': {},
            'geometry.humanoid': {},
            'geometry.humanoid.custom': {},
            'geometry.player': {},
            'geometry.zombie': {},
            'geometry.skeleton': {},
        }
        for path in rp.rglob('*.geo.json'):
            rel=path.relative_to(rp).parts
            if len(rel)<3 or rel[0]!='models' or rel[1] not in ['entity','blocks']:
                raise ValueError('Geometry outside loader directory: '+str(path))
            for geo in json.loads(path.read_text(encoding='utf-8')).get('minecraft:geometry',[]):
                geometries[geo['description']['identifier']]=geo
        item_registry=rp/'textures/item_texture.json'
        item_identifiers=set()
        if item_registry.exists():
            icons=json.loads(item_registry.read_text(encoding='utf-8'))['texture_data']
            for item_path in (bp/'items').rglob('*.json'):
                item=json.loads(item_path.read_text(encoding='utf-8'))['minecraft:item']
                ident=item['description']['identifier']
                if ident in item_identifiers:
                    raise ValueError('Item identifier conflict: '+ident)
                item_identifiers.add(ident)
                icon=item.get('components',{}).get('minecraft:icon')
                ref=icon if isinstance(icon,str) else icon.get('textures',{}).get('default') if icon else None
                if ref not in icons:
                    if ref in builtin_item_icons:continue
                    raise ValueError('Item icon missing from registry: '+str(ref))
                path=icons[ref]['textures']
                if not isinstance(path,str) or not (rp/(path+'.png')).exists():raise ValueError('Item PNG missing: '+str(path))
        for role in ['RP','BP']:
            manifest=json.loads((folder/role/'manifest.json').read_text(encoding='utf-8'))
            for key in [manifest['header']['uuid'],*[m['uuid'] for m in manifest['modules']]]:
                uuid.UUID(key)
                if key in uuids:raise ValueError('Cross-pack UUID conflict: '+key)
                uuids.add(key)
        expected=json.loads((rp/'manifest.json').read_text(encoding='utf-8'))['header']['uuid']
        if not any(d.get('uuid')==expected for d in json.loads((bp/'manifest.json').read_text(encoding='utf-8')).get('dependencies',[])):
            raise ValueError('Broken RP dependency')
        for path in (bp/'scripts').rglob('*'):
            if path.suffix not in ['.js','.mjs']:continue
            source=path.read_text(encoding='utf-8')
            subprocess.run(['node','--input-type=module','--check'],input=source,text=True,
                           encoding='utf-8',check=True,capture_output=True)
            counts['scripts']+=1
            for ref in re.findall(r'(?:from\s*|import\s*)["\'](\.[^"\']+)["\']',source):
                if not (path.parent/ref).is_file():raise ValueError(f'{path}: missing import {ref}')
        for path in (bp/'blocks').rglob('*.json'):
            block=json.loads(path.read_text(encoding='utf-8'))['minecraft:block'];ident=block['description']['identifier']
            if ident in identifiers:raise ValueError('Block identifier conflict: '+ident)
            identifiers.add(ident);counts['blocks']+=1
            components=block['components']
            geometry=components.get('minecraft:geometry',{})
            geo=geometry if isinstance(geometry,str) else geometry.get('identifier')
            if geo and geo not in geometries:raise ValueError('Missing block geometry '+geo)
            loot=components.get('minecraft:loot')
            if loot and not (bp/loot).is_file():raise ValueError('Missing loot table '+loot)
            for material in components.get('minecraft:material_instances',{}).values():
                registry=json.loads((rp/'textures/terrain_texture.json').read_text(encoding='utf-8'))['texture_data']
                ref=registry[material['texture']]['textures']
                if not (rp/(ref+'.png')).is_file():raise ValueError('Missing block atlas '+ref)
        for path in (bp/'entities').rglob('*.json'):
            ident=json.loads(path.read_text(encoding='utf-8'))['minecraft:entity']['description']['identifier']
            if ident in identifiers:raise ValueError('Entity identifier conflict: '+ident)
            identifiers.add(ident)
        for path in (rp/'animations').rglob('*.json'):
            for name,animation in json.loads(path.read_text(encoding='utf-8'))['animations'].items():
                if not name.startswith('animation.'):raise ValueError('Invalid animation identifier: '+name)
                if '"vector"' in json.dumps(animation) or '"easing"' in json.dumps(animation):raise ValueError('Unconverted GeckoLib channel')
                counts['animations']+=1
        sounddefs=rp/'sounds/sound_definitions.json'
        if sounddefs.exists():
            for sound in json.loads(sounddefs.read_text(encoding='utf-8'))['sound_definitions'].values():
                for ref in sound['sounds']:
                    name=ref if isinstance(ref,str) else ref['name']
                    if not (rp/(name+'.ogg')).is_file():raise ValueError('Missing sound '+name)
                    counts['sounds']+=1
    return counts


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folders',type=Path,nargs='+')
    print(json.dumps(check(ap.parse_args().folders),indent=2))
