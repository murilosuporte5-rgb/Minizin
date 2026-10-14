#!/usr/bin/env python3
"""Overlay the source-built Aether world pack into the combined-pack layout.

The isolated world builder uses pack-local paths (``textures/blocks`` and
``loot_tables/blocks``).  The combined pack namespaces every mod below
``aether_full_v3``.  Keeping this translation explicit prevents a valid
standalone pack from becoming invisible or unlootable after combination.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


PREFIX = "aether_full_v3"


def rewrite_strings(value: Any, *, block: bool = False) -> Any:
    if isinstance(value, list):
        return [rewrite_strings(item, block=block) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_strings(item, block=block) for key, item in value.items()}
    if not isinstance(value, str):
        return value
    if value.startswith("loot_tables/") and not value.startswith(f"loot_tables/{PREFIX}/"):
        return f"loot_tables/{PREFIX}/{value.removeprefix('loot_tables/')}"
    if value.startswith("textures/entity/"):
        return f"textures/{PREFIX}/{value.removeprefix('textures/')}"
    if block and value and not value.startswith(f"{PREFIX}_"):
        return f"{PREFIX}_{value}"
    return value


def rewrite_bp(path: Path, destination: Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    is_block = "minecraft:block" in document
    document = rewrite_strings(document, block=False)
    if is_block:
        instances = document["minecraft:block"].get("components", {}).get("minecraft:material_instances", {})
        for material in instances.values():
            if isinstance(material, dict) and isinstance(material.get("texture"), str):
                texture = material["texture"]
                if not texture.startswith(f"{PREFIX}_"):
                    material["texture"] = f"{PREFIX}_{texture}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rewrite_rp(path: Path, destination: Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    document = rewrite_strings(document)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def overlay_registry(source: Path, destination: Path, *, item: bool) -> None:
    document = json.loads(source.read_text(encoding="utf-8"))
    current = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else {
        "resource_pack_name": "Minizin combined",
        "texture_name": "atlas.items" if item else "atlas.terrain",
        "texture_data": {},
    }
    textures = current.setdefault("texture_data", {})
    for key, value in document.get("texture_data", {}).items():
        entry = dict(value) if isinstance(value, dict) else {"textures": value}
        texture_path = entry.get("textures")
        if isinstance(texture_path, str) and texture_path.startswith("textures/"):
            if not texture_path.startswith(f"textures/{PREFIX}/"):
                entry["textures"] = f"textures/{PREFIX}/{texture_path.removeprefix('textures/')}"
        textures[f"{PREFIX}_{key}" if not key.startswith(f"{PREFIX}_") else key] = entry
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def overlay_flipbook(source: Path, destination: Path) -> None:
    """Merge the Aether flipbook into the combined RP root catalog.

    Bedrock discovers this catalog at RP/textures/flipbook_texture.json, not
    below a mod namespace directory. Every asset path and atlas key still has
    to use the combined-pack prefix used by terrain_texture.json.
    """
    incoming = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(incoming, list):
        raise ValueError(f"Invalid flipbook catalog: {source}")
    current = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else []
    if not isinstance(current, list):
        raise ValueError(f"Invalid combined flipbook catalog: {destination}")
    merged = [entry for entry in current if not (
        isinstance(entry, dict) and str(entry.get("atlas_tile", "")).startswith(f"{PREFIX}_")
    )]
    for entry in incoming:
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid flipbook entry in {source}: {entry!r}")
        converted = dict(entry)
        path = converted.get("flipbook_texture")
        if isinstance(path, str) and path.startswith("textures/"):
            converted["flipbook_texture"] = f"textures/{PREFIX}/{path.removeprefix('textures/')}"
        tile = converted.get("atlas_tile")
        if isinstance(tile, str) and not tile.startswith(f"{PREFIX}_"):
            converted["atlas_tile"] = f"{PREFIX}_{tile}"
        variant = converted.get("atlas_tile_variant")
        if isinstance(variant, str) and not variant.startswith(f"{PREFIX}_"):
            converted["atlas_tile_variant"] = f"{PREFIX}_{variant}"
        merged.append(converted)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def target_for(role: str, relative: Path, output: Path) -> Path | None:
    if relative.name == "manifest.json":
        return None
    parts = relative.parts
    if len(parts) < 2:
        return None
    category, rest = parts[0], Path(*parts[1:])
    if role == "RP" and category == "models":
        if len(rest.parts) < 2:
            return None
        return output / role / "models" / rest.parts[0] / PREFIX / Path(*rest.parts[1:])
    return output / role / category / PREFIX / rest


def overlay(combined_source: Path, world_pack: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"Choose a fresh output folder: {output}")
    shutil.copytree(combined_source, output)
    for role in ("BP", "RP"):
        source_root = world_pack / role
        for path in source_root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(source_root)
            if relative.as_posix() == "manifest.json":
                continue
            if role == "RP" and relative.as_posix() == "textures/terrain_texture.json":
                overlay_registry(path, output / "RP/textures/terrain_texture.json", item=False)
                continue
            if role == "RP" and relative.as_posix() == "textures/item_texture.json":
                overlay_registry(path, output / "RP/textures/item_texture.json", item=True)
                continue
            if role == "RP" and relative.as_posix() == "textures/flipbook_texture.json":
                overlay_flipbook(path, output / "RP/textures/flipbook_texture.json")
                continue
            destination = target_for(role, relative, output)
            if destination is None:
                continue
            if path.suffix.lower() == ".json":
                (rewrite_bp if role == "BP" else rewrite_rp)(path, destination)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--combined-source", type=Path, required=True)
    parser.add_argument("--world-pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    overlay(args.combined_source.resolve(), args.world_pack.resolve(), args.output.resolve())
    print(json.dumps({
        "output": str(args.output.resolve()),
        "world_pack": str(args.world_pack.resolve()),
        "prefix": PREFIX,
    }))


if __name__ == "__main__":
    main()
