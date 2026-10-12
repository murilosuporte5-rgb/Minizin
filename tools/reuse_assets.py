#!/usr/bin/env python3
"""Source asset audit and Bedrock geometry staging. Python 3.10+; stdlib only."""
from __future__ import annotations
import argparse, csv, json, shutil, uuid, zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MODS = ["15-waystones", "16-ice-and-fire", "19-biomes-o-plenty", "33-mca-reborn",
        "34-carry-on", "41-the-aether", "42-alexs-caves", "43-cataclysm",
        "44-mowzies-mobs", "53-immersive-portals", "54-rftools", "55-origins",
        "57-xaeros-minimap", "58-distant-horizons"]

def category(name: str):
    p = name.lower().replace("\\", "/")
    if p.endswith(".bbmodel"): return "blockbench_source"
    if p.endswith(".geo.json"): return "bedrock_geometry"
    if p.endswith(".animation.json"): return "animation_json"
    if p.endswith((".obj", ".mtl", ".blend", ".fbx", ".glb", ".gltf")): return "mesh_source"
    if p.endswith(".java") and ("/client/model/" in p or "/client/models/" in p): return "java_entity_model"
    if p.endswith(".class") and "/client/model/" in p: return "compiled_java_model"
    if p.endswith(".json") and "/models/" in p: return "java_block_item_model"
    if p.endswith((".png", ".jpg", ".tga", ".jpeg")) and "/textures/" in p: return "texture"
    if p.endswith((".ogg", ".wav")): return "sound"
    if p.endswith((".nbt", ".schem", ".schematic", ".mcstructure")): return "structure"
    if p.endswith(".json") and "/worldgen/" in p: return "worldgen"
    return None

def inventory(path: Path):
    if not path.exists(): return []
    if path.is_file():
        if not zipfile.is_zipfile(path): raise ValueError("Expected source folder or Java mod .jar/.zip")
        with zipfile.ZipFile(path) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir()]
    else:
        names = [p.relative_to(path).as_posix() for p in path.rglob("*")
                 if p.is_file() and ".git" not in p.relative_to(path).parts]
    return [{"file": name, "type": kind} for name in sorted(names)
            if (kind := category(name)) is not None]

def scan(args):
    if args.source and not args.mod: raise SystemExit("--source requires --mod")
    results, rows = {}, []
    for mod in ([args.mod] if args.mod else MODS):
        source = Path(args.source) if args.source else ROOT / "mods" / mod / "upstream"
        assets = inventory(source)
        counts = dict(Counter(it["type"] for it in assets))
        results[mod] = {"source": str(source), "present": source.exists(),
                        "counts": counts, "total": len(assets)}
        rows += [{"mod": mod, **it} for it in assets]
        print(f"{mod}: {len(assets)} categorized files; {counts}" if source.exists()
              else f"{mod}: unavailable — initialize source submodule or pass --source")
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "asset_inventory.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    with (BUILD / "asset_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        out = csv.DictWriter(f, fieldnames=["mod", "file", "type"])
        out.writeheader()
        out.writerows(rows)
    print("Wrote build/asset_inventory.json and build/asset_inventory.csv")

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2)+"\n", encoding="utf-8")

def manifest(name, key, kind):
    return {"format_version": 2,
            "header": {"name": name, "description": "Local visual asset reuse prototype",
                       "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, key+kind+"header")),
                       "version": [0,1,0], "min_engine_version": [1,20,0]},
            "modules": [{"type": kind, "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, key+kind+"module")),
                         "version": [0,1,0]}]}

def build_bluff():
    source = ROOT / "mods/44-mowzies-mobs/upstream"
    base = source / "src/main/resources/assets/mowziesmobs"
    geometry = base / "geo/bluff.geo.json"
    texture = base / "textures/entity/bluff.png"
    animation = base / "animations/bluff.animation.json"
    bbmodel = source / "assets/bluff.bbmodel"
    if not geometry.is_file() or not texture.is_file():
        raise SystemExit("Mowzie geometry/PNG missing. Run: git submodule update --init --recursive")
    parsed = json.loads(geometry.read_text(encoding="utf-8"))
    entries = parsed.get("minecraft:geometry", [])
    if not entries or "description" not in entries[0]:
        raise SystemExit("Unexpected geometry schema; inspect original first")
    geom_id = entries[0]["description"]["identifier"]
    out = BUILD / "mowzie_bluff_reference"
    if out.exists(): shutil.rmtree(out)
    rp, bp = out / "Bluff_RP", out / "Bluff_BP"
    (rp / "models/entity").mkdir(parents=True, exist_ok=True)
    (rp / "textures/entity").mkdir(parents=True, exist_ok=True)
    shutil.copy2(geometry, rp / "models/entity/bluff.geo.json")
    shutil.copy2(texture, rp / "textures/entity/bluff.png")
    write_json(rp / "manifest.json", manifest("Minizin Bluff Resource Pack","minizin:bluff","resources"))
    write_json(bp / "manifest.json", manifest("Minizin Bluff Behavior Pack","minizin:bluff","data"))
    write_json(rp / "entity/bluff.entity.json", {
        "format_version":"1.10.0",
        "minecraft:client_entity":{"description":{
            "identifier":"minizin:bluff","materials":{"default":"entity_alphatest"},
            "textures":{"default":"textures/entity/bluff"},
            "geometry":{"default":geom_id},
            "render_controllers":["controller.render.minizin.bluff"],
            "spawn_egg":{"base_color":"#564337","overlay_color":"#c7bba2"}
        }}
    })
    write_json(rp / "render_controllers/bluff.render_controllers.json", {
        "format_version":"1.8.0",
        "render_controllers":{"controller.render.minizin.bluff":{
            "geometry":"Geometry.default",
            "materials":[{"*":"Material.default"}],
            "textures":["Texture.default"]
        }}
    })
    write_json(bp / "entities/bluff.json", {
        "format_version":"1.20.0",
        "minecraft:entity":{"description":{
            "identifier":"minizin:bluff","is_spawnable":True,
            "is_summonable":True,"is_experimental":False
        },"components":{
            "minecraft:type_family":{"family":["minizin","mob"]},
            "minecraft:health":{"value":20,"max":20},
            "minecraft:collision_box":{"width":0.8,"height":1.8},
            "minecraft:physics":{},
            "minecraft:movement":{"value":0.2},
            "minecraft:movement.basic":{},
            "minecraft:navigation.walk":{},
            "minecraft:behavior.random_stroll":{"priority":6,"speed_multiplier":0.8},
            "minecraft:behavior.look_at_player":{"priority":7,"look_distance":6},
            "minecraft:behavior.random_look_around":{"priority":8}
        }}
    })
    (out / "source_reference").mkdir(parents=True, exist_ok=True)
    if animation.exists(): shutil.copy2(animation, out / "source_reference/bluff.animation.json")
    if bbmodel.exists(): shutil.copy2(bbmodel, out / "source_reference/bluff.bbmodel")
    # Original animation contains Java/GeckoLib expression forms and is intentionally not wired.
    for folder in [rp, bp]:
        with zipfile.ZipFile(out / (folder.name + ".mcpack"), "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.rglob("*")):
                if p.is_file(): z.write(p, p.relative_to(folder).as_posix())
    with zipfile.ZipFile(out / "Minizin_Bluff_Reference.mcaddon", "w", zipfile.ZIP_DEFLATED) as z:
        for p in ["Bluff_RP.mcpack", "Bluff_BP.mcpack"]:
            z.write(out / p, p)
    print("Staged:", out / "Minizin_Bluff_Reference.mcaddon")
    print("Only geo+PNG included. Animation in source_reference; no native animation/AI port.")
    print("UNTESTED in Minecraft Bedrock. Do not publish derived assets without authorization.")

def main():
    ap = argparse.ArgumentParser()
    cmd = ap.add_subparsers(dest="command", required=True)
    s = cmd.add_parser("scan")
    s.add_argument("--mod", choices=MODS)
    s.add_argument("--source", type=str)
    cmd.add_parser("stage-mowzie-bluff")
    args = ap.parse_args()
    if args.command == "scan": scan(args)
    if args.command == "stage-mowzie-bluff": build_bluff()
if __name__ == "__main__": main()
