"""Convert Java Aether boss/dungeon loot tables using only registered Bedrock items.

Java functions/conditions that cannot be represented are audited and omitted,
not silently reinterpreted. Protected PNGs are copied only into ignored build/.
"""
from __future__ import annotations
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JAVA_LOOT = ROOT / "mods/41-the-aether/upstream/src/generated/resources/data/aether/loot_table"
ITEM_TEXTURES = ROOT / "mods/41-the-aether/upstream/src/main/resources/assets/aether/textures/item"
ITEM_SOURCE = {
    "bronze_dungeon_key": "miscellaneous/bronze_dungeon_key.png",
    "silver_dungeon_key": "miscellaneous/silver_dungeon_key.png",
    "gold_dungeon_key": "miscellaneous/gold_dungeon_key.png",
    "zanite_gemstone": "materials/zanite_gemstone.png",
    "golden_amber": "materials/golden_amber.png",
    "ambrosium_shard": "materials/ambrosium_shard.png",
    "life_shard": "miscellaneous/life_shard.png",
}
LOOT_IDS = ("slider", "valkyrie_queen", "sun_spirit")
CHEST_TIERS = ("bronze", "silver", "gold")


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def item_name(original: str, available_blocks: set[str]) -> str | None:
    if original.startswith("minecraft:"):
        return original
    if not original.startswith("aether:"):
        return None
    local = original.split(":", 1)[1]
    if local in ITEM_SOURCE or local in available_blocks:
        return f"minizin_aether:{local}"
    return None


def count_value(value):
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, dict) and "min" in value and "max" in value:
        return {"min": int(value["min"]), "max": int(value["max"])}
    return None


def transform_pool(pool: dict, available_blocks: set[str], known_tables: set[str],
                   lost: Counter) -> dict | None:
    entries = []
    for entry in pool.get("entries", []):
        t = entry.get("type")
        if t == "minecraft:item":
            original = entry.get("name", "")
            mapped = item_name(original, available_blocks)
            if not mapped:
                lost["item:" + original] += 1
                continue
            dest = {"type": "item", "name": mapped, "weight": int(entry.get("weight", 1))}
            functions = []
            for func in entry.get("functions", []):
                name = func.get("function", "")
                if name == "minecraft:set_count":
                    count = count_value(func.get("count"))
                    if count is not None:
                        functions.append({"function": "set_count", "count": count})
                    else:
                        lost["function_count:" + original] += 1
                else:
                    lost["function:" + name] += 1
            if functions:
                dest["functions"] = functions
            if entry.get("conditions"):
                # Unsupported Java predicates are not executed by Bedrock.
                # Omit entire entry to avoid unintended guaranteed drops.
                lost["conditional:" + original] += 1
                continue
            entries.append(dest)
        elif t == "minecraft:loot_table":
            ref = entry.get("value", "")
            if ref not in known_tables:
                lost["missing_nested_table:" + ref] += 1
                continue
            new = {"type": "loot_table",
                   "name": "loot_tables/minizin_aether/" + ref.removeprefix("aether:") + ".json",
                   "weight": int(entry.get("weight", 1))}
            entries.append(new)
        else:
            lost["entry_type:" + str(t)] += 1
    if not entries:
        return None
    rolls = count_value(pool.get("rolls", 1))
    if rolls is None:
        lost["roll_expression"] += 1
        return None
    result = {"rolls": rolls, "entries": entries}
    if pool.get("conditions"):
        lost["pool_conditions"] += 1
        return None
    return result


def original_tables() -> dict[str, dict]:
    results = {}
    for p in sorted(JAVA_LOOT.glob("entities/*.json")) + sorted(JAVA_LOOT.glob("chests/dungeon/**/*.json")):
        rel = p.relative_to(JAVA_LOOT).with_suffix("")
        results[f"aether:{rel.as_posix()}"] = json.loads(p.read_text(encoding="utf-8"))
    return results


def build_items(bp: Path, rp: Path) -> None:
    atlas = {"resource_pack_name": "minizin_aether_loot",
             "texture_name": "atlas.items", "texture_data": {}}
    labels = []
    for name, source in ITEM_SOURCE.items():
        path = ITEM_TEXTURES / source
        if not path.is_file():
            raise FileNotFoundError(f"Missing original Java loot item texture: {path}")
        key = f"minizin_aether_{name}"
        target = rp / "textures/items" / (key + ".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        atlas["texture_data"][key] = {"textures": f"textures/items/{key}"}
        is_key = name.endswith("_dungeon_key")
        component = {"minecraft:icon": {"textures": {"default": key}}, "minecraft:max_stack_size": 1 if is_key else 64,
                     "minecraft:display_name": {"value": name.replace("_", " ").title()}}
        dump(bp / "items" / (name + ".json"), {
            "format_version": "1.21.80",
            "minecraft:item": {"description": {
                "identifier": "minizin_aether:" + name,
                "menu_category": {"category": "items"}}, "components": component}})
        labels.append(f"item.minizin_aether:{name}.name={name.replace('_', ' ').title()}")
    dump(rp / "textures" / "item_texture.json", atlas)
    return None


def flatten_rewards(table_id: str, tables: dict[str, dict],
                    available: set[str], seen: set[str] | None = None) -> list[dict]:
    seen = set() if seen is None else seen
    if table_id in seen or table_id not in tables:
        return []
    seen = seen | {table_id}
    rewards = []
    for pool in tables[table_id].get("pools", []):
        for entry in pool.get("entries", []):
            if entry.get("type") == "minecraft:item":
                target = item_name(entry.get("name", ""), available)
                if target and not entry.get("conditions"):
                    c = 1
                    for f in entry.get("functions", []):
                        if f.get("function") == "minecraft:set_count":
                            c = count_value(f.get("count", 1)) or 1
                    rewards.append({"name": target, "weight": int(entry.get("weight", 1)),
                                    "count": c})
            elif entry.get("type") == "minecraft:loot_table":
                rewards.extend(flatten_rewards(entry.get("value", ""), tables, available, seen))
    return rewards


def build_loot(bp: Path, rp: Path, available: set[str]) -> dict:
    build_items(bp, rp)
    tables = original_tables()
    losses = Counter()
    converted, empty = 0, []
    for identifier, data in tables.items():
        content = {"pools": []}
        for pool in data.get("pools", []):
            transformed = transform_pool(pool, available, set(tables), losses)
            if transformed:
                content["pools"].append(transformed)
        if not content["pools"]:
            empty.append(identifier)
        target = bp / "loot_tables/minizin_aether" / (
            identifier.removeprefix("aether:") + ".json")
        dump(target, content)
        converted += 1
    rewards = {}
    for tier in CHEST_TIERS:
        key = f"aether:chests/dungeon/{tier}/{tier}_dungeon_reward"
        rewards[tier] = flatten_rewards(key, tables, available)
    (bp / "scripts").mkdir(parents=True, exist_ok=True)
    (bp / "scripts/dungeon_loot.js").write_text(
        "/* Original weighted Java reward entries, only registered Bedrock items retained. */\n"
        "export const DUNGEON_REWARDS = " + json.dumps(rewards, ensure_ascii=False)
        + ";\n", encoding="utf-8")
    report = {
        "source_tables": len(tables), "converted_tables": converted,
        "no_supported_entries": empty, "losses": dict(losses),
        "available_rewards_per_tier": {k: len(v) for k, v in rewards.items()},
        "original_java_loot_parity": False,
    }
    dump(bp.parent / "loot_conversion_report.json", report)
    return report
