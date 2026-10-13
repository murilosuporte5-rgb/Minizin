#!/usr/bin/env python3
"""Overlay a source-built world pack into the combined-pack layout.

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


def rewrite_bp(path: Path, destination: Path, item_icons: set[str] | None = None) -> None:
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
    item = document.get("minecraft:item")
    if item:
        components = item.get("components", {})
        icon = components.get("minecraft:icon")
        if isinstance(icon, str) and icon in (item_icons or set()):
            components["minecraft:icon"] = f"{PREFIX}_{icon}"
        elif isinstance(icon, dict):
            textures = icon.get("textures", {})
            if isinstance(textures, dict) and textures.get("default") in (item_icons or set()):
                textures["default"] = f"{PREFIX}_{textures['default']}"
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


def overlay(combined_source: Path, world_pack: Path, output: Path, prefix: str = PREFIX) -> None:
    global PREFIX
    if prefix not in ("aether_full_v3", "bop_full_v3"):
        raise ValueError(f"Unsupported world pack prefix: {prefix}")
    PREFIX = prefix
    if output.exists():
        raise ValueError(f"Choose a fresh output folder: {output}")
    shutil.copytree(combined_source, output)
    categories = {"blocks": "minecraft:block", "items": "minecraft:item",
                  "entities": "minecraft:entity"}
    existing = {}
    for category, root_key in categories.items():
        for candidate in (output / "BP" / category).rglob("*.json"):
            document = json.loads(candidate.read_text(encoding="utf-8"))
            identifier = document.get(root_key, {}).get("description", {}).get("identifier")
            if identifier:
                existing[(category, identifier)] = str(candidate.relative_to(output))
    overlaps = []
    registry_path = world_pack / "RP/textures/item_texture.json"
    item_icons = (set(json.loads(registry_path.read_text(encoding="utf-8"))
                      .get("texture_data", {})) if registry_path.exists() else set())
    for role in ("BP", "RP"):
        source_root = world_pack / role
        for path in source_root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(source_root)
            if relative.as_posix() == "manifest.json":
                continue
            if role == "BP" and relative.parts[0] in categories and path.suffix == ".json":
                category = relative.parts[0]
                source_document = json.loads(path.read_text(encoding="utf-8"))
                identifier = source_document.get(categories[category], {}).get("description", {}).get("identifier")
                if identifier and (category, identifier) in existing:
                    overlaps.append({"identifier": identifier, "kept": existing[(category, identifier)],
                                     "skipped": str(relative)})
                    continue
                if identifier:
                    existing[(category, identifier)] = str(relative)
            if role == "RP" and relative.as_posix() == "textures/terrain_texture.json":
                overlay_registry(path, output / "RP/textures/terrain_texture.json", item=False)
                continue
            if role == "RP" and relative.as_posix() == "textures/item_texture.json":
                overlay_registry(path, output / "RP/textures/item_texture.json", item=True)
                continue
            destination = target_for(role, relative, output)
            if destination is None:
                continue
            if role == "BP" and relative.as_posix() == "scripts/main.js" and destination.exists():
                previous = destination.read_text(encoding="utf-8")
                incoming = path.read_text(encoding="utf-8")
                # The repair stage has already wired Freezer and Incubator.
                # Replacing main.js must retain those imports, or the machines
                # remain registered as files but never execute.
                imports = [line for line in previous.splitlines()
                           if line.strip().startswith('import ') and line not in incoming]
                destination.write_text(incoming.rstrip() + "\n" + "\n".join(imports) + "\n",
                                       encoding="utf-8")
            elif path.suffix.lower() == ".json":
                if role == "BP":
                    rewrite_bp(path, destination, item_icons)
                else:
                    rewrite_rp(path, destination)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
    entry = output / "BP/scripts/main.js"
    line = f'import "./{prefix}/main.js";'
    contents = entry.read_text(encoding="utf-8")
    if line not in contents:
        entry.write_text(contents.rstrip() + "\n" + line + "\n", encoding="utf-8")
    if prefix == "aether_full_v3":
        manifest = output / "BP/manifest.json"
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        for dep in doc.get("dependencies", []):
            if dep.get("module_name") == "@minecraft/server":
                dep["version"] = "beta"
        manifest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / f"OVERLAY_CONFLICTS_{prefix}.json").write_text(
        json.dumps(overlaps, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--combined-source", type=Path, required=True)
    parser.add_argument("--world-pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prefix", choices=("aether_full_v3", "bop_full_v3"), default=PREFIX)
    args = parser.parse_args()
    overlay(args.combined_source.resolve(), args.world_pack.resolve(), args.output.resolve(), args.prefix)
    print(json.dumps({
        "output": str(args.output.resolve()),
        "world_pack": str(args.world_pack.resolve()),
        "prefix": PREFIX,
    }))


if __name__ == "__main__":
    main()
