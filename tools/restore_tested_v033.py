#!/usr/bin/env python3
"""Restore identifiers present in the user's v0.3.3 Android retest pack.

This optional local overlay never overwrites newer content except the legacy
RFTools grid runtime, whose earlier repository copy used a vanilla lodestone.
Do not commit the input archive or copied third-party binary assets.
"""
import argparse
import hashlib
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from validate_gameplay_packs import check


ROOT_KEYS = {'items': 'minecraft:item', 'blocks': 'minecraft:block',
             'entities': 'minecraft:entity', 'biomes': 'minecraft:biome'}


def identifier(path, category):
    document = json.loads(path.read_text(encoding='utf-8'))
    return document.get(ROOT_KEYS[category], {}).get('description', {}).get('identifier')


def unpack(archive: Path, directory: Path):
    with zipfile.ZipFile(archive) as outer:
        assert outer.testzip() is None
        for name in outer.namelist():
            role = 'BP' if 'BehaviorPack' in name else 'RP' if 'ResourcePack' in name else None
            if not role:
                raise ValueError(f'Unexpected inner pack: {name}')
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                assert inner.testzip() is None
                for member in inner.namelist():
                    destination = directory / role / member
                    if member.startswith('/') or '..' in Path(member).parts:
                        raise ValueError(f'Unsafe archive member: {member}')
                    if member.endswith('/'):
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(inner.read(member))


def merge_registry(legacy: Path, current: Path, key: str):
    a = json.loads(legacy.read_text(encoding='utf-8'))
    b = json.loads(current.read_text(encoding='utf-8'))
    added = []
    for name, value in a.get(key, {}).items():
        if name not in b.setdefault(key, {}):
            b[key][name] = value
            added.append(name)
    current.write_text(json.dumps(b, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return added


def restore(previous: Path, candidate: Path):
    previous = previous.resolve()
    candidate = candidate.resolve()
    with tempfile.TemporaryDirectory() as temp:
        old = Path(temp)
        unpack(previous, old)
        copied, skipped, resources = {}, {}, 0
        for category in ROOT_KEYS:
            present = {identifier(path, category) for path in (candidate/'BP'/category).rglob('*.json')}
            copied[category], skipped[category] = [], []
            for path in (old/'BP'/category).rglob('*.json'):
                name = identifier(path, category)
                if name in present:
                    continue
                destination = candidate/'BP'/category/path.relative_to(old/'BP'/category)
                if destination.exists():
                    raise ValueError(f'Legacy path conflicts with new item: {destination}')
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
                present.add(name)
                copied[category].append(name)
        # Keep newer art wherever paths already exist; bring in older paths
        # needed by the six creature aliases and legacy RFTools machine blocks.
        for path in (old/'RP').rglob('*'):
            if not path.is_file():continue
            relative = path.relative_to(old/'RP')
            if relative.name in ('manifest.json','item_texture.json','terrain_texture.json',
                                 'sound_definitions.json','en_US.lang','pt_BR.lang','languages.json'):
                continue
            destination = candidate/'RP'/relative
            if destination.exists():continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            resources += 1
        for filename, key in [('item_texture.json','texture_data'),
                              ('terrain_texture.json','texture_data')]:
            merge_registry(old/'RP/textures'/filename, candidate/'RP/textures'/filename, key)
        old_sound = old/'RP/sounds/sound_definitions.json'
        new_sound = candidate/'RP/sounds/sound_definitions.json'
        if old_sound.exists() and new_sound.exists():
            merge_registry(old_sound, new_sound, 'sound_definitions')
        for language in ('en_US', 'pt_BR'):
            old_lang = old/'RP/texts'/f'{language}.lang'
            new_lang = candidate/'RP/texts'/f'{language}.lang'
            lines = new_lang.read_text(encoding='utf-8').splitlines()
            keys = {line.split('=',1)[0] for line in lines if '=' in line}
            additions = [line for line in old_lang.read_text(encoding='utf-8').splitlines()
                         if '=' in line and line.split('=',1)[0] not in keys]
            new_lang.write_text('\n'.join(lines+additions)+'\n', encoding='utf-8')
        old_scripts = old/'BP/scripts/minizin_creatures'
        new_scripts = candidate/'BP/scripts/minizin_creatures'
        shutil.copytree(old_scripts, new_scripts)
        entry = candidate/'BP/scripts/main.js'
        line = 'import "./minizin_creatures/main.js";'
        if line not in entry.read_text(encoding='utf-8'):
            entry.write_text(entry.read_text(encoding='utf-8').rstrip()+'\n'+line+'\n', encoding='utf-8')
        # Restore the tested physical four-block grid and its v2 migration
        # state; the newer tiered machine runtime continues on separate IDs.
        shutil.copy2(old/'BP/scripts/rftools/rftools.js',
                     candidate/'BP/scripts/rftools/rftools.js')
        # Vanilla creative icons in the old pack masked real Java item PNGs.
        # Alias items now point at their already integrated source-backed icons.
        item_icons = json.loads((candidate/'RP/textures/item_texture.json').read_text())['texture_data']
        for name in ('dragon_meal','creative_dragon_meal','dragon_flute','dragon_armor_iron','serene_salad'):
            path = candidate/'BP/items/minizin_creatures'/f'{name}.json'
            if not path.is_file():
                continue
            document = json.loads(path.read_text(encoding='utf-8'))
            namespace = 'minizin_alexscaves' if name == 'serene_salad' else 'minizin_iceandfire'
            icon = namespace+'_'+name
            if icon not in item_icons:raise ValueError(f'Original icon missing for legacy alias: {icon}')
            document['minecraft:item']['components']['minecraft:icon'] = {
                'textures': {'default': icon}}
            path.write_text(json.dumps(document, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        counts = check([candidate])
        for category in ROOT_KEYS:
            original_ids = {identifier(path, category) for path in (old/'BP'/category).rglob('*.json')}
            current_ids = {identifier(path, category) for path in (candidate/'BP'/category).rglob('*.json')}
            missing = original_ids - current_ids
            if missing:
                raise ValueError(f'Legacy {category} IDs lost: {sorted(missing)}')
        report = {'source_name': previous.name, 'source_sha256': hashlib.sha256(previous.read_bytes()).hexdigest(),
                  'restored_identifiers': copied, 'resource_files_added': resources,
                  'rftools_grid_v2_restored': True, 'validation': counts,
                  'android_tested': False}
        (candidate/'LEGACY_V033_REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps(report, ensure_ascii=False))
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous-addon', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    restore(args.previous_addon, args.candidate)
