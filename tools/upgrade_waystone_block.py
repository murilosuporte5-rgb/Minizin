#!/usr/bin/env python3
"""Upgrade an *existing* staged pack to a real Waystones block.

Preserves the v1 world registry for migration, copies original Java-converted
geometry and texture already in the RP, and never rewrites source directories.
The old entity definition stays only so old worlds can be migrated on load.
"""
from __future__ import annotations
import argparse
import copy
import json
import shutil
import zipfile
from pathlib import Path
from build_bedrock_packs import zipped
from validate_gameplay_packs import check

ROOT = Path(__file__).resolve().parents[1]
BLOCK = "minizin:andesite_waystone_block"
GEO = "geometry.minizin.andesite_waystone_block"


def write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_locale(path, new):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    rows = [line for line in old.splitlines() if line.partition("=")[0] not in new]
    path.write_text("\n".join(rows + [k + "=" + v for k, v in new.items()]) + "\n", encoding="utf-8")


def upgrade(folder: Path):
    """Mutate a fresh build output; do NOT call on the canonical source pack."""
    rp, bp = folder / "RP", folder / "BP"
    entity_geo = rp / "models/entity/andesite_waystone.geo.json"
    entity_texture = rp / "textures/entity/andesite_waystone.png"
    if not entity_geo.is_file() or not entity_texture.is_file():
        raise FileNotFoundError("Existing Waystone geometry/texture required; no generic replacement.")
    doc = json.loads(entity_geo.read_text())
    copied = copy.deepcopy(doc)
    if len(copied["minecraft:geometry"]) != 1:
        raise ValueError("Unexpected original Waystone geometry count")
    copied["minecraft:geometry"][0]["description"]["identifier"] = GEO
    write(rp / "models/blocks/andesite_waystone.geo.json", copied)

    terrain = rp / "textures/terrain_texture.json"
    registry = json.loads(terrain.read_text()) if terrain.exists() else {
        "resource_pack_name": "Minizin Waystones", "texture_name": "atlas.terrain",
        "texture_data": {},
    }
    registry["texture_data"]["minizin_waystone_original"] = {
        "textures": "textures/entity/andesite_waystone"
    }
    write(terrain, registry)

    name = "tile.minizin:andesite_waystone_block.name"
    components = {
        "minecraft:geometry": {"identifier": GEO},
        "minecraft:material_instances": {"*": {
            "texture": "minizin_waystone_original", "render_method": "alpha_test"
        }},
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 2.5},
        "minecraft:loot": "loot_tables/blocks/andesite_waystone_block.json",
        "minecraft:collision_box": {"origin": [-8, 0, -8], "size": [16, 16, 16]},
        "minecraft:selection_box": {"origin": [-8, 0, -8], "size": [16, 16, 16]},
        "minecraft:display_name": name,
        "minizin:waystone_control": {},
    }
    permutations = []
    for direction, degrees in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        permutations.append({
            "condition": "q.block_state('minecraft:cardinal_direction') == '" + direction + "'",
            "components": {"minecraft:transformation": {"rotation": [0, degrees, 0]}},
        })
    # Separate light from facing permutation: these combine without overriding
    # any other block component, and use an original texture in both states.
    permutations.append({
        "condition": "q.block_state('minizin:active') == true",
        "components": {"minecraft:light_emission": 7},
    })
    write(bp / "blocks/andesite_waystone_block.json", {
        "format_version": "1.21.90",
        "minecraft:block": {
            "description": {
                "identifier": BLOCK,
                "menu_category": {"category": "construction"},
                "states": {"minizin:active": [False, True]},
                "traits": {"minecraft:placement_direction": {
                    "enabled_states": ["minecraft:cardinal_direction"],
                }},
            },
            "components": components,
            "permutations": permutations,
        },
    })

    icon_key = "minizin_waystone_original_item"
    icon_path = "textures/items/waystones/andesite_waystone"
    src = ROOT / "mods/15-waystones/upstream/common/src/main/resources/assets/waystones/textures/item/andesite_waystone.png"
    dest = rp / (icon_path + ".png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dest)
        icon_source = str(src.relative_to(ROOT))
    else:
        # Exact texture from the original converted Waystone: known visibility,
        # but atlas-to-item icon fidelity must be checked on Android.
        shutil.copy2(entity_texture, dest)
        icon_source = "Existing converted Waystone atlas (fallback; not a Java item icon)"
    items = rp / "textures/item_texture.json"
    icons = json.loads(items.read_text()) if items.exists() else {
        "resource_pack_name": "Minizin Waystones", "texture_name": "atlas.items", "texture_data": {}
    }
    icons["texture_data"][icon_key] = {"textures": icon_path}
    write(items, icons)
    write(bp / "items/andesite_waystone_block.json", {
        "format_version": "1.21.90",
        "minecraft:item": {
            "description": {"identifier": BLOCK, "menu_category": {"category": "construction"}},
            "components": {
                "minecraft:icon": {"textures": {"default": icon_key}},
                "minecraft:display_name": {"value": name},
                "minecraft:max_stack_size": 64,
                "minecraft:block_placer": {"block": BLOCK},
            },
        },
    })
    write(bp / "loot_tables/blocks/andesite_waystone_block.json", {
        "pools": [{"rolls": 1, "entries": [{"type": "item", "name": BLOCK, "weight": 1}]}]
    })
    # Player break normally leaves block drops to the engine; do not spawn a
    # second item from script. No source item custom texture is invented.
    for lang, title in (("pt_BR", "Marco de Teleporte"), ("en_US", "Waystone")):
        append_locale(rp / "texts" / (lang + ".lang"), {
            name: title,
            "item." + BLOCK + ".name": title,
        })

    # Keep the legacy entity only for old-world conversion, without its spawn egg.
    old_entity = bp / "entities/andesite_waystone.json"
    if old_entity.exists():
        legacy = json.loads(old_entity.read_text())
        desc = legacy["minecraft:entity"]["description"]
        desc["is_spawnable"] = False
        desc["is_summonable"] = False
        comp = legacy["minecraft:entity"]["components"]
        comp["minecraft:knockback_resistance"] = {"value": 1.0}
        comp["minecraft:damage_sensor"] = {"triggers": [{"cause": "all", "deals_damage": False}]}
        write(old_entity, legacy)
    client = rp / "entity/andesite_waystone.entity.json"
    if client.exists():
        old = json.loads(client.read_text())
        old["minecraft:client_entity"]["description"].pop("spawn_egg", None)
        write(client, old)

    scripts = bp / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "bedrock/runtime/waystones_block.js", scripts / "waystones_block.js")
    main = scripts / "main.js"
    original = main.read_text() if main.is_file() else ""
    legacy_import = 'import "./waystones/main.js";'
    if legacy_import in original:
        new_main = original.replace(legacy_import, 'import "./waystones_block.js";')
    elif original.startswith('import "./waystones_block.js";'):
        new_main = original
    else:
        new_main = 'import "./waystones_block.js";\n'
    main.write_text(new_main)
    if 'import "./warp_stone.js";' in new_main:
        shutil.copy2(ROOT / "bedrock/runtime/warp_stone.js", scripts / "warp_stone.js")
    report = {
        "mod": "Waystones",
        "original_geometry": str(entity_geo.relative_to(folder)),
        "original_texture": str(entity_texture.relative_to(folder)),
        "icon_source": icon_source,
        "new_block": BLOCK,
        "legacy_entity": "Retained ONLY for loaded-chunk migration, no spawn egg",
        "storage_schema": "minizin:waystones_world_v1 (preserved)",
        "limitations": [
            "Android placement/UI/render and full multiplayer tests pending",
            "Legacy entity migration only in loaded nearby areas",
            "No guaranteed engine-level atomicity if interrupted during migration",
            "Standing 30px model uses collision/selection limited to base block",
            "Visual activation uses emitted light; original on/off artwork not verified",
            "Existing-world backup required",
        ],
        "tested_in_android": False,
    }
    write(folder / "WAYSTONE_BLOCK_REPORT.json", report)
    return report


def build_standalone(source: Path, output: Path):
    if output.exists():
        raise ValueError("Fresh output required; older versions must remain intact")
    shutil.copytree(source, output)
    for addon in output.glob("*.mcaddon"):
        addon.unlink()
    report = upgrade(output)
    for role in ["RP", "BP"]:
        manifest = output / role / "manifest.json"
        doc = json.loads(manifest.read_text())
        doc["header"]["version"] = [0, 2, 5]
        doc["header"]["min_engine_version"] = [1, 21, 90]
        doc["header"]["name"] = "Minizin Waystones Block Prototype " + role
        for module in doc["modules"]:
            module["version"] = [0, 2, 5]
        for dependency in doc.get("dependencies", []):
            if "uuid" in dependency:
                dependency["version"] = [0, 2, 5]
        write(manifest, doc)
    report["structural"] = check([output])
    write(output / "WAYSTONE_BLOCK_REPORT.json", report)
    dest = output / "Minizin_Waystones_Block_v0.2.5_EXPERIMENTAL.mcaddon"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_STORED) as archive:
        for role in ("RP", "BP"):
            archive.writestr("Minizin_Waystones_" + role + ".mcpack", zipped(output / role))
    assert zipfile.ZipFile(dest).testzip() is None
    print(json.dumps({"output": str(dest), "report": report}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "bedrock/packs/waystones")
    parser.add_argument("--output", type=Path, required=True)
    opt = parser.parse_args()
    build_standalone(opt.source, opt.output)
