"""Generate Bedrock native custom biome *replacements* from all pinned BoP JSON.

This enables actual named biome generation on Minecraft Bedrock >=1.21.110.
It does not and cannot turn the original Java biome router and configured
features into Bedrock code. Original feature references and conversion coverage
are accounted for in build/worlds/bop/worldgen_conversion_report.json.

The End dimension does not have a documented minecraft:replace_biomes route:
End biomes are defined but intentionally not given fake Overworld placement.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path

FORMAT = "1.21.110"
# Vanilla candidate biomes for terrain/replacement families. These are
# deliberate native Bedrock approximations, not Java biome routing weights.
TARGETS = {
    "forest": ("forest", "birch_forest"),
    "jungle": ("jungle", "sparse_jungle"),
    "savanna": ("savanna", "savanna_plateau"),
    "taiga": ("taiga", "old_growth_pine_taiga"),
    "plains": ("plains", "sunflower_plains"),
    "mountains": ("stony_peaks", "windswept_hills"),
    "desert": ("desert",),
    "snow": ("snowy_plains", "snowy_taiga"),
    "swamp": ("swamp", "mangrove_swamp"),
    "beach": ("beach", "stony_shore"),
    "river": ("river",),
    "badlands": ("badlands", "eroded_badlands"),
}
# Do not represent unsupported End placements as generated Overworld biomes.
END = {"auroral_garden", "crystalline_chasm", "end_corruption", "end_flats",
       "end_reef", "end_wilds", "withered_abyss", "visceral_heap"}
NETHER = {"erupting_inferno", "volcanic_plains", "volcano", "glowing_grotto"}
# Source features include custom trees not all converted. Use only species
# whose original textures and Bedrock features the pack actually defines.
SPECIES = ("redwood", "fir", "magic", "jacaranda", "maple",
           "palm", "pine", "umbran")
FLOWERS = ("lavender", "glowflower", "white_lavender", "violet")
GROUP_HINTS = {
    "forest": ("forest", "woods", "woodland", "grove", "orchard", "rainforest",
               "rain", "bog", "overgrown", "jungle", "undergrowth", "fir",
               "clearing", "maple", "pine", "redwood", "mystic", "dead", "conifer"),
    "jungle": ("jungle", "tropics", "subtropics"),
    "savanna": ("savanna", "dryland", "scrubland", "shrubland"),
    "taiga": ("taiga", "tundra", "muskeg"),
    "desert": ("desert", "wasteland", "steppe", "dune", "cold_desert"),
    "snow": ("snow", "wintry"),
    "mountains": ("cliff", "crag", "highland", "rocky", "volcano"),
    "swamp": ("swamp", "marsh", "wetland", "floodplain", "bayou"),
    "beach": ("beach",),
    "river": ("river",),
    "badlands": ("canyon",),
}
SOURCE_ROOT = Path("common/src/generated/resources/data/biomesoplenty/worldgen/biome")


def group_for(name: str) -> str:
    # Specialized terrain categories precede the broader forest grouping.
    for kind in ("snow", "desert", "swamp", "jungle", "savanna",
                 "mountains", "beach", "river", "badlands", "taiga", "forest"):
        if any(h in name for h in GROUP_HINTS.get(kind, ())):
            return kind
    return "plains"


def native_replacement(name: str) -> dict | None:
    if name in END:
        return None
    if name in NETHER:
        return {"dimension": "minecraft:nether",
                "targets": ["nether_wastes", "basalt_deltas"],
                "amount": 0.11, "noise_frequency_scale": 15.0}
    group = group_for(name)
    targets = list(TARGETS[group])
    return {"dimension": "minecraft:overworld",
            "targets": targets, "amount": 0.10 if group == "plains" else 0.16,
            "noise_frequency_scale": 19.0}


def selected_feature(name: str, java_refs: list[str], available: set[str]) -> tuple[str | None, str | None]:
    context = " ".join([name] + java_refs).lower()
    species = next((s for s in SPECIES if s in context and f"{s}_log" in available
                    and f"{s}_leaves" in available), None)
    flower = next((f for f in FLOWERS if f in context and f in available), None)
    return species, flower


def convert_biome(name: str, src: dict) -> dict:
    effects = src.get("effects", {})
    original_refs = [str(x) for group in src.get("features", []) for x in group]
    rule = native_replacement(name)
    group = group_for(name)
    components = {
        "minecraft:climate": {
            "temperature": float(src["temperature"]),
            "downfall": float(src["downfall"]),
            "snow_accumulation": [0.0, 0.0], "ash": 0,
            "red_spores": 0, "white_ash": 0,
        },
        "minecraft:overworld_height": {"noise_type": {
            "mountains": "highlands", "desert": "lowlands",
            "plains": "lowlands", "beach": "lowlands",
        }.get(group, "default")},
        "minecraft:surface_parameters": {
            "sea_floor_depth": 7,
            "sea_floor_material": "minecraft:gravel",
            "foundation_material": "minecraft:stone",
            "mid_material": "minecraft:dirt",
            "top_material": ("minecraft:sand" if group in ("desert", "beach")
                             else "minecraft:snow" if group == "snow"
                             else "minecraft:grass_block"),
            "sea_material": "minecraft:water",
        },
        "minecraft:tags": {
            "tags": ["minizin_bop", name, "no_legacy_worldgen",
                     "nether" if name in NETHER else
                     "the_end" if name in END else "overworld"]},
    }
    if rule:
        components["minecraft:replace_biomes"] = {"replacements": [rule]}
    return {
        "biome": {"format_version": FORMAT,
                  "minecraft:biome": {
                      "description": {"identifier": f"minizin_bop:{name}"},
                      "components": components}},
        "client": {"format_version": FORMAT,
                   "minecraft:client_biome": {
                       "description": {"identifier": f"minizin_bop:{name}"},
                       "components": {
                           "minecraft:water_appearance": {
                               "surface_color": effects.get("water_color", "#3f76e4"),
                               "surface_opacity": 0.6},
                           **({"minecraft:grass_appearance": {"color": effects["grass_color"]}}
                              if "grass_color" in effects else {}),
                           **({"minecraft:foliage_appearance": {"color": effects["foliage_color"]}}
                              if "foliage_color" in effects else {}),
                       }}},
        "source_feature_refs": original_refs,
        "placement": rule,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def decorate_rule(name: str, feature: str, attempts: int) -> dict:
    return {"format_version": FORMAT, "minecraft:feature_rules": {
        "description": {"identifier": f"minizin_bop:{name}_{feature}_native",
                        "places_feature": f"minizin_bop:{feature}_feature"},
        "conditions": {"placement_pass": "surface_pass",
                       "minecraft:biome_filter": {
                           "test": "has_biome_tag", "operator": "==",
                           "value": name}},
        "distribution": {"iterations": attempts,
                         "x": {"distribution": "uniform", "extent": [0, 15]},
                         "y": "query.heightmap(variable.worldx, variable.worldz)",
                         "z": {"distribution": "uniform", "extent": [0, 15]}}}}


def build_all(source: Path, bp: Path, rp: Path, available: set[str],
              tree_factory, flower_factory) -> dict:
    inputs = sorted(source.glob("*.json"))
    if not inputs:
        raise FileNotFoundError(f"No upstream biome JSON under {source}")
    coverage = Counter()
    rows = []
    species_found, flowers_found = set(), set()
    for p in inputs:
        src = json.loads(p.read_text(encoding="utf-8"))
        name = p.stem
        converted = convert_biome(name, src)
        write_json(bp / "biomes" / f"{name}.json", converted["biome"])
        write_json(rp / "biomes_client" / f"{name}.biome_client.json", converted["client"])
        species, flower = selected_feature(name, converted["source_feature_refs"], available)
        rule = converted["placement"]
        dimension = rule["dimension"] if rule else "not_supported_end"
        coverage[dimension] += 1
        # An unsupported End replacement must not accidentally cause vegetation
        # in vanilla Overworld biomes.
        if rule:
            if species:
                species_found.add(species)
                write_json(bp / "feature_rules" / f"{name}_{species}_native.json",
                           decorate_rule(name, species, 3))
            if flower:
                flowers_found.add(flower)
                write_json(bp / "feature_rules" / f"{name}_{flower}_native.json",
                           decorate_rule(name, flower, 7))
        rows.append({"java_id": f"biomesoplenty:{name}",
                     "bedrock_id": f"minizin_bop:{name}",
                     "dimension": dimension,
                     "replacement": rule,
                     "java_feature_refs": converted["source_feature_refs"],
                     "native_tree": species, "native_flower": flower,
                     "java_feature_coverage": "partial" if species or flower else "unported"})
    for sp in sorted(species_found):
        write_json(bp / "features" / f"{sp}_feature.json", tree_factory(sp))
    for flower in sorted(flowers_found):
        write_json(bp / "features" / f"{flower}_feature.json", flower_factory(flower))
    report = {"source_count": len(inputs), "coverage": dict(coverage),
              "original_java_worldgen_equivalence": False, "biomes": rows}
    write_json(bp.parent / "worldgen_conversion_report.json", report)
    native = {
        r["bedrock_id"]: {"tree": r["native_tree"],
                          "flower": r["native_flower"],
                          "dimension": r["dimension"]}
        for r in rows if r["replacement"] is not None
    }
    script = bp / "scripts/native_biomes.js"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("/* Derived from pinned Java BiomesOPlenty worldgen; engine replacement is Bedrock-native. */\\n".replace("\\\\n", "\\n")
                      + "export const NATIVE_BOP = " + json.dumps(native, ensure_ascii=False)
                      + ";\\n".replace("\\\\n", "\\n"), encoding="utf-8")
    return report
