#!/usr/bin/env python3
"""Validate staged RP/BP and package nested .mcpack ZIPs into a .mcaddon (stdlib only)."""
from __future__ import annotations
import argparse, io, json, sys, uuid, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def scan_json(base):
    for path in base.rglob("*.json"):
        try: yield path, json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, UnicodeError) as error: raise ValueError(f"Invalid JSON: {path}: {error}") from error

def validate(root):
    rp,bp=root/"RP",root/"BP"
    data={}
    for label,folder in (("RP",rp),("BP",bp)):
        if not folder.is_dir(): raise ValueError(f"Missing folder {folder}")
        data[label]=dict(scan_json(folder))
        manifest=data[label].get(folder/"manifest.json")
        if not manifest: raise ValueError(f"Missing manifest in {folder}")
        uuid.UUID(manifest["header"]["uuid"])
        for module in manifest.get("modules",[]): uuid.UUID(module["uuid"])
    clients={}
    geos=set()
    animations=set()
    for file,doc in data["RP"].items():
        if not isinstance(doc,dict): continue  # texts/languages.json is an array
        if "minecraft:client_entity" in doc:
            c=doc["minecraft:client_entity"]["description"]
            clients[c["identifier"]]=c
        for geo in doc.get("minecraft:geometry",[]): geos.add(geo["description"]["identifier"])
        animations.update(doc.get("animations",{}).keys())
    entities={d["minecraft:entity"]["description"]["identifier"] for p,d in data["BP"].items() if "minecraft:entity" in d}
    if clients.keys()!=entities: raise ValueError(f"Client/behavior IDs differ: {clients.keys()} vs {entities}")
    for ident,desc in clients.items():
        for g in desc.get("geometry",{}).values():
            if g not in geos: raise ValueError(f"{ident}: geometry missing: {g}")
        for tex in desc.get("textures",{}).values():
            if not (rp/(tex+".png")).exists(): raise ValueError(f"{ident}: missing texture {tex}.png")
        for anim in desc.get("animations",{}).values():
            if anim not in animations: raise ValueError(f"{ident}: missing animation {anim}")
    return rp,bp,len(entities)

def zipped(folder):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for path in sorted(folder.rglob("*")):
            if path.is_file(): z.write(path,path.relative_to(folder).as_posix())
    return out.getvalue()

def build(name,root=ROOT):
    if name not in ("waystones","mowzie"): raise ValueError("Unknown pack")
    rp,bp,n=validate(root/"bedrock"/"packs"/name)
    dest=root/"build"/f"Minizin_{name}.mcaddon"
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_STORED) as z:
        z.writestr(name+"_RP.mcpack",zipped(rp))
        z.writestr(name+"_BP.mcpack",zipped(bp))
    with zipfile.ZipFile(dest) as archive:
        for filename in archive.namelist():
            with zipfile.ZipFile(io.BytesIO(archive.read(filename))) as pack:
                assert "manifest.json" in pack.namelist(), "pack without manifest"
    print(f"Built {dest} ({dest.stat().st_size} bytes, {n} entities). Not tested in Minecraft.")
    return dest

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("name",choices=["waystones","mowzie"])
    ap.add_argument("--repo-root",type=Path,default=ROOT)
    opt=ap.parse_args()
    try:build(opt.name,opt.repo_root)
    except Exception as error:
        print(f"Build error: {error}",file=sys.stderr)
        sys.exit(1)
