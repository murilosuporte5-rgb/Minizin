#!/usr/bin/env python3
"""Actual visual-resource conversion from pinned MCA/Origins/RFTools upstream files.

- Bedrock item_texture.json + minecraft:item registry for original PNG icons
- Flatten original MCA two-layer crib/item sprites to Bedrock RGBA icons
- Convert standard JSON block-model elements to Bedrock geometry/texture atlases
- Preserve source geometry provenance; no code or assets authored from scratch
- Does NOT auto-convert Blender/OBJ polygons to 3D Bedrock cubes.

Requires Pillow, and the original checked-out Git submodules.
"""
from __future__ import annotations
import argparse, json, re, shutil, io, hashlib, zipfile, sys
from pathlib import Path
from PIL import Image
from block_atlas_to_bedrock import convert as java_to_geo

ROOT=Path(__file__).resolve().parent.parent
SOURCES={
 "mca":(ROOT/"mods/33-mca-reborn/upstream","common/src/main/resources"),
 "rftools":(ROOT/"mods/54-rftools/upstream","src/main/resources"),
 "origins":(ROOT/"mods/55-origins/upstream","src/main/resources"),
}
def json_out(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
def source_png(mod,rel):
    base,res=SOURCES[mod]
    candidates=[base/res/"assets"/mod/"textures"/(rel+".png"),
        base/"common/src/generated/resources"/"assets"/mod/"textures"/(rel+".png")]
    if mod=="mca":
        candidates.extend([base/"common/src/main/resources"/"assets"/mod/"textures"/(rel+".png")])
    return next((p for p in candidates if p.is_file()),None)
def copy_icon(mod,rel,rp,registry,items,provenance):
    original=source_png(mod,rel)
    if not original:return False
    ident="minizin_"+mod+"_"+re.sub(r"[^a-z0-9_]","_",rel.lower().replace("/","_"))
    if ident in registry:return False
    target=rp/"textures"/"items"/"minizin"/mod/(rel+".png")
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(original,target)
    registry[ident]={"textures":"textures/items/minizin/"+mod+"/"+rel}
    items.append((mod,ident))
    provenance.append({"id":ident,"source":str(original.relative_to(SOURCES[mod][0])),
                       "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"kind":"original_icon"})
    return True
def flatten_mca_item_models(rp,registry,items,provenance):
    root=SOURCES["mca"][0]/"common/src/generated/resources/assets/mca/models/item"
    generated=0;issues=[]
    for file in sorted(root.glob("*.json")):
        try:
            doc=json.loads(file.read_text())
            textures=doc.get("textures",{})
            layers=[]
            for i in range(6):
                val=textures.get("layer"+str(i))
                if not val:break
                namespace,rel=val.split(":",1) if ":" in val else ("minecraft",val)
                if namespace!="mca":raise ValueError("Needs vanilla external texture "+val)
                png=source_png("mca",rel)
                if not png:raise ValueError("Missing original texture "+val)
                layers.append(Image.open(png).convert("RGBA"))
            if not layers:continue
            if any(layer.size!=layers[0].size for layer in layers):
                raise ValueError("Layer dimensions differ")
            result=layers[0]
            for layer in layers[1:]:result=Image.alpha_composite(result,layer)
            ident="minizin_mca_item_"+re.sub(r"[^a-z0-9_]","_",file.stem.lower())
            out=rp/"textures/items/minizin/mca_generated"/(file.stem+".png")
            out.parent.mkdir(parents=True,exist_ok=True)
            result.save(out)
            registry[ident]={"textures":"textures/items/minizin/mca_generated/"+file.stem}
            items.append(("mca",ident))
            provenance.append({"id":ident,"source":str(file.relative_to(SOURCES["mca"][0])),
                    "layers":list(textures.values()),
                    "sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"kind":"composited_item_layers"})
            generated+=1
        except (ValueError,KeyError,OSError) as e:
            issues.append({"source":file.name,"reason":str(e)})
    return generated,issues
def assets_for_player_skins(rp,provenance):
    root=SOURCES["mca"][0]/"common/src/main/resources/assets/mca/skins"
    genders=("female","male")
    result=[]
    for gender in genders:
        for n in range(5):
            paths=[root/f"skin/{gender}/{n}.png",
                   root/"face/normal/0.png",
                   root/f"hair/{gender}/0.png"]
            if not all(x.exists() for x in paths):
                raise ValueError("Missing MCA original skin layer "+gender+"/"+str(n))
            images=[Image.open(x).convert("RGBA") for x in paths]
            if not all(x.size==(64,64) for x in images):raise ValueError("Skin UV source needs 64x64")
            skin=images[0]
            for x in images[1:]:skin=Image.alpha_composite(skin,x)
            dest=rp/f"textures/entity/minizin/mca_{gender}_{n}.png"
            dest.parent.mkdir(parents=True,exist_ok=True)
            skin.save(dest)
            provenance.append({"kind":"mca_skin_composite","source_layers":
                [str(x.relative_to(SOURCES["mca"][0])) for x in paths],
                "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                "output":str(dest.relative_to(rp))})
            result.append((gender,n,dest))
    return result
def test_entity_geometry(rp):
    # A minimal humanoid geometry approximation uses original MCA layered 64x64 PNGs.
    # Body UV must be visually reviewed against MCA ModelPart rig before release.
    bones=[
        {"name":"head","pivot":[0,24,0],"cubes":[{"origin":[-4,24,-4],"size":[8,8,8],"uv":[0,0]}]},
        {"name":"body","pivot":[0,24,0],"cubes":[{"origin":[-4,12,-2],"size":[8,12,4],"uv":[16,16]}]},
        {"name":"rightArm","pivot":[-5,22,0],"cubes":[{"origin":[-8,12,-2],"size":[4,12,4],"uv":[40,16]}]},
        {"name":"leftArm","pivot":[5,22,0],"cubes":[{"origin":[4,12,-2],"size":[4,12,4],"uv":[32,48]}]},
        {"name":"rightLeg","pivot":[-2,12,0],"cubes":[{"origin":[-4,0,-2],"size":[4,12,4],"uv":[0,16]}]},
        {"name":"leftLeg","pivot":[2,12,0],"cubes":[{"origin":[0,0,-2],"size":[4,12,4],"uv":[16,48]}]}
    ]
    json_out(rp/"models/entity/minizin_mca_humanoid.geo.json",{
      "format_version":"1.12.0",
      "minecraft:geometry":[{
        "description":{"identifier":"geometry.minizin.mca_humanoid",
         "texture_width":64,"texture_height":64,
         "visible_bounds_width":2,"visible_bounds_height":3,"visible_bounds_offset":[0,1.5,0]},
        "bones":bones}]})
    json_out(rp/"render_controllers/minizin_mca.render_controllers.json",{
      "format_version":"1.8.0","render_controllers":{
       "controller.render.minizin.mca_npc":{"geometry":"Geometry.default",
            "materials":[{"*":"Material.default"}],"textures":["Texture.default"]}}})
def spawnable_entities(bp,rp,skins):
    for gender,n,path in skins:
        ident=f"minizin:mca_{gender}_{n}"
        json_out(bp/f"entities/mca_{gender}_{n}.json",{
          "format_version":"1.21.0","minecraft:entity":{
           "description":{"identifier":ident,"is_spawnable":True,"is_summonable":True,"is_experimental":False},
           "components":{
            "minecraft:type_family":{"family":["villager","minizin","npc"]},
            "minecraft:health":{"value":20,"max":20},
            "minecraft:collision_box":{"width":0.6,"height":1.8},
            "minecraft:physics":{},"minecraft:movement":{"value":0.23},
            "minecraft:movement.basic":{},"minecraft:navigation.walk":{},
            "minecraft:behavior.random_stroll":{"priority":5,"speed_multiplier":0.6},
            "minecraft:behavior.look_at_player":{"priority":6,"look_distance":8.0},
            "minecraft:behavior.random_look_around":{"priority":7}
           }}})
        json_out(rp/f"entity/mca_{gender}_{n}.entity.json",{
          "format_version":"1.10.0","minecraft:client_entity":{"description":{
           "identifier":ident,
           "materials":{"default":"entity_alphatest"},
           "textures":{"default":f"textures/entity/minizin/mca_{gender}_{n}"},
           "geometry":{"default":"geometry.minizin.mca_humanoid"},
           "render_controllers":["controller.render.minizin.mca_npc"],
           "spawn_egg":{"base_color":"#88654c","overlay_color":"#b89e80"}}}})
def generated_item_defs(bp,rp,registry,items):
    json_out(rp/"textures/item_texture.json",{
      "resource_pack_name":"minizin_next_four","texture_name":"atlas.items",
      "texture_data":registry})
    for source,icon in items:
        # No automatic crafting/behavior equivalence to Java mods.
        if source=="mca":key="mca"
        elif source=="rftools":key="rftools"
        else:key="origins"
        full_id="minizin:"+icon.removeprefix("minizin_")
        json_out(bp/"items"/(icon+".json"),{
          "format_version":"1.21.0","minecraft:item":{
           "description":{"identifier":full_id,"menu_category":{"category":"items"}},
           "components":{"minecraft:icon":icon,
                         "minecraft:max_stack_size":64}}})
def discover_icons(rp,registry,items,provenance):
    count={}
    for mod in ("mca","rftools","origins"):
        root=SOURCES[mod][0]
        relroot="common/src/main/resources/assets/mca/textures/item" if mod=="mca" else (
           "src/main/resources/assets/rftools/textures/items" if mod=="rftools" else
           "src/main/resources/assets/origins/textures/item")
        base=root/relroot
        n=0
        for file in sorted(base.rglob("*.png")):
            rel=file.relative_to(base).with_suffix("").as_posix()
            namespace_prefix=("items" if mod=="rftools" else "item")
            if copy_icon(mod,namespace_prefix+"/"+rel,rp,registry,items,provenance):n+=1
        count[mod]=n
    return count
def convert_blocks(bp,rp):
    converted={};warnings=[]
    for mod in ("mca","rftools"):
        root=SOURCES[mod][0]
        modelroot=root/("common/src/main/resources/assets/mca/models/block" if mod=="mca"
                        else "src/main/resources/assets/rftools/models/block")
        count=0;skip=[]
        for path in sorted(modelroot.glob("*.json")):
            try:
                geo,atlas,issues=java_to_geo(root,mod,["block/"+path.stem],
                              "geometry.minizin."+mod+"."+path.stem.lower())
                target=f"{mod}_{path.stem}"
                geo_out=rp/"models/entity"/(target+".geo.json")
                tex_out=rp/"textures/entity/minizin"/(target+".png")
                json_out(geo_out,geo);tex_out.parent.mkdir(parents=True,exist_ok=True);atlas.save(tex_out)
                count+=1
                for note in set(issues):warnings.append({"model":path.name,"reason":note})
            except Exception as e:
                skip.append({"model":path.name,"reason":str(e)})
        converted[mod]={"source_count":len(list(modelroot.glob("*.json"))),
                "converted":count,"skipped":skip}
    return converted,warnings
def run(root:Path):
    bp=root/"BP";rp=root/"RP"
    if not bp.exists() or not rp.exists():raise ValueError("Run build_next_four_pack.py first")
    origins_registry={};items=[];provenance=[]
    icons=discover_icons(rp,origins_registry,items,provenance)
    layered,issues=flatten_mca_item_models(rp,origins_registry,items,provenance)
    skins=assets_for_player_skins(rp,provenance)
    test_entity_geometry(rp)
    spawnable_entities(bp,rp,skins)
    generated_item_defs(bp,rp,origins_registry,items)
    blocks,warnings=convert_blocks(bp,rp)
    report={"icons_by_mod":icons,"composited_mca_items":layered,
       "composite_skipped":issues,"skin_presets":len(skins),
       "generated_bedrock_items":len(items),"java_block_conversion":blocks,
       "geometry_warnings":warnings,"asset_provenance":provenance,
       "limits":["2D icons are importable; their original Java functionality is not ported.",
                 "MCA entity UV/humanoid is an approximation; test visuals and animations.",
                 "Converted block geometries are resources; separate custom block/entity definitions needed.",
                 "OBJ/Blender meshes stay unconverted as existing original sources.",
                 "Not tested on Minecraft Bedrock Android."]}
    json_out(root/"converted_resources_report.json",report)
    print(json.dumps({"icons":icons,"layered_mca_items":layered,"skins":len(skins),
                      "registered_items":len(items),
                      "blocks":{k:{"converted":v["converted"],"source":v["source_count"]}
                       for k,v in blocks.items()}},ensure_ascii=False))
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--staged",type=Path,default=ROOT/"build/next_four")
    a=p.parse_args()
    try:run(a.staged)
    except Exception as e:print("Conversion failure:",e,file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
