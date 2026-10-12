#!/usr/bin/env python3
"""Recover the genuine RFTools Storage Terminal block for Bedrock visual QA.

Uses the original pinned Java model and its PNG textures, rather than reusing
the duplicated turquoise/generic images in Reinos & Circuitos v2.4.0.
Builds an independent RP+BP, verifies JSON + texture references, and reports
remaining limitations. No fabricated textures, no claim of gameplay parity.
"""
from __future__ import annotations
import argparse, hashlib, io, json, shutil, uuid, zipfile
from pathlib import Path
from block_atlas_to_bedrock import convert

ROOT=Path(__file__).resolve().parent.parent
NAMESPACE=uuid.UUID("01aed03f-0b0d-424b-a8b7-1716b4e9cd2e")
def uid(x):return str(uuid.uuid5(NAMESPACE,x))
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def manifest(pack):
    identifier=uid(pack+"/header")
    return {"format_version":2,"header":{"name":"RFTools Recovered — Storage Terminal "+pack,
        "description":"Original model and texture research; not a functional RFTools port",
        "uuid":identifier,"version":[0,1,0],"min_engine_version":[1,21,90]},
        "modules":[{"type":"resources" if pack=="RP" else "data",
                    "uuid":uid(pack+"/module"),"version":[0,1,0]}],
        **({"dependencies":[{"uuid":uid("RP/header"),"version":[0,1,0]}]} if pack=="BP" else {})}
def archive(folder):
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w",zipfile.ZIP_DEFLATED) as z:
        for file in sorted(folder.rglob("*")):
            if file.is_file():z.write(file,file.relative_to(folder).as_posix())
    return data.getvalue()
def build(upstream,out):
    geo,atlas,issues=convert(upstream,"rftools",["block/storage_terminal"],
                             "geometry.rftools_recovered.storage_terminal")
    cube_count=sum(len(b.get("cubes",[])) for b in geo["minecraft:geometry"][0]["bones"])
    if cube_count<1:raise ValueError("Upstream model provided no cuboids; refusing empty render")
    rp,bp=out/"RP",out/"BP"
    save(rp/"manifest.json",manifest("RP"));save(bp/"manifest.json",manifest("BP"))
    save(rp/"models/blocks/storage_terminal.geo.json",geo)
    img=rp/"textures/blocks/storage_terminal_atlas.png"
    img.parent.mkdir(parents=True,exist_ok=True);atlas.save(img)
    save(rp/"textures/terrain_texture.json",{
        "resource_pack_name":"rftools_recovered","texture_name":"atlas.terrain",
        "texture_data":{"rftools_storage_terminal":{"textures":"textures/blocks/storage_terminal_atlas"}}})
    save(rp/"blocks.json",{"rftools_recovered:storage_terminal":{"sound":"stone"}})
    save(bp/"blocks/storage_terminal.json",{
        "format_version":"1.21.90",
        "minecraft:block":{
            "description":{"identifier":"rftools_recovered:storage_terminal",
                           "menu_category":{"category":"construction"}},
            "components":{"minecraft:geometry":"geometry.rftools_recovered.storage_terminal",
                          "minecraft:material_instances":{"*":{"texture":"rftools_storage_terminal",
                                                              "render_method":"opaque"}},
                          "minecraft:destructible_by_mining":{"seconds_to_destroy":3},
                          "minecraft:destructible_by_explosion":{"explosion_resistance":6}}}})
    license_path=upstream/"LICENSE.md"
    if license_path.is_file():
        shutil.copy2(license_path,out/"RFTools_UPSTREAM_LICENSE.md")
    archive_path=out/"RFTools_StorageTerminal_Original_Visual_QA.mcaddon"
    with zipfile.ZipFile(archive_path,"w",zipfile.ZIP_STORED) as bundle:
        bundle.writestr("RFToolsRecovered_RP.mcpack",archive(rp))
        bundle.writestr("RFToolsRecovered_BP.mcpack",archive(bp))
    report={"status":"GENERATED_NOT_GAME_TESTED","source_repo":"McJtyMods/RFTools",
      "commit":"030a495c8530183bdfe47475ed41d45386e56f6c",
      "model":"src/main/resources/assets/rftools/models/block/storage_terminal.json",
      "original_textures":["machinestorageterminal.png","machineside.png","machinebottom.png"],
      "geometry_cubes":cube_count,"texture_atlas_size":list(atlas.size),
      "atlas_sha256":hashlib.sha256(img.read_bytes()).hexdigest(),
      "warnings":issues+["No original RFTools machine logic, recipes, GUI or inventory behavior.",
                         "Bedrock Content Log and hand/placed block visual testing pending."]}
    save(out/"VERIFIED_SOURCE_AND_LIMITATIONS.json",report)
    print(json.dumps(report,indent=2))
    return archive_path
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",type=Path,default=ROOT/"mods/54-rftools/upstream")
    p.add_argument("--output",type=Path,default=ROOT/"build/rftools_storage_terminal")
    a=p.parse_args()
    build(a.upstream,a.output)
