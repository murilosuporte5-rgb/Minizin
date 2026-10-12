#!/usr/bin/env python3
"""Local, isolated Bedrock pack builder for Aether + Biomes O' Plenty.

Third-party textures are read from the pinned git submodules and placed only
in build/ (ignored by Git). No art, audio or NBT is redistributed in this tree.
"""
from __future__ import annotations

import argparse
import json
import shutil
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = {
    "aether": ROOT / "mods/41-the-aether/upstream/src/main/resources/assets/aether/textures/block",
    "bop": ROOT / "mods/19-biomes-o-plenty/upstream/common/src/main/resources/assets/biomesoplenty/textures/block",
}
NAMESPACE = {"aether": "minizin_aether", "bop": "minizin_bop"}
ASSETS = {
    "aether": {
        "holystone": ("natural/holystone.png", "stone"),
        "aether_dirt": ("natural/aether_dirt.png", "gravel"),
        "aether_grass": ("natural/aether_grass_block_side.png", "grass"),
        "ambrosium_ore": ("natural/ambrosium_ore.png", "stone"),
        "zanite_ore": ("natural/zanite_ore.png", "stone"),
        "skyroot_log": ("natural/skyroot_log.png", "wood"),
        "skyroot_leaves": ("natural/skyroot_leaves.png", "grass"),
        "golden_oak_log": ("natural/golden_oak_log.png", "wood"),
        "golden_oak_leaves": ("natural/golden_oak_leaves.png", "grass"),
        "holystone_bricks": ("construction/holystone_bricks.png", "stone"),
        "aether_portal": ("miscellaneous/aether_portal.png", "glass"),
        "carved_stone": ("dungeon/carved_stone.png", "stone"),
        "angelic_stone": ("dungeon/angelic_stone.png", "stone"),
        "light_angelic_stone": ("dungeon/light_angelic_stone.png", "stone"),
        "hellfire_stone": ("dungeon/hellfire_stone.png", "stone"),
        "light_hellfire_stone": ("dungeon/light_hellfire_stone.png", "stone"),
        "sentry_stone": ("dungeon/sentry_stone.png", "stone"),
        "locked_angelic_stone": ("dungeon/angelic_stone.png", "stone"),
        "boss_doorway_angelic_stone": ("dungeon/door.png", "stone"),
        "pillar": ("dungeon/pillar_side.png", "stone"),
        "mossy_holystone": ("natural/mossy_holystone.png", "stone"),
        "icestone": ("natural/icestone.png", "stone"),
        "quicksoil": ("natural/quicksoil.png", "sand"),
        "skyroot_planks": ("construction/skyroot_planks.png", "wood"),
        "cold_aercloud": ("natural/cold_aercloud.png", "glass"),
        "blue_aercloud": ("natural/blue_aercloud.png", "glass"),
        "golden_aercloud": ("natural/golden_aercloud.png", "glass"),
        "gravitite_ore": ("natural/gravitite_ore.png", "stone"),
        "crystal_leaves": ("natural/crystal_leaves.png", "grass"),
        "crystal_fruit_leaves": ("natural/crystal_fruit_leaves.png", "grass"),
        "skyroot_sapling": ("natural/skyroot_sapling.png", "grass"),
        "white_flower": ("natural/white_flower.png", "grass"),
        "purple_flower": ("natural/purple_flower.png", "grass"),
        "berry_bush": ("natural/berry_bush.png", "grass"),
        "sun_altar": ("utility/sun_altar_side.png", "stone"),
        "locked_carved_stone": ("dungeon/carved_stone.png", "stone"),
        "locked_sentry_stone": ("dungeon/sentry_stone.png", "stone"),
        "boss_doorway_carved_stone": ("dungeon/door.png", "stone"),
        "locked_light_angelic_stone": ("dungeon/light_angelic_stone.png", "stone"),
        "trapped_angelic_stone": ("dungeon/angelic_stone.png", "stone"),
        "trapped_light_angelic_stone": ("dungeon/light_angelic_stone.png", "stone"),
        "treasure_doorway_angelic_stone": ("dungeon/treasure.png", "stone"),
        "locked_hellfire_stone": ("dungeon/hellfire_stone.png", "stone"),
        "locked_light_hellfire_stone": ("dungeon/light_hellfire_stone.png", "stone"),
        "boss_doorway_hellfire_stone": ("dungeon/door.png", "stone"),
        "treasure_doorway_hellfire_stone": ("dungeon/treasure.png", "stone"),
    },
    "bop": {
        "lavender": ("lavender.png", "grass"),
        "magic_log": ("magic_log.png", "wood"),
        "magic_leaves": ("magic_leaves.png", "grass"),
        "redwood_log": ("redwood_log.png", "wood"),
        "redwood_leaves": ("redwood_leaves.png", "grass"),
        "umbran_log": ("umbran_log.png", "wood"),
        "umbran_leaves": ("umbran_leaves.png", "grass"),
        "glowflower": ("glowflower.png", "grass"),
        "fir_log": ("fir_log.png", "wood"),
        "fir_leaves": ("fir_leaves.png", "grass"),
        "pine_log": ("pine_log.png", "wood"),
        "pine_leaves": ("pine_leaves.png", "grass"),
        "jacaranda_log": ("jacaranda_log.png", "wood"),
        "jacaranda_leaves": ("jacaranda_leaves.png", "grass"),
        "maple_log": ("maple_log.png", "wood"),
        "maple_leaves": ("pink_maple_leaves.png", "grass"),
        "palm_log": ("palm_log.png", "wood"),
        "palm_leaves": ("palm_leaves.png", "grass"),
        "white_lavender": ("white_lavender.png", "grass"),
        "violet": ("violet.png", "grass"),
    },
}
# Directional texture faces preserve the original top/bottom materials instead of
# stretching the Java side texture across all six faces in Bedrock.
FACES = {
    "aether": {
        "aether_grass": {"up": "natural/aether_grass_block_top.png",
                         "down": "natural/aether_dirt.png"},
        "skyroot_log": {"up": "natural/skyroot_log_top.png",
                        "down": "natural/skyroot_log_top.png"},
        "pillar": {"up": "dungeon/pillar_top.png",
                   "down": "dungeon/pillar_top.png"},
        "sun_altar": {"up": "utility/sun_altar_top.png", "down": "utility/sun_altar_top.png"},
    },
    "bop": {
        "magic_log": {"up": "magic_log_top.png", "down": "magic_log_top.png"},
        "redwood_log": {"up": "redwood_log_top.png", "down": "redwood_log_top.png"},
        "umbran_log": {"up": "umbran_log_top.png", "down": "umbran_log_top.png"},
        "fir_log": {"up": "fir_log_top.png", "down": "fir_log_top.png"},
        "pine_log": {"up": "pine_log_top.png", "down": "pine_log_top.png"},
        "jacaranda_log": {"up": "jacaranda_log_top.png", "down": "jacaranda_log_top.png"},
        "maple_log": {"up": "maple_log_top.png", "down": "maple_log_top.png"},
        "palm_log": {"up": "palm_log_top.png", "down": "palm_log_top.png"},
    },
}
PLANTS = {"bop": {"lavender", "glowflower", "white_lavender", "violet"},
          "aether": {"white_flower", "purple_flower", "berry_bush", "skyroot_sapling"}}
LEAVES = {
    "aether": {"skyroot_leaves", "golden_oak_leaves",
              "crystal_leaves", "crystal_fruit_leaves"},
    "bop": {"magic_leaves", "redwood_leaves", "umbran_leaves", "fir_leaves",
            "pine_leaves", "jacaranda_leaves", "maple_leaves", "palm_leaves"},
}
BIOME_SOURCE = ROOT / "mods/19-biomes-o-plenty/upstream/common/src/generated/resources/data/biomesoplenty/worldgen/biome"
AETHER_BIOME_SOURCE = ROOT / "mods/41-the-aether/upstream/src/generated/resources/data/aether/worldgen/biome"
AETHER_BIOME_DENSITIES = {"skyroot_forest": 9, "skyroot_grove": 6,
                          "skyroot_meadow": 2, "skyroot_woodland": 4}
BIOMES = {
    "lavender_field": dict(temp=.75, rain=.42, noise="lowlands", climate="medium",
                          tree=None, flower="lavender", trees=0, flowers=10,
                          water="#5584c9", fog="#d9baf0"),
    "mystic_grove": dict(temp=.65, rain=.8, noise="default", climate="medium",
                         tree="magic", flower="glowflower", trees=3, flowers=5,
                         water="#7358b5", fog="#8976c8"),
    "redwood_forest": dict(temp=.5, rain=.8, noise="highlands", climate="medium",
                           tree="redwood", flower=None, trees=4, flowers=0,
                           water="#436d83", fog="#8b9da0"),
    "ominous_woods": dict(temp=.7, rain=.8, noise="default", climate="medium",
                          tree="umbran", flower=None, trees=4, flowers=0,
                          water="#3b3b59", fog="#55516b"),
    "coniferous_forest": dict(temp=.5, rain=.75, noise="default", climate="medium",
                             tree="fir", flower=None, trees=5, flowers=0,
                             water="#3f76e4", fog="#aaaaaa"),
    "maple_woods": dict(temp=.65, rain=.55, noise="default", climate="medium",
                        tree="maple", flower=None, trees=5, flowers=0,
                        water="#3f76e4", fog="#aaaaaa"),
    "jade_cliffs": dict(temp=.7, rain=.7, noise="highlands", climate="medium",
                        tree="jacaranda", flower=None, trees=3, flowers=0,
                        water="#3f76e4", fog="#aaaaaa"),
    "tropics": dict(temp=.85, rain=.85, noise="default", climate="warm",
                    tree="palm", flower=None, trees=4, flowers=0,
                    water="#3f76e4", fog="#aaaaaa"),
    "highland": dict(temp=.5, rain=.5, noise="highlands", climate="medium",
                     tree="pine", flower=None, trees=3, flowers=0,
                     water="#3f76e4", fog="#aaaaaa"),
}
# Stable UUIDv5 avoids pack identity churn between builds and device upgrades.
def uid(part: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/murilosuporte5-rgb/Minizin/worlds/" + part))

def jwrite(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def manifest(mod: str, kind: str) -> dict:
    name = "The Aether" if mod == "aether" else "Biomes O' Plenty"
    data = {
        "format_version": 2,
        "header": {
            "name": f"Minizin Worlds - {name} ({kind})",
            "description": "Private local conversion from pinned Java resources; experimental behavior.",
            "uuid": uid(f"{mod}-{kind}-header"),
            "version": [0, 2, 8],
            "min_engine_version": [1, 21, 110] if mod == "bop" else [1, 21, 80],
        },
        "modules": [{
            "type": "data" if kind == "BP" else "resources",
            "uuid": uid(f"{mod}-{kind}-module"),
            "version": [0, 2, 8],
        }],
    }
    if kind == "BP":
        data["dependencies"] = [{"uuid": uid(f"{mod}-RP-header"), "version": [0, 2, 8]}]
        if mod in ("aether", "bop"):
            data["modules"].append({
                "type": "script",
                "language": "javascript",
                "entry": "scripts/main.js",
                "uuid": uid(f"{mod}-BP-script"),
                "version": [0, 2, 8],
            })
            data["dependencies"].append({"module_name": "@minecraft/server", "version": "beta" if mod == "aether" else "2.0.0"})
    return data

def block_def(mod: str, name: str) -> dict:
    ns = NAMESPACE[mod]
    components = {
        "minecraft:geometry": "minecraft:geometry.full_block",
        "minecraft:material_instances": {
            "*": {"texture": f"{ns}_{name}",
                  "render_method": "alpha_test" if name in LEAVES[mod] else "opaque"}
        },
        "minecraft:destructible_by_mining": {
            "seconds_to_destroy": 0.3 if name in PLANTS.get(mod, set()) else 1.2
        },
    }
    for face in FACES.get(mod, {}).get(name, {}):
        components["minecraft:material_instances"][face] = {
            "texture": f"{ns}_{name}_{face}", "render_method": "opaque"}
    if name in PLANTS.get(mod, set()):
        components["minecraft:geometry"] = "geometry.minizin_worlds.cross"
        components["minecraft:collision_box"] = False
        components["minecraft:selection_box"] = {"origin": [-7, 0, -7], "size": [14, 16, 14]}
        components["minecraft:material_instances"]["*"]["render_method"] = "alpha_test"
    if mod == "aether" and ("locked_" in name or "trapped_" in name
                            or "boss_doorway_" in name or "treasure_doorway_" in name):
        # Source has dungeon lock semantics. Until original boss progression is
        # ported these must stay locked rather than granting fake access.
        components["minecraft:destructible_by_mining"] = False
        components["minecraft:destructible_by_explosion"] = False
    if name == "aether_portal":
        components["minecraft:geometry"] = "geometry.minizin_worlds.portal"
        components["minecraft:collision_box"] = False
        components["minecraft:selection_box"] = False
        components["minecraft:material_instances"]["*"]["render_method"] = "blend"
    desc = {"identifier": f"{ns}:{name}", "menu_category": {"category": "nature"}}
    if name == "aether_portal":
        desc["states"] = {"minizin_aether:axis": ["x", "z"]}
        # The texture is a thin plane, rotated when the glowstone frame faces X.
        perms = [{"condition": "q.block_state('minizin_aether:axis') == 'x'",
                  "components": {"minecraft:transformation": {"rotation": [0, 90, 0]}}}]
    else:
        perms = []
    b = {"description": desc, "components": components}
    if perms:
        b["permutations"] = perms
    return {"format_version": "1.21.80", "minecraft:block": b}

def geometry(kind: str) -> dict:
    # Original textures supply the faces. Geometry adapts plane layout for Bedrock.
    cubes = ([{"origin": [-8, 0, -0.5], "size": [16, 16, 1], "uv": [0, 0]}]
             if kind == "portal" else [
                 {"origin": [-8, 0, -0.1], "size": [16, 16, .2],
                  "pivot": [0, 8, 0], "rotation": [0, 45, 0], "uv": [0, 0]},
                 {"origin": [-8, 0, -0.1], "size": [16, 16, .2],
                  "pivot": [0, 8, 0], "rotation": [0, -45, 0], "uv": [0, 0]},
             ])
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.minizin_worlds.{kind}",
                        "texture_width": 16, "texture_height": 16,
                        "visible_bounds_width": 2, "visible_bounds_height": 2.5,
                        "visible_bounds_offset": [0, .75, 0]},
        "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": cubes}],
    }]}

def copy_texture(source: Path, target: Path, mod: str, name: str) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Original asset missing: {source}. Initialize git submodules.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Java animated portal sprite sheets have vertically stacked frames. Retain
    # the original first frame instead of incorrectly stretching the whole PNG.
    if name == "aether_portal":
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow required for extracting Aether portal animation frame") from exc
        with Image.open(source) as img:
            if img.height > img.width:
                img.crop((0, 0, img.width, img.width)).save(target)
            else:
                img.save(target)
    else:
        shutil.copyfile(source, target)

def aether_biome_profiles() -> list[dict]:
    """Extract real Java biome IDs and feature references from pinned sources.

    Tree density is explicitly a Bedrock runtime adjustment, not Java parity.
    """
    profiles = []
    for name, attempts in AETHER_BIOME_DENSITIES.items():
        src = AETHER_BIOME_SOURCE / f"{name}.json"
        if not src.is_file():
            raise FileNotFoundError(f"Original Aether biome JSON missing: {src}")
        data = json.loads(src.read_text(encoding="utf-8"))
        features = [x for group in data.get("features", []) for x in group]
        if f"aether:{name}_trees" not in features:
            raise ValueError(f"Original Aether tree feature not present: {name}")
        profiles.append({"java_id": f"aether:{name}",
                         "temperature": data["temperature"],
                         "downfall": data["downfall"],
                         "tree_attempts": attempts,
                         "java_tree_feature": f"aether:{name}_trees",
                         "java_feature_refs": features})
    return profiles


def java_biome_spec(name: str, proposal: dict) -> dict:
    """Read climatic values and water palette from the pinned original Java data.

    Java noise/router, spawn rules and feature lists are not directly executable.
    Those fields must NOT be represented as ported.
    """
    path = BIOME_SOURCE / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Original biome definition missing: {path}")
    source = json.loads(path.read_text(encoding="utf-8"))
    if "temperature" not in source or "downfall" not in source:
        raise ValueError(f"Original biome missing temperature/downfall: {name}")
    palette = source.get("effects", {})
    return {**proposal, "temp": float(source["temperature"]),
            "rain": float(source["downfall"]),
            "water": palette.get("water_color", proposal["water"]),
            "grass_color": palette.get("grass_color"),
            "foliage_color": palette.get("foliage_color")}


def biome_def(name: str, spec: dict) -> dict:
    ns = NAMESPACE["bop"]
    return {"format_version": "1.21.40", "minecraft:biome": {
        "description": {"identifier": f"{ns}:{name}"},
        "components": {
            "minecraft:climate": {"temperature": spec["temp"], "downfall": spec["rain"],
                                  "snow_accumulation": [0, 0], "ash": 0,
                                  "red_spores": 0, "white_ash": 0},
            "minecraft:overworld_height": {"noise_type": spec["noise"]},
            "minecraft:surface_parameters": {
                "sea_floor_depth": 7, "sea_floor_material": "minecraft:gravel",
                "foundation_material": "minecraft:stone", "mid_material": "minecraft:dirt",
                "top_material": "minecraft:grass_block", "sea_material": "minecraft:water"},
            "minecraft:overworld_generation_rules": {
                "generate_for_climates": [[spec["climate"], 2]]},
            "minecraft:tags": {"tags": ["overworld", name, "minizin_bop", "no_legacy_worldgen"]},
        },
    }}

def rule(biome: str, feature: str, count: int) -> dict:
    ns = NAMESPACE["bop"]
    name = f"{biome}_{feature}_rule"
    return {"format_version": "1.21.40", "minecraft:feature_rules": {
        "description": {"identifier": f"{ns}:{name}",
                        "places_feature": f"{ns}:{feature}_feature"},
        "conditions": {
            "placement_pass": "surface_pass",
            "minecraft:biome_filter": {"test": "has_biome_tag", "operator": "==",
                                       "value": biome},
        },
        "distribution": {
            "iterations": count,
            "x": {"distribution": "uniform", "extent": [0, 15]},
            "y": "query.heightmap(variable.worldx, variable.worldz)",
            "z": {"distribution": "uniform", "extent": [0, 15]},
        },
    }}

def tree_feature(tree: str) -> dict:
    ns = NAMESPACE["bop"]
    base = 12 if tree == "redwood" else 5
    return {"format_version": "1.21.40", "minecraft:tree_feature": {
        "description": {"identifier": f"{ns}:{tree}_feature"},
        "acacia_trunk": {
            "trunk_width": 2 if tree == "redwood" else 1,
            "trunk_height": {"base": base, "intervals": [4],
                             "min_height_for_canopy": 4},
            "trunk_block": {"name": f"{ns}:{tree}_log"},
            "trunk_lean": {"allow_diagonal_growth": False},
        },
        "random_spread_canopy": {
            "canopy_height": 5 if tree == "redwood" else 3,
            "canopy_radius": 4 if tree == "redwood" else 3,
            "leaf_placement_attempts": 110,
            "leaf_blocks": [[f"{ns}:{tree}_leaves", 1]],
        },
        "may_grow_on": ["minecraft:grass_block", "minecraft:dirt", "minecraft:podzol"],
        "may_replace": ["minecraft:air", "minecraft:tallgrass", "minecraft:grass",
                        "minecraft:oak_leaves", f"{ns}:{tree}_leaves"],
        "may_grow_through": ["minecraft:air", "minecraft:tallgrass", "minecraft:grass"],
    }}

def flower_feature(name: str) -> dict:
    ns = NAMESPACE["bop"]
    return {"format_version": "1.21.40", "minecraft:single_block_feature": {
        "description": {"identifier": f"{ns}:{name}_feature"},
        "places_block": f"{ns}:{name}", "may_replace": ["minecraft:air"],
        "enforce_placement_rules": False, "enforce_survivability_rules": False,
    }}

def add_biomes(bp: Path, rp: Path) -> None:
    for name, proposal in BIOMES.items():
        spec = java_biome_spec(name, proposal)
        jwrite(bp / "biomes" / f"{name}.json", biome_def(name, spec))
        jwrite(rp / "biomes_client" / f"{name}.biome_client.json", {
            "format_version": "1.21.40",
            "minecraft:client_biome": {
                "description": {"identifier": f"minizin_bop:{name}"},
                "components": {
                    "minecraft:water_appearance": {
                        "surface_color": spec["water"], "surface_opacity": .6},
                    **({"minecraft:grass_appearance": {"color": spec["grass_color"]}}
                       if spec["grass_color"] else {}),
                    **({"minecraft:foliage_appearance": {"color": spec["foliage_color"]}}
                       if spec["foliage_color"] else {}),
                },
            },
        })
        if spec["tree"]:
            jwrite(bp / "feature_rules" / f"{name}_tree_rule.json",
                   rule(name, spec["tree"], spec["trees"]))
        if spec["flower"]:
            jwrite(bp / "feature_rules" / f"{name}_flower_rule.json",
                   rule(name, spec["flower"], spec["flowers"]))
    for tree in ("magic", "redwood", "umbran", "fir", "maple", "jacaranda", "palm", "pine"):
        jwrite(bp / "features" / f"{tree}_feature.json", tree_feature(tree))
    for flower in ("lavender", "glowflower", "white_lavender", "violet"):
        jwrite(bp / "features" / f"{flower}_feature.json", flower_feature(flower))

def validate_pack(bp: Path, rp: Path, mod: str) -> None:
    ns = NAMESPACE[mod]
    ids = set()
    for path in sorted(bp.rglob("*.json")) + sorted(rp.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "minecraft:block" in data:
            ids.add(data["minecraft:block"]["description"]["identifier"])
    assert len(ids) == len(ASSETS[mod]), f"{mod}: missing block definitions"
    assert all(k.startswith(ns + ":") for k in ids)
    terrain = json.loads((rp / "textures/terrain_texture.json").read_text())
    for name in ASSETS[mod]:
        key = f"{ns}_{name}"
        assert key in terrain["texture_data"], key
        assert (rp / f"textures/blocks/{key}.png").is_file(), key
        for face in FACES.get(mod, {}).get(name, {}):
            face_key = f"{key}_{face}"
            assert face_key in terrain["texture_data"]
            assert (rp / f"textures/blocks/{face_key}.png").is_file()
    if mod == "aether":
        assert (bp / "scripts/biome_profiles.js").is_file()
    if mod == "bop":
        assert len(list((bp / "biomes").glob("*.json"))) >= len(BIOMES)
        assert (bp.parent / "worldgen_conversion_report.json").is_file()
        for name, spec in BIOMES.items():
            assert (bp / f"biomes/{name}.json").is_file()
            if spec["tree"]:
                assert (bp / f"features/{spec['tree']}_feature.json").is_file()
    assert (bp / "scripts/main.js").stat().st_size > 1000

def pack_zip(root: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                z.write(p, str(p.relative_to(root)))

def build(mod: str, output: Path) -> Path:
    bp, rp = output / mod / "BP", output / mod / "RP"
    if output.resolve() == ROOT.resolve() or output.resolve() == HERE.resolve():
        raise ValueError("Output must stay in a separate build directory")
    for d in (bp, rp):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    jwrite(bp / "manifest.json", manifest(mod, "BP"))
    jwrite(rp / "manifest.json", manifest(mod, "RP"))
    ns = NAMESPACE[mod]
    atlas = {"resource_pack_name": f"minizin_worlds_{mod}",
             "texture_name": "atlas.terrain", "texture_data": {}}
    translations = []
    for name, (relative, sound) in ASSETS[mod].items():
        key = f"{ns}_{name}"
        src = SOURCES[mod] / relative
        dst = rp / f"textures/blocks/{key}.png"
        copy_texture(src, dst, mod, name)
        atlas["texture_data"][key] = {"textures": f"textures/blocks/{key}"}
        for face, side_source in FACES.get(mod, {}).get(name, {}).items():
            face_key = f"{key}_{face}"
            face_target = rp / f"textures/blocks/{face_key}.png"
            copy_texture(SOURCES[mod] / side_source, face_target, mod, name)
            atlas["texture_data"][face_key] = {"textures": f"textures/blocks/{face_key}"}
        jwrite(bp / "blocks" / f"{name}.json", block_def(mod, name))
        translations.append(f"tile.{ns}:{name}.name={name.replace('_', ' ').title()}")
    jwrite(rp / "textures/terrain_texture.json", atlas)
    (rp / "texts").mkdir(parents=True, exist_ok=True)
    (rp / "texts/en_US.lang").write_text("\n".join(translations) + "\n", encoding="utf-8")
    (rp / "texts/pt_BR.lang").write_text("\n".join(translations) + "\n", encoding="utf-8")
    (rp / "texts/languages.json").write_text('["en_US", "pt_BR"]\n', encoding="utf-8")
    (bp / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / mod / "main.js", bp / "scripts/main.js")
    if mod == "aether":
        jwrite(rp / "models/blocks/portal.geo.json", geometry("portal"))
        jwrite(rp / "models/blocks/cross.geo.json", geometry("cross"))
        profiles = aether_biome_profiles()
        (bp / "scripts" / "biome_profiles.js").write_text(
            "/* Data from pinned Java Aether biome JSON; densities are adaptations. */\n"
            + "export const AETHER_BIOMES = " + json.dumps(profiles, ensure_ascii=False)
            + ";\n", encoding="utf-8")
        from aether.convert_structures import convert_all
        destination = bp / "structures" / "minizin_aether"
        results = convert_all(destination,
            {f"minizin_aether:{name}" for name in ASSETS["aether"]})
        print(f"Aether Java structures: {sum(x['status'].startswith('converted') for x in results)}/{len(results)} converted (audit in build/)")
        from aether.build_entities import build_all as build_entities
        print("Aether Java model -> Bedrock: ", build_entities(bp, rp))
        from aether.convert_loot import build_loot
        print("Aether original loot coverage:", build_loot(bp, rp, set(ASSETS["aether"])))
    else:
        jwrite(rp / "models/blocks/cross.geo.json", geometry("cross"))
        add_biomes(bp, rp)
        from bop.worldgen_full import build_all
        result = build_all(BIOME_SOURCE, bp, rp, set(ASSETS["bop"]),
                           tree_feature, flower_feature)
        print(f"BOP Java biome definitions: {result['source_count']} extracted; "
              f"native replacements: {result['coverage']}")
    validate_pack(bp, rp, mod)
    out = output / f"Minizin_Worlds_{mod}_v0.2.8.mcaddon"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in ("BP", "RP"):
            for p in sorted((output / mod / folder).rglob("*")):
                if p.is_file():
                    z.write(p, str(p.relative_to(output / mod)))
    return out

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod", choices=("aether", "bop", "both"), default="both")
    parser.add_argument("--output", type=Path, default=ROOT / "build/worlds")
    args = parser.parse_args()
    mods = ("aether", "bop") if args.mod == "both" else (args.mod,)
    args.output.mkdir(parents=True, exist_ok=True)
    for mod in mods:
        print(f"Built: {build(mod, args.output)}")
    print("Static checks completed; Android in-game validation is still required.")

if __name__ == "__main__":
    main()
