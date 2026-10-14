#!/usr/bin/env python3
"""Merge the functional Aether world pack with the broader block catalog."""
import argparse
import json
import shutil
from pathlib import Path


def copy_missing(source: Path, target: Path) -> int:
    copied = 0
    for path in source.rglob('*'):
        if not path.is_file() or path.name == 'manifest.json':
            continue
        relative = path.relative_to(source)
        destination = target / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied += 1
    return copied


def merge_terrain(world: Path, catalog: Path) -> int:
    world_path = world / 'RP/textures/terrain_texture.json'
    catalog_path = catalog / 'RP/textures/terrain_texture.json'
    if not catalog_path.exists():
        return 0
    world_path.parent.mkdir(parents=True, exist_ok=True)
    world_doc = json.loads(world_path.read_text(encoding='utf-8')) if world_path.exists() else {
        'resource_pack_name': 'minizin_worlds_aether',
        'texture_name': 'atlas.terrain',
        'texture_data': {},
    }
    catalog_doc = json.loads(catalog_path.read_text(encoding='utf-8'))
    textures = world_doc.setdefault('texture_data', {})
    added = 0
    for key, value in catalog_doc.get('texture_data', {}).items():
        if key not in textures:
            textures[key] = value
            added += 1
    world_path.write_text(json.dumps(world_doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return added


def merge(world: Path, catalog: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f'Choose a fresh output folder: {output}')
    shutil.copytree(world, output)
    copied = 0
    for role in ('BP', 'RP'):
        copied += copy_missing(catalog / role, output / role)
    terrain_added = merge_terrain(output, catalog)
    print(json.dumps({
        'output': str(output),
        'copied_missing_files': copied,
        'added_terrain_keys': terrain_added,
    }))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--world', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    merge(args.world, args.catalog, args.output)
