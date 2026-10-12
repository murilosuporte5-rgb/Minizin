#!/usr/bin/env python3
"""Specialized reverse-engineering inventories for MCA, Carry On, RFTools, Origins.

Consumes outputs from tools/extract_next_four.py. No Minecraft runtime needed.
Reports are file-grounded: no inferences about game feature completeness.
"""
from __future__ import annotations
import argparse,collections,json,struct,sys
from pathlib import Path

def load_manifest(root):
    return json.loads((root/"inventory.json").read_text(encoding="utf-8"))["files"]
def json_docs(root,records,predicate):
    for rec in records:
        if rec["category"] in ("java_model_json","origin_power","origin_definition",
                               "origin_layer","tag_json","json_data") and predicate(rec["source"]):
            p=root/"original"/rec["source"]
            try:yield rec["source"],json.loads(p.read_text(encoding="utf-8-sig"))
            except (UnicodeError,ValueError) as e:
                raise ValueError(f"Invalid upstream JSON {p}: {e}") from e
def png_dimensions(path):
    with path.open("rb") as f:data=f.read(24)
    if len(data)!=24 or data[:8]!=b"\x89PNG\r\n\x1a\n" or data[12:16]!=b"IHDR":
        return None
    return struct.unpack(">II",data[16:24])
def resource_root(rel):
    k=rel.find("/assets/")
    if k!=-1:return rel[k+8:]
    if rel.startswith("assets/"):return rel[7:]
    return None

def mca_analysis(root,files):
    skins=[];model_refs=[];missing=[];texture_sizes=collections.Counter()
    all_paths={resource_root(rec["source"]) for rec in files if rec["category"]=="png_texture"}
    for rec in files:
        if "/assets/mca/skins/" in rec["source"]:
            d=png_dimensions(root/"original"/rec["source"]) if rec["source"].endswith(".png") else None
            skins.append({"source":rec["source"],"pixel_size":d,"bytes":rec["bytes"],"sha256":rec["sha256"]})
            if d:texture_sizes[str(d)]+=1
    for name,obj in json_docs(root,files,lambda p:"/assets/mca/models/" in p):
        textures=obj.get("textures",{})
        refs=[]
        for key,target in textures.items():
            if not isinstance(target,str):continue
            if target.startswith("#"):continue
            ns,sub=target.split(":",1) if ":" in target else ("minecraft",target)
            available=(f"{ns}/textures/{sub}.png" in all_paths)
            refs.append({"layer":key,"texture":target,"exists_locally":available})
            if not available and ns=="mca":missing.append({"model":name,"texture":target})
        model_refs.append({"source":name,"parent":obj.get("parent"),"textures":refs,
                           "geometry_elements":len(obj.get("elements",[]))})
    return {"mod":"mca","skins":len(skins),"skin_dimensions":dict(texture_sizes),
        "skin_index":skins,"model_json":len(model_refs),"models":model_refs,
        "missing_local_mca_textures":missing,
        "notice":"Layered 2D crib item textures are not automatically 3D entity geometries; villager rigs are Java ModelPart."}

def carryon_analysis(root,files):
    tags=[]
    for name,obj in json_docs(root,files,lambda p:"/data/carryon/tags/" in p):
        tags.append({"source":name,"replace":obj.get("replace",False),
                     "values":obj.get("values",[]),"entries":len(obj.get("values",[]))})
    java=[{"source":f["source"],"bytes":f["bytes"]}
        for f in files if f["source"].endswith(".java")]
    return {"mod":"carryon","tags":tags,"source_java":java,
      "rendering":"The mod relies on client-side vanilla/block/entity renderers, not a separate library of custom 3D models.",
      "note":"Empty whitelist/blacklist JSON alone does not define full rules; config and Java guards must be interpreted."}

def parse_obj(path):
    verts=[];normals=0;uvs=0;faces=0;groups=collections.Counter();materials=set()
    mtllibs=[];active="none"
    for raw in path.read_text(encoding="utf-8-sig",errors="replace").splitlines():
        if raw.startswith("v "):
            t=raw.split()
            if len(t)>=4:verts.append([float(x) for x in t[1:4]])
        elif raw.startswith("vn "):normals+=1
        elif raw.startswith("vt "):uvs+=1
        elif raw.startswith("f "):
            faces+=1
            cells=raw.split()[1:]
            if len(cells)<3:raise ValueError("Degenerate OBJ face")
            for elem in cells:
                a=elem.split("/")[0]
                if int(a)==0:raise ValueError("OBJ face vertex index zero")
            groups[active]+=1
        elif raw.startswith("usemtl "):
            active=raw.split(maxsplit=1)[1];materials.add(active)
        elif raw.startswith("mtllib "):mtllibs.append(raw.split(maxsplit=1)[1])
    if not verts or not faces:raise ValueError("Missing mesh data "+str(path))
    return {"vertices":len(verts),"normals":normals,"texture_coords":uvs,
            "faces":faces,"face_materials":dict(groups),"material_names":sorted(materials),
            "material_libraries":mtllibs,
            "bounds":{"min":[min(v[i] for v in verts) for i in range(3)],
                      "max":[max(v[i] for v in verts) for i in range(3)]}}
def rftools_analysis(root,files):
    obj=[];blend=[];mtls=[]
    for f in files:
        name=f["source"];p=root/"original"/name
        if name.endswith(".obj"):
            obj.append({"source":name,**parse_obj(p)})
        elif name.endswith(".mtl"):
            textures=[line[7:].strip() for line in p.read_text(errors="replace").splitlines()
                      if line.strip().startswith("map_Kd ")]
            mtls.append({"source":name,"diffuse_maps":textures})
        elif name.endswith(".blend"):
            h=p.read_bytes()[:12]
            blend.append({"source":name,"valid_blender_header":h.startswith(b"BLENDER"),
                          "size":f["bytes"],"signature":h.decode("ascii","replace")})
    model_files=[f["source"] for f in files if f["category"]=="java_model_json"]
    return {"mod":"rftools","obj":obj,"blender":blend,"materials":mtls,
            "json_models":len(model_files),"model_examples":model_files[:30],
            "warning":"OBJ triangles/quads cannot be losslessly represented as Bedrock cuboids; preserve mesh and UV for Blender/Blockbench conversion."}

def origins_analysis(root,files):
    base="/data/origins/"
    powers={};origins={};layers={}
    for name,obj in json_docs(root,files,lambda p:base in p):
        if base+"powers/" in name and name.endswith(".json"):
            power="origins:"+Path(name).stem
            powers[power]={"source":name,"type":obj.get("type"),"fields":sorted(obj)}
        elif base+"origins/" in name and name.endswith(".json"):
            origin="origins:"+Path(name).stem
            origins[origin]={"source":name,"powers":obj.get("powers",[]),
                             "icon":obj.get("icon"),"impact":obj.get("impact"),
                             "order":obj.get("order")}
        elif base+"origin_layers/" in name and name.endswith(".json"):
            layers["origins:"+Path(name).stem]={"source":name,"origins":obj.get("origins",[])}
    links=[];missing=[]
    for origin,detail in origins.items():
        for key in detail["powers"]:
            external=key.split(":")[0]!="origins"
            found=key in powers
            links.append({"origin":origin,"power":key,"has_local_json":found,"external_namespace":external})
            if not found:missing.append({"origin":origin,"power":key})
    return {"mod":"origins","origins":origins,"powers":powers,
            "layers":layers,"power_type_counts":dict(collections.Counter(p.get("type") for p in powers.values())),
            "origin_power_links":links,"missing_local_power_json":missing,
            "note":"A JSON reference is data, not a Bedrock Script API implementation. Some power kinds rely on Apoli's Java runtime."}

ANALYZERS={"mca":mca_analysis,"carryon":carryon_analysis,
           "rftools":rftools_analysis,"origins":origins_analysis}
def analyze(mod,root):
    if mod not in ANALYZERS:raise ValueError("Unknown mod "+mod)
    files=load_manifest(root)
    report=ANALYZERS[mod](root,files)
    (root/"format_analysis.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                                             encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mod",required=True,choices=sorted(ANALYZERS))
    p.add_argument("--stage",type=Path,required=True)
    a=p.parse_args()
    try:
        data=analyze(a.mod,a.stage)
        print(json.dumps({"mod":a.mod,"keys":list(data),
             "counts":{k:v for k,v in data.items() if isinstance(v,int)}},ensure_ascii=False))
    except Exception as exc:print("Audit failed:",exc,file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
