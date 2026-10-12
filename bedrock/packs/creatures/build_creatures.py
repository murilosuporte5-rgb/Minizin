#!/usr/bin/env python3
"""Local-only staging of original assets for the Minizin creature experiment.

Never checks third-party PNG/OGG back into Git. Explicit permission required.
Exit nonzero if any original model or texture is missing: no invisible mobs.
"""
import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
SRC=ROOT/"generated/conversions"
MOD=ROOT/"mods"
TEXTURES={
 "fire_dragon":("16-ice-and-fire","iceandfire","models/firedragon",[f"red_{i}.png" for i in range(1,6)]),
 "ice_dragon":("16-ice-and-fire","iceandfire","models/icedragon",[f"blue_{i}.png" for i in range(1,6)]),
 "lightning_dragon":("16-ice-and-fire","iceandfire","models/lightningdragon",[f"black_{i}.png" for i in range(1,6)]),
 "atlatitan":("42-alexs-caves","alexscaves","entity",["atlatitan.png"]),
 "ignis":("43-cataclysm","cataclysm","entity/ignis",["ignis_idle_0.png","ignis_soul_idle_0.png"])
}
GEO={
 "fire_dragon":"ice_and_fire/firedragon/firedragon_BaseMale.geo.json",
 "ice_dragon":"ice_and_fire/icedragon/icedragon_BaseMale.geo.json",
 "lightning_dragon":"ice_and_fire/lightningdragon/lightningdragon_BaseMale.geo.json",
 "atlatitan":"alex_caves/atlatitan.geo.json",
 "ignis":"cataclysm/Ignis_Model.geo.json"
}
ITEMS={
 "dragon_meal":("16-ice-and-fire","iceandfire","dragon_meal.png"),
 "creative_dragon_meal":("16-ice-and-fire","iceandfire","creative_dragon_meal.png"),
 "dragon_flute":("16-ice-and-fire","iceandfire","dragon_flute.png"),
 "dragon_armor_iron":("16-ice-and-fire","iceandfire","dragonarmor_iron_head.png"),
 "serene_salad":("42-alexs-caves","alexscaves","serene_salad.png"),
 "dragon_egg_fire":("16-ice-and-fire","iceandfire","egg_red.png"),
 "dragon_egg_ice":("16-ice-and-fire","iceandfire","egg_blue.png"),
 "dragon_egg_lightning":("16-ice-and-fire","iceandfire","egg_black.png"),
 "dragon_scale_fire":("16-ice-and-fire","iceandfire","scales_red.png"),
 "dragon_scale_ice":("16-ice-and-fire","iceandfire","scales_blue.png"),
 "dragon_scale_lightning":("16-ice-and-fire","iceandfire","scales_black.png")
}
POSE_SETS={"bite":["Bite1","Bite2","Bite3"],
           "tail":["Tail1","Tail2","Tail3"],
           "wing":["WingBlast1","WingBlast3","WingBlast5","WingBlast7"],
           "stream":["AttackStreamCharge1","AttackStreamCharge3","AttackStreamBreath"],
           "charge":["AttackBlastCharge1","AttackBlastCharge3","AttackBlastBreath"],
           "flight":["Flight1","Flight2","Flight3","Flight4","Flight5","Flight6"]}
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def original(mod,namespace,subdir,name):
    return MOD/mod/"upstream/src/main/resources/assets"/namespace/"textures"/subdir/name
def geometry(path):
    payload=json.loads(path.read_text(encoding="utf-8"))
    geo=payload["minecraft:geometry"][0]
    if not geo["bones"] or not geo["description"]["identifier"]:
        raise ValueError("Geometria vazia: "+str(path))
    return payload
def pose_clip(baseline,pose_paths,duration):
    base={b["name"]:b for b in baseline["minecraft:geometry"][0]["bones"]}
    poses=[{b["name"]:b for b in geometry(path)["minecraft:geometry"][0]["bones"]} for path in pose_paths]
    output={}
    for name,rest in base.items():
        if not any(name in pose for pose in poses):continue
        origin=rest.get("rotation",[0,0,0])
        rotations=[]
        for pose in poses:
            rot=pose.get(name,rest).get("rotation",origin)
            rotations.append([round(float(rot[i])-float(origin[i]),3) for i in range(3)])
        if all(max(abs(n) for n in r)<0.01 for r in rotations):continue
        keys={"0.0":[0,0,0]}
        for i,r in enumerate(rotations):
            keys[str(round(duration*(i+1)/(len(poses)+1),3))]=r
        keys[str(duration)]=[0,0,0]
        output[name]={"rotation":keys}
    return {"loop":False,"animation_length":duration,"bones":output}
def render_controller(id,count):
    texture_names=["Texture.stage"+str(i) for i in range(count)]
    index="query.property('minizin_creatures:stage') - 1" if id.endswith("_dragon") else ("query.property('minizin_creatures:phase') > 0" if id=="ignis" else "0")
    return {"arrays":{"textures":{"Array.original_skins":texture_names}},
            "geometry":"Geometry.default","materials":[{"*":"Material.default"}],
            "textures":["Array.original_skins["+index+"]"]}
def build(out,has_permission):
    if not has_permission:raise RuntimeError("Use --authorized-assets apenas quando tiver autorização para adaptar e redistribuir os recursos dos quatro mods.")
    out=Path(out)
    if out.exists():shutil.rmtree(out)
    bp=out/"Minizin_Creatures_BP";rp=out/"Minizin_Creatures_RP"
    shutil.copytree(FOLDER/"BP",bp)
    write_json(rp/"manifest.json",{"format_version":2,
      "header":{"name":"Minizin Creatures RP (original resources, private stage)",
      "description":"Unverified experimental textures and Java geometry converted for Bedrock",
      "uuid":"5d1ad275-1803-4128-88c3-8f60d0f96a0a","version":[0,1,0],"min_engine_version":[1,21,0]},
      "modules":[{"type":"resources","uuid":"1511b358-9d4b-42d1-a432-6fe89107d72c","version":[0,1,0]}]})
    controllers={}
    for id,(mod,namespace,subdir,skins) in TEXTURES.items():
        source=SRC/GEO[id]
        converted=geometry(source)
        geo_id=converted["minecraft:geometry"][0]["description"]["identifier"]
        target=rp/"models/entity"/(id+".geo.json");target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        textures={}
        for i,skin in enumerate(skins):
            texture_source=original(mod,namespace,subdir,skin)
            if not texture_source.is_file():raise FileNotFoundError("Textura original ausente: "+str(texture_source))
            dst=rp/"textures/entity"/(id+"_stage"+str(i)+".png");dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(texture_source,dst)
            textures["stage"+str(i)]="textures/entity/"+id+"_stage"+str(i)
        animations={}
        if id.endswith("_dragon"):
            kind=id.replace("_dragon","")+"dragon"
            base=SRC/"ice_and_fire"/kind/(kind+"_BaseMale.geo.json")
            clips={}
            for key,pose_names in POSE_SETS.items():
                paths=[SRC/"ice_and_fire"/kind/(kind+"_"+name+".geo.json") for name in pose_names]
                duration=1.2 if key in ("flight","wing") else 0.75
                clip=pose_clip(converted,paths,duration)
                clips["animation.minizin_creatures."+id+"."+key]=clip
                animations[key]="animation.minizin_creatures."+id+"."+key
            write_json(rp/"animations"/(id+".animation.json"),{"format_version":"1.8.0","animations":clips})
        desc={"identifier":"minizin_creatures:"+id,"materials":{"default":"entity_alphatest"},
              "textures":textures,"geometry":{"default":geo_id},
              "render_controllers":["controller.render.minizin_creatures."+id]}
        if animations:
            desc["animations"]=animations
            desc["scripts"]={"animate":[{key:"query.property('minizin_creatures:attack') == '"+key+"'"} for key in animations if key!="flight"]}
        write_json(rp/"entity"/(id+".entity.json"),{"format_version":"1.10.0","minecraft:client_entity":{"description":desc}})
        controllers["controller.render.minizin_creatures."+id]=render_controller(id,len(skins))
    for kind,col in (("fire","red"),("ice","blue"),("lightning","black")):
        shutil.copy2(FOLDER/"egg.geo.json",rp/"models/entity"/(kind+"_dragon_egg.geo.json"))
        egg_src=original("16-ice-and-fire","iceandfire","models/"+{"fire":"firedragon","ice":"icedragon","lightning":"lightningdragon"}[kind],"egg_"+col+".png")
        if not egg_src.is_file():raise FileNotFoundError("Modelo original de ovo sem textura: "+str(egg_src))
        dst=rp/"textures/entity"/(kind+"_dragon_egg.png");shutil.copy2(egg_src,dst)
        write_json(rp/"entity"/(kind+"_dragon_egg.entity.json"),{"format_version":"1.10.0","minecraft:client_entity":{"description":{
          "identifier":"minizin_creatures:"+kind+"_dragon_egg",
          "materials":{"default":"entity_alphatest"},"textures":{"default":"textures/entity/"+kind+"_dragon_egg"},
          "geometry":{"default":"geometry.minizin_creatures.dragon_egg_java"},
          "render_controllers":["controller.render.minizin_creatures."+kind+"_egg"]}}})
        controllers["controller.render.minizin_creatures."+kind+"_egg"]={"geometry":"Geometry.default",
          "materials":[{"*":"Material.default"}],"textures":["Texture.default"]}
    write_json(rp/"render_controllers/creatures.json",{"format_version":"1.8.0","render_controllers":controllers})
    atlas={}
    for id,(mod,namespace,file) in ITEMS.items():
        src=original(mod,namespace,("models/"+{"fire":"firedragon","ice":"icedragon","lightning":"lightningdragon"}[id.split("_")[-1]]) if id.startswith("dragon_egg_") else "item",file)
        if not src.is_file():raise FileNotFoundError("Ícone original ausente: "+str(src))
        dst=rp/"textures/items"/(id+".png");dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        atlas["minizin_creatures_"+id]={"textures":"textures/items/"+id}
        write_json(bp/"items"/(id+".json"),{"format_version":"1.21.0","minecraft:item":{
          "description":{"identifier":"minizin_creatures:"+id,"menu_category":{"category":"items"}},
          "components":{"minecraft:icon":"minizin_creatures_"+id,
             "minecraft:display_name":{"value":id.replace("_"," ").title()},
             "minecraft:max_stack_size":64,
             "minecraft:use_modifiers":{"use_duration":0.2,"movement_modifier":1.0}}}})
    write_json(rp/"textures/item_texture.json",{"resource_pack_name":"minizin_creatures","texture_name":"atlas.items","texture_data":atlas})
    # Existing original Bluff texture/rig is packed unchanged in its own source RP/BP.
    source_mowzie=ROOT/"bedrock/packs/mowzie"
    for part in ("BP","RP"):
        shutil.copytree(source_mowzie/part,out/("Minizin_Mowzie_"+part))
    archive=out.parent/"Minizin_Creatures_Research.mcaddon"
    if archive.exists():archive.unlink()
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for path in out.rglob("*"):
            if path.is_file():z.write(path,path.relative_to(out))
    return archive
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorized-assets",action="store_true")
    parser.add_argument("--output",default=str(ROOT/"build/creatures_staged"))
    args=parser.parse_args()
    try:print(build(Path(args.output),args.authorized_assets))
    except (RuntimeError,FileNotFoundError,KeyError,ValueError) as err:
        print("CREATURES BUILD FAILED: "+str(err),file=sys.stderr);return 2
    return 0
if __name__=="__main__":sys.exit(main())
