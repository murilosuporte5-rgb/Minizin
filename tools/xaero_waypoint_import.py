#!/usr/bin/env python3
"""Read-only importer of Xaero's Minimap waypoint .txt format into Bedrock-friendly JSON.

Source format documented for releases 23.9.7 and later in Conflux-Union's
waypoint storage format reference. NEVER changes original files or teleports.
Conversion preserves dimension/world identifiers so coordinates are not confused.
"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

PALETTE=["#000000","#0000AA","#00AA00","#00AAAA","#AA0000","#AA00AA",
         "#FFAA00","#AAAAAA","#555555","#5555FF","#55FF55","#55FFFF",
         "#FF0000","#FF55FF","#FFFF55","#FFFFFF"]
DIMENSIONS={"dim%0":"minecraft:overworld","dim%-1":"minecraft:nether","dim%1":"minecraft:the_end"}
LOCAL_NAMES={"gui.xaero_default":"Default","gui.xaero_deathpoint":"Latest Death",
             "gui.xaero_deathpoint_old":"Old Death"}

def parse_bool(raw,default=False):
    if raw is None:return default
    if raw=="true":return True
    if raw=="false":return False
    raise ValueError("invalid boolean "+raw)

def parse_dimension(folder):
    if folder in DIMENSIONS:return DIMENSIONS[folder]
    if folder in ("Overworld","Nether","The End"):
        return {"Overworld":"minecraft:overworld","Nether":"minecraft:nether","The End":"minecraft:the_end"}[folder]
    if not folder.startswith("dim%"):return None
    value=folder[4:]
    if "$" in value:
        ns,ident=value.split("$",1)
        return ns+":"+ident.replace("%","/")
    return "legacy:"+value if re.fullmatch("-?[0-9]+",value) else None

def display_name(raw):
    text=raw.replace("§§",":")
    return LOCAL_NAMES.get(text,text)

def read_waypoints(path:Path):
    output=[]
    stats={"read":0,"skipped":0,"reason_counts":{}}
    for lineno,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.startswith("waypoint:"):continue
        stats["read"]+=1
        tokens=line.split(":")
        try:
            if len(tokens)<10:raise ValueError("fewer than 10 tokens")
            name,initials=tokens[1:3]
            x=int(tokens[3]);y=None if tokens[4]=="~" else int(tokens[4]);z=int(tokens[5])
            raw_color=int(tokens[6]);disabled=parse_bool(tokens[7])
            kind=int(tokens[8]);which_set=tokens[9]
            rotate=parse_bool(tokens[10]) if len(tokens)>10 else False
            yaw=int(tokens[11]) if len(tokens)>11 else 0
            visibility=tokens[12] if len(tokens)>12 else "0"
            if visibility in ("true","false"):visibility="1" if visibility=="true" else "0"
            visibility=int(visibility)
            destination=parse_bool(tokens[13]) if len(tokens)>13 else False
            if kind in (1,2):visibility=1;destination=True
            color_index=(max(0,raw_color))%16
            output.append({"name":display_name(name),"initials":display_name(initials),
                "x":x,"y":y,"z":z,"color":PALETTE[color_index],
                "color_index":color_index,"disabled":disabled,"type":kind,
                "set":display_name(which_set),"rotate_on_tp":rotate,"yaw":yaw,
                "visibility_type":visibility,"destination":destination,
                "source_line":lineno})
        except (ValueError,IndexError) as error:
            stats["skipped"]+=1
            key=str(error)
            stats["reason_counts"][key]=stats["reason_counts"].get(key,0)+1
    return output,stats

def find_waypoint_files(root:Path):
    if root.is_file():return [root]
    preferred=[root/"xaero/minimap",root/"XaeroWaypoints"]
    base=next((f for f in preferred if f.is_dir()),root)
    return sorted(p for p in base.rglob("*.txt")
        if p.name!="config.txt" and not p.name.endswith(".txt.temp")
        and not any(d in p.parts for d in ("backup","temp_to_add"))
        and any(f.startswith("dim%") or f in ("Overworld","Nether","The End") for f in p.parts))

def classify(path):
    dimfolder=next((s for s in reversed(path.parts[:-1]) if parse_dimension(s)),None)
    world=None
    if dimfolder:
        parts=path.parts;at=max(i for i,p in enumerate(parts) if p==dimfolder)
        if at>0:world=parts[at-1]
    return world,parse_dimension(dimfolder) if dimfolder else None

def convert(source:Path):
    files=find_waypoint_files(source)
    entries=[];summary={"files":len(files),"parsed":0,"skipped":0,"errors":[]}
    for file in files:
        try:
            rows,stats=read_waypoints(file);world,dim=classify(file)
            multiworld=None if file.name=="waypoints.txt" else file.stem
            for row in rows:
                entries.append({**row,"world":world,"dimension":dim,"multiworld":multiworld,
                    "source_file":str(file)})
            summary["parsed"]+=len(rows);summary["skipped"]+=stats["skipped"]
        except Exception as e:
            summary["errors"].append({"file":str(file),"error":str(e)})
    return {"schema":"minizin:xaero_waypoints_v1","metadata":summary,
            "waypoints":entries,
            "notice":"For importing/display only. No automatic teleport. Bedrock dimension and world identifiers must be validated."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path,help="Game directory, Xaero root or single waypoint .txt")
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        doc=convert(a.source)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(doc["metadata"]))
        print("Saved",a.output)
        if doc["metadata"]["errors"]:return 2
    except Exception as e:
        print("import error:",e,file=sys.stderr);return 1
    return 0
if __name__=="__main__":sys.exit(main())
