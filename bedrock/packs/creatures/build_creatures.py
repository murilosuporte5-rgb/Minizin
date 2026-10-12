#!/usr/bin/env python3
"""Local-only staging of original assets for the Minizin creature experiment.

Never checks third-party PNG/OGG back into Git. Explicit permission required.
Exit nonzero if any original model or texture is missing: no invisible mobs.
"""
import argparse
import io
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
 "ignis":("43-cataclysm","cataclysm","entity/ignis",["ignis_idle_0.png","ignis_soul_idle_0.png"]),
 "umvuthi":("44-mowzies-mobs","mowziesmobs","entity",["umvuthi.png"]),
 "umvuthana":("44-mowzies-mobs","mowziesmobs","entity",["umvuthana.png"]),
 "ender_guardian":("43-cataclysm","cataclysm","entity",["ender_guardian.png"])
}
GEO={
 "fire_dragon":"ice_and_fire/firedragon/firedragon_BaseMale.geo.json",
 "ice_dragon":"ice_and_fire/icedragon/icedragon_BaseMale.geo.json",
 "lightning_dragon":"ice_and_fire/lightningdragon/lightningdragon_BaseMale.geo.json",
 "atlatitan":"alex_caves/atlatitan.geo.json",
 "ignis":"cataclysm/Ignis_Model.geo.json",
 "ender_guardian":"cataclysm/Ender_Guardian_Model.geo.json"
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
AUDIO={
 "fire_dragon_breath":("16-ice-and-fire","iceandfire","mobs/dragon/fire/breath.ogg"),
 "ice_dragon_breath":("16-ice-and-fire","iceandfire","mobs/dragon/ice/breath.ogg"),
 "lightning_dragon_breath":("16-ice-and-fire","iceandfire","mobs/dragon/lightning/breath.ogg"),
 "dragon_egg_hatch":("16-ice-and-fire","iceandfire","effects/egg_hatch.ogg"),
 "atlatitan_stomp":("42-alexs-caves","alexscaves","mob/atlatitan/atlatitan_stomp_0.ogg"),
 "ignis_impact":("43-cataclysm","cataclysm","entity/ignis_impact.ogg"),
 "bluff_attack":("44-mowzies-mobs","mowziesmobs","entity/bluff/attack.ogg"),
 "bluff_spike":("44-mowzies-mobs","mowziesmobs","entity/bluff/spike_explode.ogg"),
 "umvuthi_supernova":("44-mowzies-mobs","mowziesmobs","entity/umvuthi/supernova_end.ogg"),
 "umvuthi_supernova_start":("44-mowzies-mobs","mowziesmobs","entity/umvuthi/supernova_start.ogg"),
 "ender_stomp":("43-cataclysm","cataclysm","entity/ender_guardian_stomp.ogg")
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
def check_staged(rp,bp):
    clients={}
    geos={}
    anims=set()
    for file in (rp/"entity").glob("*.json"):
        c=json.loads(file.read_text())["minecraft:client_entity"]["description"]
        if c["identifier"] in clients:raise ValueError("Duplicate client "+c["identifier"])
        clients[c["identifier"]]=c
    for file in (rp/"models/entity").glob("*.geo.json"):
        g=geometry(file)["minecraft:geometry"][0]
        geos[g["description"]["identifier"]]=g
    for file in (rp/"animations").glob("*.json"):
        anims.update(json.loads(file.read_text())["animations"])
    server=set()
    for file in (bp/"entities").glob("*.json"):
        j=json.loads(file.read_text())["minecraft:entity"]["description"]["identifier"]
        if j in server:raise ValueError("Duplicate server ID "+j)
        server.add(j)
    if set(clients)!=server:raise ValueError("Missing visual/server entity: "+str(server^set(clients)))
    for id,c in clients.items():
        for geo in c.get("geometry",{}).values():
            if geo not in geos:raise ValueError("No geometry "+id+":"+geo)
        for path in c.get("textures",{}).values():
            if not (rp/(path+".png")).is_file():raise ValueError("No texture "+id+":"+path)
        for anim in c.get("animations",{}).values():
            if anim not in anims:raise ValueError("No animation "+id+":"+anim)
    if len(server)!=11:raise ValueError("Wrong total entity count "+str(len(server)))
    print("PASS: 11 server/client definitions, models, PNG textures, animation names, archive manifests")

def build(out,has_permission,validate_only=False):
    if not (has_permission or validate_only):
        raise RuntimeError("Use --authorized-assets para redistribuição autorizada; --validate-only apenas valida localmente, sem criar pacote final.")
    out=Path(out).resolve()
    allowed=(ROOT/"build").resolve()
    if allowed not in out.parents:raise ValueError("Output must be a directory inside build/: "+str(out))
    if out.exists():shutil.rmtree(out)
    bp=out/"Minizin_Creatures_BP";rp=out/"Minizin_Creatures_RP"
    shutil.copytree(FOLDER/"BP",bp)
    write_json(rp/"manifest.json",{"format_version":2,
      "header":{"name":"Minizin Creatures RP (original resources, private stage)",
      "description":"Unverified experimental textures and Java geometry converted for Bedrock",
      "uuid":"5d1ad275-1803-4128-88c3-8f60d0f96a0a","version":[0,1,0],"min_engine_version":[1,21,90]},
      "modules":[{"type":"resources","uuid":"1511b358-9d4b-42d1-a432-6fe89107d72c","version":[0,1,0]}]})
    controllers={}
    for id,(mod,namespace,subdir,skins) in TEXTURES.items():
        if id in ("umvuthi","umvuthana"):
            source=MOD/"44-mowzies-mobs"/"upstream/src/main/resources/assets/mowziesmobs/geo"/(id+".geo.json")
        else:
            source=SRC/GEO[id]
        converted=geometry(source)
        geo_id="geometry.minizin_creatures."+id
        converted["minecraft:geometry"][0]["description"]["identifier"]=geo_id
        target=rp/"models/entity"/(id+".geo.json")
        write_json(target,converted)
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
        if id in ("umvuthi","umvuthana"):
            original_anim=MOD/"44-mowzies-mobs"/"upstream/src/main/resources/assets/mowziesmobs/animations"/(id+".animation.json")
            if not original_anim.is_file():raise FileNotFoundError("Animação original ausente: "+str(original_anim))
            sources=json.loads(original_anim.read_text(encoding="utf-8")).get("animations",{})
            selected=(("idle","solar_beam","sun_strike","flare","supernova","spawn_strix","roar") if id=="umvuthi"
                      else ("idle_neutral","attack_slash_left","attack_slash_right","heal_loop"))
            output={}
            for key in selected:
                if key not in sources:raise ValueError("Animação ausente: "+id+" "+key)
                native="animation.minizin_creatures."+id+"."+key
                output[native]=sources[key]
                animations[key]=native
            write_json(rp/"animations"/(id+".animation.json"),{"format_version":"1.8.0","animations":output})
        desc={"identifier":"minizin_creatures:"+id,"materials":{"default":"entity_alphatest"},
              "textures":textures,"geometry":{"default":geo_id},
              "render_controllers":["controller.render.minizin_creatures."+id]}
        if animations:
            desc["animations"]=animations
            desc["scripts"]={"animate":[{key:("query.property('minizin_creatures:attack') == '"+key+"'") if key not in ("idle","idle_neutral") else ("query.property('minizin_creatures:attack') == 'idle'")} for key in animations if key!="flight"]}
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
        write_json(bp/"items"/(id+".json"),{"format_version":"1.21.90","minecraft:item":{
          "description":{"identifier":"minizin_creatures:"+id,"menu_category":{"category":"items"}},
          "components":{"minecraft:icon":"minizin_creatures_"+id,
             "minecraft:display_name":{"value":id.replace("_"," ").title()},
             "minecraft:max_stack_size":64,
             "minecraft:use_modifiers":{"use_duration":0.2,"movement_modifier":1.0},
             **({"minizin_creatures:activate":{}} if id.startswith("dragon_egg_") or id in ("dragon_flute","serene_salad") else {})}}})
    write_json(rp/"textures/item_texture.json",{"resource_pack_name":"minizin_creatures","texture_name":"atlas.items","texture_data":atlas})
    sound_defs={}
    for key,(mod,namespace,path) in AUDIO.items():
        audio=MOD/mod/"upstream/src/main/resources/assets"/namespace/"sounds"/path
        if not audio.is_file():raise FileNotFoundError("Áudio original ausente: "+str(audio))
        target=rp/"sounds/creatures"/(key+".ogg");target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(audio,target)
        sound_defs["minizin_creatures."+key.replace("_",".",1)]={"category":"hostile",
          "sounds":[{"name":"sounds/creatures/"+key}]}
    write_json(rp/"sounds/sound_definitions.json",{"format_version":"1.14.0","sound_definitions":sound_defs})
    # Existing original Bluff texture/rig is packed unchanged in its own source RP/BP.
    source_mowzie=ROOT/"bedrock/packs/mowzie"
    for part in ("BP","RP"):
        shutil.copytree(source_mowzie/part,out/("Minizin_Mowzie_"+part))
    archive=out.parent/"Minizin_Creatures_Research.mcaddon"
    if archive.exists():archive.unlink()
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_STORED) as z:
        for pack in sorted(out.iterdir()):
            if not pack.is_dir():continue
            contents=io.BytesIO()
            with zipfile.ZipFile(contents,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as inner:
                for path in sorted(pack.rglob("*")):
                    if path.is_file():inner.write(path,path.relative_to(pack).as_posix())
            z.writestr(pack.name+".mcpack",contents.getvalue())
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=4 or not all(n.endswith(".mcpack") for n in names):
            raise ValueError("Pack count/format invalid")
        for name in names:
            with zipfile.ZipFile(io.BytesIO(z.read(name))) as package:
                if "manifest.json" not in package.namelist():
                    raise ValueError("Manifest missing: "+name)
    check_staged(rp,bp)
    if validate_only:
        archive.unlink()
        shutil.rmtree(out)
        return "VALIDATED (temporary assets destroyed, no redistributable output)"
    return archive
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorized-assets",action="store_true")
    parser.add_argument("--validate-only",action="store_true")
    parser.add_argument("--output",default=str(ROOT/"build/creatures_staged"))
    args=parser.parse_args()
    try:print(build(Path(args.output),args.authorized_assets,args.validate_only))
    except (RuntimeError,FileNotFoundError,KeyError,ValueError) as err:
        print("CREATURES BUILD FAILED: "+str(err),file=sys.stderr);return 2
    return 0
if __name__=="__main__":sys.exit(main())
