#!/usr/bin/env python3
"""Experimental read-only Bedrock inventory accessory panel for Minizin Work 0.3.8+.

Do not confuse eight drawn JSON-UI guides with eight native inventory slots.
Equip and retrieve items using the existing 8-slot server-UI Aether backend.
No new hotbar item is created; this tool never overwrites its input .mcaddon.

Usage:
  python tools/minizin_inventory_accessories_ui.py INPUT.mcaddon OUTPUT.mcaddon
Requirements: Python 3.11+, Pillow.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

MARKER = "MINIZIN_AETHER_INVENTORY_GUIDE_V1"
NAMES = ("AN1", "AN2", "COL", "LUV", "CAP", "ESC", "REL1", "REL2")
CATEGORIES = ("ring", "ring", "pendant", "gloves", "cape", "shield", "accessory", "accessory")


def encode(obj: object) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def parse(blob: bytes):
    return json.loads(blob.decode("utf-8-sig"))


def png(kind: str) -> bytes:
    """Small original glyph; no Java mod art is copied into public source."""
    im = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    gold, slate = (218, 187, 130, 255), (118, 153, 190, 255)
    if kind == "ring":
        d.ellipse((4, 5, 16, 17), outline=gold, width=3)
        d.polygon(((10, 1), (14, 5), (10, 9), (6, 5)), fill=slate)
    elif kind == "pendant":
        d.arc((2, 1, 17, 15), 0, 180, fill=gold, width=2)
        d.polygon(((10, 7), (15, 13), (10, 18), (5, 13)), fill=slate)
    elif kind == "gloves":
        d.polygon(((4, 9), (6, 7), (7, 11), (7, 3), (9, 2),
                   (10, 10), (11, 3), (13, 3), (13, 10),
                   (15, 6), (17, 8), (15, 17), (7, 18)), fill=gold)
    elif kind == "cape":
        d.polygon(((5, 2), (15, 2), (18, 18), (10, 15), (2, 18)), fill=slate)
        d.line(((5, 2), (15, 2)), fill=gold, width=2)
    elif kind == "shield":
        d.polygon(((3, 3), (17, 3), (16, 12), (10, 19), (4, 12)), fill=slate)
        d.line(((3, 3), (17, 3)), fill=gold, width=2)
    else:
        d.ellipse((2, 2, 18, 18), outline=gold, width=2)
        d.line(((10, 4), (10, 16)), fill=slate, width=2)
        d.line(((4, 10), (16, 10)), fill=slate, width=2)
    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()


def cell(index: int) -> dict:
    kind = CATEGORIES[index]
    return {f"slot_{index}": {
        "type": "panel", "size": [24, 27],
        "controls": [
            {"bg": {"type": "image", "size": [23, 23], "texture": "textures/ui/White",
                    "alpha": 0.14, "color": [0.25, 0.39, 0.54], "layer": 1}},
            {"glyph": {"type": "image", "size": [15, 15],
                       "texture": "textures/ui/minizin_accessories/" + kind,
                       "anchor_from": "top_middle", "anchor_to": "top_middle",
                       "offset": [0, 3], "layer": 2}},
            {"label": {"type": "label", "size": [24, 8], "text": NAMES[index],
                       "font_scale_factor": 0.7, "text_alignment": "center",
                       "anchor_from": "bottom_middle", "anchor_to": "bottom_middle",
                       "offset": [0, 0], "color": [0.95, 0.91, 0.79], "layer": 3}}
        ]
    }}


def ui_definition() -> dict:
    def row(start: int) -> dict:
        return {f"row_{start}": {"type": "stack_panel", "orientation": "horizontal",
                "size": [96, 27], "controls": [cell(i) for i in range(start, start + 4)]}}
    return {"namespace": "minizin_accessory_inventory",
            "overview": {"type": "panel", "size": [102, 85],
                         "anchor_from": "bottom_right", "anchor_to": "bottom_right",
                         "offset": [-5, -29], "layer": 3,
                         "controls": [
                             {"back": {"type": "image", "size": [102, 85],
                                       "texture": "textures/ui/Black", "alpha": 0.68}},
                             {"heading": {"type": "label", "text": "AETHER • ACESSÓRIOS",
                                           "size": [102, 12], "text_alignment": "center",
                                           "font_scale_factor": 0.75,
                                           "anchor_from": "top_middle", "anchor_to": "top_middle",
                                           "color": [0.98, 0.84, 0.60]}},
                             {"positions": {"type": "stack_panel", "orientation": "vertical",
                                             "size": [96, 54],
                                             "anchor_from": "top_middle", "anchor_to": "top_middle",
                                             "offset": [0, 15],
                                             "controls": [row(0), row(4)]}},
                             {"hint": {"type": "label", "text": "Use um acessório p/ equipar",
                                        "size": [102, 12], "text_alignment": "center",
                                        "font_scale_factor": 0.62,
                                        "anchor_from": "bottom_middle", "anchor_to": "bottom_middle",
                                        "color": [0.82, 0.85, 0.95]}}
                         ]}}


def patch_ui(rp: dict[str, bytes]) -> None:
    # Targets checked against Mojang bedrock-samples inventory_screen*.json.
    targets = (("ui/inventory_screen.json", "crafting", "recipe_inventory_screen_content"),
               ("ui/inventory_screen_pocket.json", "crafting_pocket",
                "recipe_inventory_screen_content_pocket"))
    reference = {"minizin_aether_panel@minizin_accessory_inventory.overview": {}}
    for filename, namespace, target in targets:
        doc = parse(rp[filename]) if filename in rp else {"namespace": namespace}
        if doc.get("namespace") != namespace:
            raise ValueError(f"Conflicting vanilla UI namespace in {filename}")
        item = doc.setdefault(target, {})
        modifications = item.setdefault("modifications", [])
        if not any(reference in mod.get("value", []) for mod in modifications):
            modifications.append({"array_name": "controls", "operation": "insert_back",
                                  "value": [reference]})
        rp[filename] = encode(doc)
    registry = parse(rp.get("ui/_ui_defs.json", b'{"ui_defs":[]}'))
    dest = "ui/minizin_aether_inventory.json"
    if dest not in registry.setdefault("ui_defs", []):
        registry["ui_defs"].append(dest)
    rp["ui/_ui_defs.json"] = encode(registry)
    rp[dest] = encode(ui_definition())
    for kind in set(CATEGORIES):
        rp["textures/ui/minizin_accessories/" + kind + ".png"] = png(kind)


def patch_backend(bp: dict[str, bytes]) -> None:
    path = "scripts/aether_equipment.js"
    if path not in bp:
        raise ValueError("Aether equipment runtime missing; do not generate decorative UI alone")
    src = bp[path].decode("utf-8")
    if MARKER in src:
        raise ValueError("Aether UI patch already applied")
    if 'minizin:aether_accessories_v2' not in src or 'const SLOTS=[' not in src:
        raise ValueError("This candidate does not have Work's 8-slot Aether backend")
    target = ('for(let index=0;index<COUNT;index++){const ref=slotFor(index);'
              'form.button(ref.slot.label+" "+(ref.ordinal+1)+": "+label(rows[index]));}')
    replacement = '''const MINIZIN_SLOT_ICONS={
        ring:"textures/ui/minizin_accessories/ring",
        pendant:"textures/ui/minizin_accessories/pendant",
        gloves:"textures/ui/minizin_accessories/gloves",
        cape:"textures/ui/minizin_accessories/cape",
        shield:"textures/ui/minizin_accessories/shield",
        accessory:"textures/ui/minizin_accessories/accessory"
    };
    for(let index=0;index<COUNT;index++){
        const ref=slotFor(index);
        form.button(ref.slot.label+" "+(ref.ordinal+1)+": "+label(rows[index]),
                    MINIZIN_SLOT_ICONS[ref.slot.id]);
    }'''
    if src.count(target) != 1:
        raise ValueError("Work menu changed: manual review required; refusing blind patch")
    bp[path] = ("// " + MARKER + "\n" + src.replace(target, replacement, 1)).encode("utf-8")


def read_zip(blob: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if archive.testzip():
            raise ValueError("Bad ZIP entry in mcpack")
        return {f.filename: archive.read(f) for f in archive.infolist() if not f.is_dir()}


def zipped(files: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content)
    return out.getvalue()


def build(source: Path, destination: Path) -> None:
    if not source.is_file() or source.resolve() == destination.resolve():
        raise ValueError("Input must exist; output must be a different file")
    if destination.exists():
        raise FileExistsError(destination)
    outer = read_zip(source.read_bytes())
    packs = {}
    for path, data in outer.items():
        if not path.endswith(".mcpack"):
            continue
        contents = read_zip(data)
        manifest = parse(contents["manifest.json"])
        module_types = {m.get("type") for m in manifest["modules"]}
        if "resources" in module_types:
            packs["RP"] = (path, contents, manifest)
        if "data" in module_types:
            packs["BP"] = (path, contents, manifest)
    if set(packs) != {"BP", "RP"}:
        raise ValueError("Expected exactly one BP and one RP in the integrated mcaddon")
    rp_path, rp, rman = packs["RP"]
    bp_path, bp, bman = packs["BP"]
    patch_backend(bp)
    patch_ui(rp)
    version = list(rman["header"]["version"])
    version[-1] += 1
    for files, manifest in ((rp, rman), (bp, bman)):
        manifest["header"]["version"] = version
        for module in manifest["modules"]:
            module["version"] = version
        files["manifest.json"] = encode(manifest)
    for dependency in bman.get("dependencies", []):
        if dependency.get("uuid") == rman["header"]["uuid"]:
            dependency["version"] = version
    bp["manifest.json"] = encode(bman)
    for group, files in (("RP", rp), ("BP", bp)):
        for path, content in files.items():
            if path.endswith(".json"):
                try:
                    parse(content)
                except (ValueError, UnicodeError) as err:
                    raise ValueError(f"{group}:{path}: {err}") from err
    assert len([x for x in rp if x.startswith("textures/ui/minizin_accessories/")]) == 6
    assert MARKER in bp["scripts/aether_equipment.js"].decode("utf-8")
    outer[rp_path], outer[bp_path] = zipped(rp), zipped(bp)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(zipped(outer))
    if zipfile.ZipFile(destination).testzip():
        destination.unlink(missing_ok=True)
        raise ValueError("Outer archive integrity failure")
    print(f"Build OK: {destination} ({destination.stat().st_size} bytes)")
    print("SHA-256:", hashlib.sha256(destination.read_bytes()).hexdigest())
    print("Limit: guide is VISUAL; equip/remove actions stay in existing Aether form")
    print("NOT tested on Android; requires user validation before integration")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    build(args.input, args.output)
