#!/usr/bin/env python3
"""Convert pinned Java Aether structure NBT into *local-only* Bedrock structures.

Reads the actual Java .nbt sources and writes little-endian .mcstructure files.
Does not redistribute third-party originals or assert that block states,
processors, jigsaw connections, mob spawns or dungeon mechanics were ported.

Requirements: pip install nbtlib numpy
"""
from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Any

import nbtlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JAVA_STRUCTURES = ROOT / "mods/41-the-aether/upstream/src/main/resources/data/aether/structure"
# Minecraft add-on dimensions can only display registered blocks. Avoid
# fabricating names for new blocks not declared in the world pack.
VOID_BLOCKS = {"minecraft:structure_void", "minecraft:jigsaw", "aether:structure_void"}
WORLD_PREFIX = "minizin_aether"
MAX_VOLUME = 220_000
# Original names not available in the prototype are not silently painted as
# generic stone. They are documented and skipped (no Java-equivalence claim).
AETHER_ALIASES = {
    "aether:aether_grass_block": "minizin_aether:aether_grass",
    "aether:grass_block": "minizin_aether:aether_grass",
    "aether:holystone": "minizin_aether:holystone",
    "aether:holystone_bricks": "minizin_aether:holystone_bricks",
    "aether:skyroot_log": "minizin_aether:skyroot_log",
    "aether:skyroot_leaves": "minizin_aether:skyroot_leaves",
    "aether:angelic_stone": "minizin_aether:angelic_stone",
    "aether:light_angelic_stone": "minizin_aether:light_angelic_stone",
    "aether:hellfire_stone": "minizin_aether:hellfire_stone",
    "aether:light_hellfire_stone": "minizin_aether:light_hellfire_stone",
    "aether:carved_stone": "minizin_aether:carved_stone",
    "aether:sentry_stone": "minizin_aether:sentry_stone",
    "aether:pillar": "minizin_aether:pillar",
    "aether:mossy_holystone": "minizin_aether:mossy_holystone",
    "aether:skyroot_planks": "minizin_aether:skyroot_planks",
    "aether:ambrosium_ore": "minizin_aether:ambrosium_ore",
    "aether:zanite_ore": "minizin_aether:zanite_ore",
    "aether:icestone": "minizin_aether:icestone",
    "aether:quicksoil": "minizin_aether:quicksoil",
}
# Minecraft Java and Bedrock states are not universally compatible.
# Explicitly retain only validated equivalences for custom orientation.
# Unknown states are dropped from *all* blocks rather than emitting invalid
# data; conversion report records them for follow-up.
BEDROCK_STATE_MAP: dict[str, str] = {}
BLOCK_VERSION = 18168865


def tlist(tag, values):
    return nbtlib.List[tag](values)


def translate_block(java_id: str, registered: set[str]) -> str | None:
    if java_id in VOID_BLOCKS:
        return None
    if java_id in AETHER_ALIASES:
        target = AETHER_ALIASES[java_id]
        return target if target in registered else None
    if java_id.startswith("aether:"):
        original_name = java_id.split(":", 1)[1]
        target = f"minizin_aether:{original_name}"
        return target if target in registered else None
    if java_id.startswith("minecraft:"):
        # Compatibility requires client validation; vanilla Java identifiers
        # that changed in Bedrock remain visible in conversion report.
        return java_id
    return None


def convert_file(source: Path, output: Path, registered: set[str]) -> dict[str, Any]:
    java = nbtlib.load(source)
    dimensions = [int(n) for n in java["size"]]
    if len(dimensions) != 3 or not all(0 < d <= 384 for d in dimensions):
        raise ValueError(f"Invalid structure dimensions {source}: {dimensions}")
    sx, sy, sz = dimensions
    volume = sx * sy * sz
    if volume > MAX_VOLUME:
        raise ValueError(f"Structure too large for bounded mobile conversion: {source} ({volume})")
    raw_palette = java["palette"]
    converted_palette: list[nbtlib.Compound] = []
    palette_indices: list[int] = []
    mapped = collections.Counter()
    omitted = collections.Counter()
    dropped_states = collections.Counter()
    raw_state_keys = collections.Counter()
    for p in raw_palette:
        java_id = str(p["Name"])
        target = translate_block(java_id, registered)
        if target is None:
            palette_indices.append(-1)
            omitted[java_id] += 1
            continue
        properties = p.get("Properties", {})
        if properties:
            raw_state_keys.update(str(x) for x in properties)
            dropped_states.update(f"{java_id}:{k}" for k in properties)
        permutation = nbtlib.Compound({
            "name": nbtlib.String(target),
            "states": nbtlib.Compound(),
            "version": nbtlib.Int(BLOCK_VERSION),
        })
        palette_indices.append(len(converted_palette))
        converted_palette.append(permutation)
        mapped[target] += 1

    if not converted_palette:
        return {"source": str(source.relative_to(JAVA_STRUCTURES)), "status": "skipped",
                "reason": "No representable blocks", "size": dimensions,
                "omitted": dict(omitted)}

    data = [-1] * volume
    tile_entities = 0
    for block in java["blocks"]:
        x, y, z = (int(v) for v in block["pos"])
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"Invalid block coordinate in {source}: {(x, y, z)}")
        old_index = int(block["state"])
        if not (0 <= old_index < len(palette_indices)):
            raise ValueError(f"Invalid palette index {old_index} in {source}")
        linear = (x * sy + y) * sz + z
        data[linear] = palette_indices[old_index]
        if "nbt" in block:
            tile_entities += 1
    blank = sum(1 for n in data if n == -1)
    total = sum(1 for n in data if n >= 0)
    output.parent.mkdir(parents=True, exist_ok=True)
    structure = nbtlib.File({
        "format_version": nbtlib.Int(1),
        "size": tlist(nbtlib.Int, list(map(nbtlib.Int, dimensions))),
        "structure_world_origin": tlist(nbtlib.Int, [nbtlib.Int(0)] * 3),
        "structure": nbtlib.Compound({
            "block_indices": tlist(nbtlib.List[nbtlib.Int], [
                tlist(nbtlib.Int, [nbtlib.Int(n) for n in data]),
                tlist(nbtlib.Int, [nbtlib.Int(-1) for _ in data]),
            ]),
            "entities": tlist(nbtlib.Compound, []),
            "palette": nbtlib.Compound({
                "default": nbtlib.Compound({
                    "block_palette": tlist(nbtlib.Compound, converted_palette),
                    "block_position_data": nbtlib.Compound(),
                })
            }),
        }),
    })
    structure.save(output, gzipped=False, byteorder="little")
    reopened = nbtlib.load(output, gzipped=False, byteorder="little")
    assert list(map(int, reopened["size"])) == dimensions
    assert len(reopened["structure"]["block_indices"][0]) == volume
    assert len(reopened["structure"]["palette"]["default"]["block_palette"]) == len(converted_palette)
    return {
        "source": str(source.relative_to(JAVA_STRUCTURES)),
        "status": "converted_with_omissions" if omitted or dropped_states else "converted",
        "size": dimensions, "volume": volume, "placed": total, "omitted_positions": blank,
        "registered_palette": len(mapped), "omitted_palette": dict(omitted),
        "dropped_states": dict(dropped_states),
        "tile_entities_not_ported": tile_entities,
        "entities_not_ported": len(java.get("entities", [])),
        "output": str(output),
    }


def convert_all(output: Path, registered: set[str], max_templates: int = 0) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    templates: list[dict] = []
    sources = sorted(p for group in ("bronze_dungeon", "silver_dungeon", "gold_dungeon")
                     for p in (JAVA_STRUCTURES / group).glob("*.nbt"))
    if not sources:
        raise FileNotFoundError(f"No original Java Aether dungeon templates in {JAVA_STRUCTURES}")
    for path in sources[:max_templates or None]:
        relative = path.relative_to(JAVA_STRUCTURES)
        dest = output / relative.with_suffix(".mcstructure")
        try:
            result = convert_file(path, dest, registered)
        except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
            result = {"source": str(relative), "status": "skipped", "reason": str(error)}
        result["bedrock_id"] = f"{WORLD_PREFIX}:{relative.with_suffix('').as_posix()}"
        templates.append(result)
    (output / "conversion_report.json").write_text(
        json.dumps({"source_root": str(JAVA_STRUCTURES),
                    "block_version": BLOCK_VERSION,
                    "format": "mcstructure/little-endian",
                    "engine_verified": False, "templates": templates},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    return templates


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "build/worlds/aether/BP/structures/minizin_aether")
    p.add_argument("--registered", nargs="*", default=["holystone", "holystone_bricks", "carved_stone",
                     "angelic_stone", "light_angelic_stone", "hellfire_stone",
                     "light_hellfire_stone", "pillar", "sentry_stone"])
    a = p.parse_args()
    names = {f"minizin_aether:{x}" for x in a.registered}
    print(json.dumps(convert_all(a.output, names), indent=2))
