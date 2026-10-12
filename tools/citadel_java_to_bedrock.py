#!/usr/bin/env python3
"""Recover static Citadel AdvancedModelBox Java cuboids as Bedrock geometry.

Parses constructor setup from ordered source files, including a base model class.
Not a Java interpreter. Expressions, dynamic transformations, procedural meshes
and animations require manual follow-up. Verify all output visually.
"""
from __future__ import annotations
import argparse, json, math, re, sys
from pathlib import Path

NAME=r"([A-Za-z_$][A-Za-z0-9_$]*)"
NUM=r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?[FfDd]?)"
def parse_num(s): return float(s.removesuffix("F").removesuffix("f").removesuffix("D").removesuffix("d"))
def find_calls(pattern, text):
    return [(m.start(), m.groups()) for m in re.finditer(pattern,text,re.MULTILINE)]
def recover_models(sources:list[str],identifier="geometry.minizin.citadel"):
    all_part={}
    report={"classes":len(sources),"unsupported":[],"models":[],"box_total":0}
    texture_w=texture_h=None
    for source in sources:
        # Constructor state only: later render methods set temporary transformations.
        cut=source.find("this.updateDefaultPose();")
        if cut>0: source=source[:cut]
        for key,property_name in [("texWidth","width"),("texHeight","height")]:
            vals=re.findall(r"\b"+key+r"\s*=\s*(\d+)\s*;",source)
            if vals:
                if property_name=="width":texture_w=int(vals[-1])
                else:texture_h=int(vals[-1])
        num=NUM
        # Handles parent.addChild(child), child.setRotationPoint(x,y,z)
        events=[]
        events+= [(p,"new",args) for p,args in find_calls(rf"({NAME[1:-1]})\s*=\s*new\s+AdvancedModelBox\s*\(\s*this\s*\)",source)]
        events+= [(p,"point",args) for p,args in find_calls(rf"{NAME}\.setRotationPoint\(\s*{num}\s*,\s*{num}\s*,\s*{num}\s*\)",source)]
        events+= [(p,"child",args) for p,args in find_calls(rf"{NAME}\.addChild\(\s*{NAME}\s*\)",source)]
        events+= [(p,"rotate",args) for p,args in find_calls(rf"setRotat(?:e|ion)Angle\(\s*{NAME}\s*,\s*{num}\s*,\s*{num}\s*,\s*{num}\s*\)",source)]
        events+= [(p,"box",args) for p,args in find_calls(
            rf"{NAME}\.setTextureOffset\(\s*{num}\s*,\s*{num}\s*\)\.addBox\(\s*"
            rf"{num}\s*,\s*{num}\s*,\s*{num}\s*,\s*{num}\s*,\s*{num}\s*,\s*{num}\s*,\s*{num}\s*,\s*(true|false)\s*\)",source)]
        events.sort(key=lambda x:x[0])
        for p,tag,args in events:
            if tag=="new":
                name=args[0]
                all_part[name]={"name":name,"pos":[0,0,0],"angle":[0,0,0],"parent":None,"cubes":[]}
            elif tag=="point":
                name=args[0]
                if name in all_part:all_part[name]["pos"]=[parse_num(v) for v in args[1:]]
            elif tag=="child":
                par,name=args
                if name in all_part:all_part[name]["parent"]=par
            elif tag=="rotate":
                name=args[0]
                if name in all_part:all_part[name]["angle"]=[math.degrees(parse_num(v)) for v in args[1:]]
            elif tag=="box":
                name=args[0]
                if name in all_part:
                    vals=[parse_num(v) for v in args[1:10]]
                    u,v,x,y,z,dx,dy,dz,inflate=vals
                    mirror=args[10]=="true"
                    all_part[name]["cubes"].append({"offset":[x,y,z],"size":[dx,dy,dz],
                        "inflate":inflate,"uv":[int(u),int(v)],"mirror":mirror})
        report["models"].append({"parsed_classes":len(all_part),"events":len(events)})
    if not all_part: raise ValueError("No AdvancedModelBox declarations detected")
    if texture_w is None or texture_h is None:
        raise ValueError("Unknown texture dimension: pass model declaring texWidth and texHeight")
    all_bones=[]
    memo={}
    def world_pos(name,stack=()):
        if name in memo:return memo[name]
        if name in stack: raise ValueError("Parent cycle at "+name)
        p=all_part[name]
        parent=p["parent"]
        if parent and parent in all_part:
            q=world_pos(parent,(*stack,name))
        elif parent:
            report["unsupported"].append(f"missing inherited parent: {name} -> {parent}")
            q=[0,0,0]
        else:q=[0,0,0]
        out=[q[k]+p["pos"][k] for k in range(3)]
        memo[name]=out
        return out
    for name,part in all_part.items():
        wpos=world_pos(name)
        bone={"name":name,"pivot":[wpos[0],24-wpos[1],wpos[2]],
              "rotation":[-part["angle"][0],-part["angle"][1],part["angle"][2]]}
        if part["parent"] in all_part:bone["parent"]=part["parent"]
        bone["cubes"]=[]
        for c in part["cubes"]:
            x,y,z=c["offset"];dx,dy,dz=c["size"]
            cube={"origin":[wpos[0]+x,24-(wpos[1]+y+dy),wpos[2]+z],
                  "size":[dx,dy,dz],"uv":c["uv"]}
            if c["inflate"]:cube["inflate"]=c["inflate"]
            if c["mirror"]:cube["mirror"]=True
            if 0 in (dx,dy,dz):report["unsupported"].append(f"{name}: thin plane; Bedrock zero-size cube behavior requires QA")
            bone["cubes"].append(cube)
            report["box_total"]+=1
        all_bones.append(bone)
    desc={"identifier":identifier,"texture_width":texture_w,"texture_height":texture_h,
          "visible_bounds_width":20,"visible_bounds_height":20,"visible_bounds_offset":[0,1,0]}
    geom={"format_version":"1.12.0","minecraft:geometry":[{"description":desc,"bones":all_bones}]}
    report.update({"bones":len(all_bones),"texture":[texture_w,texture_h],"unmodeled_animation":True})
    report["unsupported"]+=["Animation/runtime poses not recovered.","Inherited rotations need visual QA.",
                           "Large model render bounds are approximate.","Not game-tested."]
    return geom,report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",action="append",type=Path,required=True,help="Pass base model first, subclass second")
    p.add_argument("--identifier",default="geometry.minizin.citadel")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        geo,report=recover_models([path.read_text() for path in a.source],a.identifier)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(geo,indent=2)+"\n")
        a.output.with_suffix(".conversion.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({"output":str(a.output),"bones":report["bones"],
                          "boxes":report["box_total"],"texture":report["texture"],
                          "warnings":len(report["unsupported"])}))
    except Exception as error:
        print("Citadel recovery failed:",error,file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":main()
