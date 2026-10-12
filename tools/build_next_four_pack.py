#!/usr/bin/env python3
"""Stage an experimental Bedrock BP/RP reusing original next-four source assets.

No source art is committed to Minizin by this script: images and 3D OBJ stay
in ignored build/. Read upstream LICENSE files before redistributing outputs.
Behavior code for four experiments is in bedrock/packs/next_four/BP/scripts.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,shutil,sys,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/"bedrock/packs/next_four"
SOURCES={
 "mca":ROOT/"mods/33-mca-reborn/upstream",
 "carryon":ROOT/"mods/34-carry-on/upstream",
 "rftools":ROOT/"mods/54-rftools/upstream",
 "origins":ROOT/"mods/55-origins/upstream",
}
PASSIVES={"avian":("slow_falling","Queda lenta"),"blazeborn":("fire_resistance","Resistência ao fogo"),
          "feline":("night_vision","Visão noturna"),"merling":("water_breathing","Respiração aquática")}

def src(mod,rel):
    p=SOURCES[mod]/rel
    if not p.is_file():raise FileNotFoundError(f"Missing source: {mod} / {rel}; initialize submodules")
    return p
def copy_provenanced(mod,rel,target,provenance):
    original=src(mod,rel)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original,target)
    data=target.read_bytes()
    provenance.append({"upstream":mod,"source":rel,"output":str(target),
                       "sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
    return target

def build_catalog(bp:Path):
    folder=SOURCES["origins"]/"src/main/resources/data/origins/origins"
    definitions={}
    for file in sorted(folder.glob("*.json")):
        data=json.loads(file.read_text(encoding="utf-8"))
        definitions[file.stem]=data
    if len(definitions)<10:raise ValueError("Missing original Origins JSON definitions")
    entries=[]
    for name,doc in definitions.items():
        entries.append({"id":name,"label":name.replace("_"," ").title(),
                        "powers":doc.get("powers",[]),"impact":doc.get("impact"),
                        "icon":doc.get("icon")})
    entries.sort(key=lambda d:(definitions[d["id"]].get("order",999),d["id"]))
    passives={k:{"effect":v[0],"title":v[1]} for k,v in PASSIVES.items()}
    js="// Generated from pinned Origins Fabric origin definitions; don't hand-edit.\n"
    js+="export const ORIGINS_CATALOG="+json.dumps(entries,ensure_ascii=False,separators=(",",":"))+";\n"
    js+="export const IMPLEMENTED_PASSIVES="+json.dumps(passives,ensure_ascii=False)+";\n"
    target=bp/"scripts/catalog.js"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(js,encoding="utf-8")
    return entries

def compose_mca(rp:Path,provenance):
    sourcebase="common/src/main/resources/assets/mca/skins/"
    input_rel=[
        sourcebase+"skin/female/0.png",
        sourcebase+"face/normal/0.png",
        sourcebase+"hair/female/0.png",
        sourcebase+"clothing/normal/female/armorer/0.png",
    ]
    original=[src("mca",rel) for rel in input_rel]
    images=[Image.open(p).convert("RGBA") for p in original]
    size=images[0].size
    if size!=(64,64) or any(im.size!=size for im in images):
        raise ValueError("MCA layered-skin dimensions differ; refuse to rescale silently")
    result=images[0]
    for layer in images[1:]:
        result=Image.alpha_composite(result,layer)
    target=rp/"textures/minizin/mca/female_armorer_composite.png"
    target.parent.mkdir(parents=True,exist_ok=True)
    result.save(target)
    provenance.append({"upstream":"mca","source_layers":input_rel,
                       "output":str(target),"size":list(size),
                       "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                       "type":"composition_of_original_64x64_skin_layers"})
    return target

def asset_sources(out:Path,provenance):
    rp=out/"RP"
    for mod,original,output in [
       ("origins","src/main/resources/assets/origins/textures/gui/badge/star.png",
        "textures/minizin/origins/star.png"),
       ("origins","src/main/resources/assets/origins/textures/gui/choose_origin.png",
        "textures/minizin/origins/choose_origin.png"),
       ("rftools","src/main/resources/assets/rftools/textures/gui/powercell.png",
        "textures/minizin/rftools/powercell.png"),
    ]:
       copy_provenanced(mod,original,rp/output,provenance)
    compose_mca(rp,provenance)
    # Preserve the exact original powercell mesh/UV/material for later Blender conversion.
    obj_root=out/"original_meshes/rftools"
    for f in ("powercell.obj","powercell.mtl","environmental.obj","environmental.mtl"):
        copy_provenanced("rftools","src/main/resources/assets/rftools/models/block/"+f,obj_root/f,provenance)
    for f in ("powercell.blend","environmental.blend"):
        copy_provenanced("rftools","art/"+f,obj_root/f,provenance)
    # CarryOn intentionally uses vanilla visuals; preserve original rules as a reference only.
    for type_name,folder in (("blocks","blocks"),("entities","entity_types")):
        for suffix in ("blacklist","whitelist"):
            prefix="block" if type_name=="blocks" else "entity"
            filename=prefix+"_"+suffix+".json"
            orig="Common/src/main/resources/data/carryon/tags/"+folder+"/"+filename
            target=out/"original_rules/carryon"/filename
            copy_provenanced("carryon",orig,target,provenance)
    for mod,license_name in (("mca","LICENSE"),("carryon","LICENSE"),
                              ("rftools","LICENSE.md"),("origins","LICENSE")):
        copy_provenanced(mod,license_name,out/"licenses"/(mod+".txt"),provenance)

def pack(folder:Path):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():z.write(p,p.relative_to(folder).as_posix())
    return buf.getvalue()

def build(out:Path):
    if out.resolve().is_relative_to((ROOT/".git").resolve()):raise ValueError("Output cannot be inside .git")
    if out.exists():shutil.rmtree(out)
    bp=out/"BP";rp=out/"RP"
    shutil.copytree(BASE/"BP",bp)
    shutil.copytree(BASE/"RP",rp)
    origin_defs=build_catalog(bp)
    provenance=[]
    asset_sources(out,provenance)
    # Metadata and reports only; never auto-publish original models in git.
    report={"origin_count":len(origin_defs),"original_images":4,
            "experimental_features":["Origins origin selection and 4 passive status effects",
             "Carry On same-entity following for four animals",
             "MCA vanilla villager reputation dialogue",
             "RFTools lodestone+redstone energy demonstration"],
            "source_files":provenance,
            "warnings":["Not a port of the four Java mods.",
                        "Skin composite is a 2D preview and not connected to a villager renderer.",
                        "RFTools original OBJ/Blend preserved for manual UV/mesh conversion; no fabricated .geo.json.",
                        "Must test on a real Minecraft Bedrock Android client."]}
    (out/"asset_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    dest=out/"Minizin_Next_Four_Prototype.mcaddon"
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_STORED) as bundle:
        bundle.writestr("Minizin_Next_Four_BP.mcpack",pack(bp))
        bundle.writestr("Minizin_Next_Four_RP.mcpack",pack(rp))
    with zipfile.ZipFile(dest) as bundle:
        for name in bundle.namelist():
            with zipfile.ZipFile(io.BytesIO(bundle.read(name))) as sub:
                assert "manifest.json" in sub.namelist()
    print(json.dumps({"mcaddon":str(dest),"bytes":dest.stat().st_size,
        "origin_definitions":len(origin_defs),"source_items":len(provenance)},ensure_ascii=False))
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/"build/next_four")
    opts=ap.parse_args()
    try:build(opts.output)
    except Exception as e:print("Build failure:",e,file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
