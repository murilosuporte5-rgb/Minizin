#!/usr/bin/env python3
"""Rebuild the integrated, offline-validated Android retest candidate.

Original third-party assets stay in the ignored build directory. The result
is a test candidate, not an assertion of Java parity or redistribution rights.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from build_bedrock_packs import zipped
from validate_gameplay_packs import check


ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    print('+', *args, flush=True)
    subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, check=True)


def build(output: Path, backpack_source: Path, previous_addon: Path | None = None) -> Path:
    output = output.resolve()
    backpack_source = backpack_source.resolve()
    if output.exists():
        raise ValueError(f'Use a new build directory: {output}')
    if not (ROOT / 'generated/next_four').is_dir():
        raise FileNotFoundError('Recover generated/ from the pinned generated-bedrock branch')
    if not (backpack_source / 'LICENSE.md').is_file():
        raise FileNotFoundError(f'Sophisticated Backpacks source absent: {backpack_source}')
    output.mkdir(parents=True)
    worlds, stages, four = (output / name for name in ('worlds', 'stages', 'four'))
    waystones, combined = output / 'waystones_v2', output / 'combined'
    mobile, backpack = output / 'mobile', output / 'with_backpack'
    aether, bop = output / 'aether_merged', output / 'bop_merged'
    linked, worlds_combined, candidate = (output / name for name in
                                           ('linked_aether', 'linked_worlds', 'candidate'))
    run('bedrock/worlds/build_worlds.py', '--output', worlds)
    run('tools/build_creature_world_packs.py', '--output', stages)
    run('tools/build_gameplay_four.py', '--output', four)
    run('tools/upgrade_waystone_block.py', '--output', waystones)
    run('tools/combine_gameplay_packs.py', '--output', combined,
        *(stages / name for name in ('iceandfire', 'cataclysm', 'alexscaves', 'mowzies',
                                    'aether', 'biomesoplenty')),
        *(four / name for name in ('mca', 'carryon', 'origins', 'rftools')),
        waystones)
    run('tools/repair_combined_pack.py', combined, '--output', mobile)
    run('tools/add_backpack_to_pack.py', mobile, backpack_source, '--output', backpack)
    run('tools/merge_aether_world_pack.py', '--world', worlds / 'aether',
        '--catalog', stages / 'aether', '--output', aether)
    run('tools/merge_aether_world_pack.py', '--world', worlds / 'bop',
        '--catalog', stages / 'biomesoplenty', '--output', bop)
    run('tools/overlay_aether_world_pack.py', '--combined-source', backpack,
        '--world-pack', aether, '--output', linked)
    run('tools/overlay_aether_world_pack.py', '--combined-source', linked,
        '--world-pack', bop, '--output', worlds_combined, '--prefix', 'bop_full_v3')
    # Repair after the source world overlay: newly registered Aether blocks
    # unlock more original recipes and their real block items need icons.
    run('tools/repair_combined_pack.py', worlds_combined, '--output', candidate)
    if previous_addon is not None:
        run('tools/restore_tested_v033.py', '--previous-addon', previous_addon,
            '--candidate', candidate)
    for role in ('BP', 'RP'):
        manifest = candidate / role / 'manifest.json'
        document = json.loads(manifest.read_text(encoding='utf-8'))
        document['header']['name'] = f'Minizin 12 Mods Android Candidato v0.3.4 {role}'
        document['header']['description'] = 'Integracao experimental; validacao no Minecraft Android pendente'
        document['header']['version'] = [0, 3, 4]
        document['header']['min_engine_version'] = [1, 21, 120]
        for module in document['modules']:
            module['version'] = [0, 3, 4]
        for dependency in document.get('dependencies', []):
            if 'uuid' in dependency:
                dependency['version'] = [0, 3, 4]
        manifest.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    counts = check([candidate])
    archive = output / 'Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v0.3.4.mcaddon'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED) as bundle:
        for role in ('BP', 'RP'):
            bundle.writestr(f'Minizin_v034_{role}.mcpack', zipped(candidate / role))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name in bundle.namelist():
            import io
            with zipfile.ZipFile(io.BytesIO(bundle.read(name))) as pack:
                assert pack.testzip() is None and 'manifest.json' in pack.namelist()
    commits = {}
    for path in sorted((ROOT / 'mods').glob('*/upstream')):
        if (path / '.git').exists():
            commits[path.parent.name] = subprocess.check_output(
                ['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    report = {'status': 'offline candidate; Android untested', 'counts': counts,
              'size_bytes': archive.stat().st_size,
              'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                       cwd=ROOT, text=True).strip(),
              'upstream_commits': commits,
              'conflicts': {name: len(json.loads((candidate / f'OVERLAY_CONFLICTS_{name}.json').read_text()))
                            for name in ('aether_full_v3', 'bop_full_v3')},
              'legacy_v033_restored': (json.loads((candidate/'LEGACY_V033_REPORT.json').read_text())
                                       if previous_addon else None),
              'android_tested': False}
    (output / 'BUILD_REPORT.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'archive': str(archive), **report}, ensure_ascii=False))
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--backpack-source', type=Path,
                        default=ROOT / 'mods/56-sophisticated-backpacks/upstream')
    parser.add_argument('--previous-addon', type=Path,
                        help='Previously tested v0.3.3 archive to retain all existing IDs')
    args = parser.parse_args()
    build(args.output, args.backpack_source, args.previous_addon)
