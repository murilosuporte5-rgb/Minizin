#!/usr/bin/env python3
"""Package twelve individually installable research packs for private QA."""
import argparse
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from build_bedrock_packs import zipped
from validate_gameplay_packs import check


ROOT = Path(__file__).resolve().parents[1]


def pack(folder: Path) -> bytes:
    check([folder])
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, 'w', zipfile.ZIP_STORED) as bundle:
        for role in ('BP', 'RP'):
            bundle.writestr(f'Minizin_{folder.name}_{role}.mcpack', zipped(folder / role))
    with zipfile.ZipFile(io.BytesIO(memory.getvalue())) as bundle:
        assert bundle.testzip() is None
    return memory.getvalue()


def backpack_standalone(build_root: Path) -> Path:
    source = ROOT / 'bedrock/packs/sophisticated_backpacks'
    target = build_root / 'backpack_standalone'
    if target.exists():
        raise ValueError(f'Fresh output required: {target}')
    shutil.copytree(source, target)
    image = build_root / 'candidate/RP/textures/items/backpack.png'
    if not image.exists():
        raise FileNotFoundError(f'Original-source backpack icon missing: {image}')
    destination = target / 'RP/textures/items/backpack.png'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image, destination)
    registry = {'resource_pack_name': 'Minizin Sophisticated Backpacks',
                'texture_name': 'atlas.items',
                'texture_data': {'minizin_backpack': {'textures': 'textures/items/backpack'}}}
    (target / 'RP/textures/item_texture.json').write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    item = target / 'BP/items/backpack.json'
    definition = json.loads(item.read_text(encoding='utf-8'))
    definition['minecraft:item']['components']['minecraft:icon'] = {
        'textures': {'default': 'minizin_backpack'}}
    item.write_text(json.dumps(definition, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return target


def package(build_root: Path) -> Path:
    build_root = build_root.resolve()
    entries = {
        'the_aether': pack(build_root / 'aether_merged'),
        'biomes_o_plenty': pack(build_root / 'bop_merged'),
        'sophisticated_backpacks': pack(backpack_standalone(build_root)),
    }
    for mod in ('iceandfire', 'alexscaves', 'cataclysm', 'mowzies'):
        matches = list((build_root / 'stages').glob(f'Minizin_{mod}_Gameplay_Experimental.mcaddon'))
        if len(matches) != 1:raise FileNotFoundError(mod)
        entries[mod] = matches[0].read_bytes()
    for mod in ('mca', 'carryon', 'origins', 'rftools'):
        matches = list((build_root / 'four' / mod).glob('*.mcaddon'))
        if len(matches) != 1:raise FileNotFoundError(mod)
        entries[mod] = matches[0].read_bytes()
    matches = list((build_root / 'waystones_v2').glob('*.mcaddon'))
    if len(matches) != 1:raise FileNotFoundError('waystones')
    entries['waystones'] = matches[0].read_bytes()
    assert len(entries) == 12
    report = {}
    archive = build_root / 'Minizin_12_Packs_Independentes_CANDIDATOS.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED) as bundle:
        for name, data in sorted(entries.items()):
            with zipfile.ZipFile(io.BytesIO(data)) as addon:
                assert addon.testzip() is None
            filename = f'Minizin_{name}_INDEPENDENTE_EXPERIMENTAL.mcaddon'
            bundle.writestr(filename, data)
            report[name] = {'name': filename, 'size_bytes': len(data),
                            'sha256': hashlib.sha256(data).hexdigest()}
        bundle.writestr('LEIA_ANTES.txt',
            '12 packs experimentais separados. Teste cada pack em um mundo novo; '\
            'não ative todos os independentes junto do integrado. '\
            'Os packs têm coberturas diferentes e não são paridade Java nem QA Android. '\
            'Registre Content Log, versão Bedrock, capturas e testes de persistência. '\
            'Redistribuição pública de arte/som/modelos exige auditoria das licenças.\n')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
    summary = {'archive': str(archive), 'size_bytes': archive.stat().st_size,
               'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'packs': report, 'android_tested': False}
    (build_root / 'INDEPENDENT_REPORT.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-root', type=Path, required=True)
    package(parser.parse_args().build_root)
