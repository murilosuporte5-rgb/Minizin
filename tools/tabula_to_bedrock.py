#!/usr/bin/env python3
"""Convert Tabula (.tbl ZIP of model.json) to Bedrock geometry (prototype).

Preserves source cuboids, texture atlas dimensions, names, parent graph,
pivot translation and Euler rotations. Mapping from legacy Tabula/Java model
coordinates to Bedrock requires visual QA. NO animation, code or AI port.
Use on legally permissioned source files and keep results in build/.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

def read_tabula(file: Path) -> dict:
    if not zipfile.is_zipfile(file):
        raise ValueError(f"Not a Tabula ZIP: {file}")
    with zipfile.ZipFile(file) as z:
        options=[name for name in z.namelist() if name.endswith("model.json")]
        if not options: raise ValueError("Tabula model.json missing")
        return json.loads(z.read(options[0]))

def vector(value, name, *, default=None):
    if value is None: value=default
    if not isinstance(value,(list,tuple)) or len(value)!=3:
        raise ValueError(f"{name}: expected 3D vector")
    result=[float(x) for x in value]
    if not all(math.isfinite(x) for x in result):
        raise ValueError(f"{name}: nonfinite vector")
    return result

def sanitize(value: str) -> str:
    out=re.sub(r"[^a-zA-Z0-9_]", "_", value.strip())
    return out[:80] or "unnamed"

def export_tabula(model: dict, identifier="geometry.minizin.tabula", *, flip_x=False) -> tuple[dict,dict]:
    w=int(model["textureWidth"])
    h=int(model["textureHeight"])
    if min(w,h)<1: raise ValueError("Invalid source UV atlas")
    roots=model.get("cubes",[])
    if not isinstance(roots,list): raise ValueError("Unexpected Tabula cube root")
    bones=[]
    report={"source_name":model.get("modelName"),"atlas":[w,h],
            "model_boxes":0,"bones":0,"issues":[],"original_cubes_hint":model.get("cubeCount"),
            "mapping":"Tabula Y-down model convention -> Bedrock Y-up; visual QA required."}
    seen=set()
    # Geometry scaled in Minecraft's model-unit space (1 unit = 1/16 block)
    bbox=[math.inf,math.inf,math.inf,-math.inf,-math.inf,-math.inf]
    def child_part(part,parent=None,parent_pivot=(0,0,0),depth=0):
        if depth>80: raise ValueError("Exceeded bone hierarchy depth")
        if not isinstance(part,dict): raise ValueError("Non-object Tabula cuboid")
        base=sanitize(str(part.get("name","part")))
        name=base
        n=2
        while name in seen:
            name=f"{base}_{n}"
            n+=1
        seen.add(name)
        local=vector(part.get("position"),name+".position",default=[0,0,0])
        offset=vector(part.get("offset"),name+".offset",default=[0,0,0])
        size=vector(part.get("dimensions"),name+".dimensions",default=[0,0,0])
        angles=vector(part.get("rotation"),name+".rotation",default=[0,0,0])
        pv=(parent_pivot[0]+local[0],parent_pivot[1]+local[1],parent_pivot[2]+local[2])
        # Java Tabula convention is +Y downward (Minecraft ModelBox local coordinates).
        pivot=[-pv[0] if flip_x else pv[0],24.0-pv[1],pv[2]]
        bone={"name":name,"pivot":pivot}
        if parent: bone["parent"]=parent
        bone["rotation"]=[-angles[0],-angles[1],angles[2]]
        cubes=[]
        if all(s>0 for s in size):
            # Source cuboid is located at 'offset' relative to the joint.
            origin=[pv[0]+offset[0],24.0-(pv[1]+offset[1]+size[1]),pv[2]+offset[2]]
            if flip_x: origin[0]=-(origin[0]+size[0])
            uv=part.get("txOffset",[0,0])
            if not isinstance(uv,(list,tuple)) or len(uv)!=2:
                raise ValueError("Invalid txOffset: "+name)
            cube={"origin":origin,"size":size,"uv":[int(uv[0]),int(uv[1])]}
            if part.get("txMirror"):cube["mirror"]=True
            if any(abs(s-1.0)>0.0001 for s in part.get("scale",[1,1,1])):
                report["issues"].append(f"{name}: non-unit Tabula scale; needs geometry bake")
            if part.get("mcScale",0):
                inflate=float(part["mcScale"])
                cube["inflate"]=inflate
            cubes.append(cube)
            report["model_boxes"]+=1
            for a in range(3):
                bbox[a]=min(bbox[a],origin[a])
                bbox[a+3]=max(bbox[a+3],origin[a]+size[a])
        bone["cubes"]=cubes
        bones.append(bone)
        for child in part.get("children",[]) or []:
            child_part(child,name,pv,depth+1)
    for part in roots: child_part(part)
    if not bones: raise ValueError("Model has no bones")
    report["bones"]=len(bones)
    maxAbs=max(abs(v) for v in bbox if math.isfinite(v)) if report["model_boxes"] else 24
    # Bound values are in blocks, rounded up with safety padding.
    vw=max(3,math.ceil((bbox[3]-bbox[0])/16+2)) if report["model_boxes"] else 4
    vh=max(3,math.ceil((bbox[4]-bbox[1])/16+2)) if report["model_boxes"] else 4
    desc={"identifier":identifier,"texture_width":w,"texture_height":h,
          "visible_bounds_width":vw,"visible_bounds_height":vh,
          "visible_bounds_offset":[0,1,0]}
    geom={"format_version":"1.12.0",
          "minecraft:geometry":[{"description":desc,"bones":bones}]}
    report["issues"] += [
        "No animation or AI converted; base geometry only.",
        "Requires review of axis signs, yaw/pitch/roll, mirror UV and Tabula inherited pivots.",
        "Animations and large entity visible bounds must be tested in Minecraft Bedrock.",
        "Source license and redistribution permissions require confirmation.",
    ]
    report["max_abs_model_coord"]=maxAbs
    return geom,report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("tabula",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--identifier",default="geometry.minizin.tabula")
    p.add_argument("--flip-x",action="store_true",help="Optional coordinate mirror, not default")
    a=p.parse_args()
    try:
        model=read_tabula(a.tabula)
        result,report=export_tabula(model,a.identifier,flip_x=a.flip_x)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        report_path=a.output.with_suffix(".conversion.json")
        report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"geometry":str(a.output),"report":str(report_path),
                          "source_name":report["source_name"],"bones":report["bones"],
                          "cubes":report["model_boxes"],"atlas":report["atlas"]}))
    except Exception as e:
        print("conversion failed:",e,file=sys.stderr)
        sys.exit(1)

if __name__=="__main__":main()
