#!/usr/bin/env python3
"""Stage and audit source formats for MCA Reborn, Carry On, RFTools, Origins.

Copies only files that exist in the pinned upstream Git submodules. Excludes fonts
and secrets. Each staged item has original path, SHA-256, size and category.
This is source extraction, NOT a Bedrock port or automatic Java-to-geo conversion.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil,sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SPECS={
 "mca":{"folder":"33-mca-reborn","repo":"Luke100000/minecraft-comes-alive",
        "prefixes":["/assets/mca/","/data/mca/","/net/conczin/mca/client/model/"]},
 "carryon":{"folder":"34-carry-on","repo":"Tschipp/CarryOn",
        "prefixes":["/assets/carryon/","/data/carryon/","/tschipp/carryon/common/carry/",
                    "/tschipp/carryon/common/scripting/","/tschipp/carryon/common/config/",
                    "/tschipp/carryon/client/render/","/tschipp/carryon/client/modeloverride/"]},
 "rftools":{"folder":"54-rftools","repo":"McJtyMods/RFTools",
        "prefixes":["/assets/rftools/","art/"]},
 "origins":{"folder":"55-origins","repo":"apace100/origins-fabric",
        "prefixes":["/assets/origins/","/data/origins/"]},
}
EXCLUDE={".ttf",".otf",".woff",".woff2",".env",".key",".pem",".p12",".pfx"}
def category(p:str):
    path=p.replace("\\","/").lower()
    name=path.rsplit("/",1)[-1]
    if path.endswith((".bbmodel",".geo.json")):return "geometry"
    if path.endswith((".obj",".blend",".fbx",".gltf",".glb")):return "mesh"
    if path.endswith(".mtl"):return "mesh_material"
    if path.endswith(".png"):return "png_texture"
    if path.endswith((".ogg",".wav")):return "sound"
    if "/models/" in path and path.endswith(".json"):return "java_model_json"
    if "/client/model/" in path and path.endswith(".java"):return "java_entity_model"
    if "/client/render/" in path and path.endswith(".java"):return "java_renderer"
    if "/common/carry/" in path and path.endswith(".java"):return "carry_logic_java"
    if "/common/scripting/" in path and path.endswith(".java"):return "carry_rules_java"
    if "/common/config/" in path and path.endswith(".java"):return "carry_config_java"
    if path.endswith(".java"):return "java_logic"
    if "/powers/" in path and path.endswith(".json"):return "origin_power"
    if "/origins/" in path and path.endswith(".json"):return "origin_definition"
    if "/origin_layers/" in path and path.endswith(".json"):return "origin_layer"
    if "/tags/" in path and path.endswith(".json"):return "tag_json"
    if path.endswith((".nbt",".schem",".mcstructure")):return "structure"
    if path.endswith(".json"):return "json_data"
    if path.endswith((".lang",".properties")) or "/lang/" in path:return "localization"
    return "other_resource"

def permitted(name,mod):
    if mod not in SPECS:raise ValueError("Unsupported mod: "+mod)
    pos=name.replace("\\","/")
    return any(pos.startswith(prefix) if prefix.startswith("art/") else prefix in "/"+pos
               for prefix in SPECS[mod]["prefixes"])

def extract(source:Path,mod:str,output:Path,copy=True):
    if not source.is_dir():raise ValueError("Source checkout not found: "+str(source))
    if mod not in SPECS:raise ValueError("Invalid mod")
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for p in sorted(source.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(source).as_posix()
        if ".git" in p.relative_to(source).parts or not permitted(rel,mod):continue
        if p.suffix.lower() in EXCLUDE:continue
        if p.stat().st_size>8_000_000:continue
        b=p.read_bytes()
        row={"source":rel,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
             "category":category(rel)}
        if copy:
            dst=output/"original"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(b)
            row["staged"]=dst.relative_to(output).as_posix()
        rows.append(row)
    if copy:
        license_name="LICENSE.md" if mod=="rftools" else "LICENSE"
        license_file=source/license_name
        if license_file.exists():
            shutil.copy2(license_file,output/"UPSTREAM_LICENSE.txt")
    counts=dict(sorted(Counter(row["category"] for row in rows).items()))
    report={"mod":mod,"source_repo":SPECS[mod]["repo"],
            "source_checkout":str(source),"file_count":len(rows),"categories":counts,
            "files":rows,"disclaimer":"Original upstream resources for inspection/conversion; not an installed Bedrock mod."}
    (output/"inventory.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (output/"inventory.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["source","bytes","sha256","category","staged"])
        writer.writeheader();writer.writerows(rows)
    print(json.dumps({"mod":mod,"files":len(rows),"categories":counts,
                      "bytes":sum(row["bytes"] for row in rows)},ensure_ascii=False))
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mod",required=True,choices=sorted(SPECS))
    ap.add_argument("--source",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--inventory-only",action="store_true")
    args=ap.parse_args()
    source=args.source or ROOT/"mods"/SPECS[args.mod]["folder"]/"upstream"
    try:
        report=extract(source,args.mod,args.output,copy=not args.inventory_only)
        if not report["file_count"]:raise ValueError("No source assets found")
    except Exception as exc:print("Error:",exc,file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
