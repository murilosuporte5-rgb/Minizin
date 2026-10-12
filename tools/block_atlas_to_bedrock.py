#!/usr/bin/env python3
"""Experimental loss-aware Java block model -> Bedrock geo + image atlas.

Only converts source geometry/UV and original PNG textures. Java shader,
animation, biome rules and blockstate orientation still need custom logic.
Requires pillow: pip install Pillow. Generated assets remain under build/.
"""
from __future__ import annotations
import argparse, json, math, re, sys
from pathlib import Path
from PIL import Image

RESOURCE_PREFIXES=("common/src/main/resources","common/src/generated/resources",
                   "src/main/resources","src/generated/resources")
FACES=("north","south","east","west","up","down")

def json_model(root,ns,key):
    srcns,rel=key.split(":",1) if ":" in key else (ns,key)
    for prefix in RESOURCE_PREFIXES:
        path=root/prefix/"assets"/srcns/"models"/(rel+".json")
        if path.exists():return json.loads(path.read_text())
    raise FileNotFoundError("model not found "+key)

def texture_file(root,ns,loc):
    srcns,rel=loc.split(":",1) if ":" in loc else (ns,loc)
    for prefix in RESOURCE_PREFIXES:
        path=root/prefix/"assets"/srcns/"textures"/(rel+".png")
        if path.exists():return path
    raise FileNotFoundError("texture not found "+loc)

def cube_faces(all_ref):
    return {k:{"texture":all_ref,"uv":[0,0,16,16]} for k in FACES}

def placeholder(parent):
    base=parent.removeprefix("minecraft:")
    if base in ("block/block",):return {"textures":{},"elements":[]}
    if base=="block/cube_all":
        return {"textures":{},"elements":[{"from":[0,0,0],"to":[16,16,16],
                 "faces":cube_faces("#all")}]}
    if base in ("block/cube_bottom_top","block/cube_column"):
        end="#end" if base=="block/cube_column" else None
        t=end or "#top";b=end or "#bottom"
        faces={k:{"texture":"#side","uv":[0,0,16,16]} for k in FACES}
        faces["up"]["texture"]=t;faces["down"]["texture"]=b
        return {"elements":[{"from":[0,0,0],"to":[16,16,16],"faces":faces}]}
    if base=="block/cube":
        faces={k:{"texture":"#"+k,"uv":[0,0,16,16]} for k in FACES}
        return {"elements":[{"from":[0,0,0],"to":[16,16,16],"faces":faces}]}
    if base in ("block/slab","block/slab_top"):
        yy=(8,16) if base.endswith("_top") else (0,8)
        faces={k:{"texture":"#side","uv":[0,0,16,8]} for k in FACES}
        faces["up"]={"texture":"#top","uv":[0,0,16,16]}
        faces["down"]={"texture":"#bottom","uv":[0,0,16,16]}
        return {"elements":[{"from":[0,yy[0],0],"to":[16,yy[1],16],"faces":faces}]}
    if base in ("block/cross","block/tinted_cross"):
        return {"elements":[
            {"from":[0,0,8],"to":[16,16,8.01],
             "rotation":{"axis":"y","angle":45,"origin":[8,8,8]},
             "faces":{"north":{"texture":"#cross","uv":[0,0,16,16]},
                      "south":{"texture":"#cross","uv":[0,0,16,16]}}},
            {"from":[0,0,8],"to":[16,16,8.01],
             "rotation":{"axis":"y","angle":-45,"origin":[8,8,8]},
             "faces":{"north":{"texture":"#cross","uv":[0,0,16,16]},
                      "south":{"texture":"#cross","uv":[0,0,16,16]}}}
        ]}
    raise ValueError("unhandled parent "+parent)

def resolve(root,ns,name,seen=()):
    if name in seen:raise ValueError("cyclic parent")
    model=json_model(root,ns,name)
    if not model.get("parent"):return model
    try:
        parent=resolve(root,ns,model["parent"],(*seen,name))
    except FileNotFoundError:
        parent=placeholder(model["parent"])
    return {**parent,**model,"textures":{**parent.get("textures",{}),**model.get("textures",{})},
            "elements":model.get("elements",parent.get("elements",[]))}

def face_uv(face,element):
    if "uv" in face:return face["uv"]
    # Derive Java default model UV from cube bounds.
    x,y,z=element["from"];xx,yy,zz=element["to"]
    return {"down":[x,16-zz,xx,16-z],"up":[x,z,xx,zz],
            "north":[16-xx,16-yy,16-x,16-y],
            "south":[x,16-yy,xx,16-y],
            "west":[z,16-yy,zz,16-y],
            "east":[16-zz,16-yy,16-z,16-y]}

def resolve_tex(value,texture_variables):
    n=0
    while value.startswith("#"):
        value=texture_variables.get(value[1:],"")
        n+=1
        if not value or n>12:raise ValueError("unresolved texture variable")
    return value

def convert(root,ns,keys,ident):
    parts=[resolve(root,ns,k) for k in keys]
    faces_to_pack={}
    entries=[]
    issues=[]
    for idx,model in enumerate(parts):
        cubes=[]
        for el in model.get("elements",[]):
            cubes.append({"el":el,"uvs":{}})
            record=cubes[-1]
            for face,info in el.get("faces",{}).items():
                if face not in FACES:continue
                tex=resolve_tex(info.get("texture","#texture"),model.get("textures",{}))
                uv=info.get("uv") or face_uv(face,el)
                rot=int(info.get("rotation",0))
                if rot not in (0,90,180,270):raise ValueError("UV rotation unsupported")
                key=(tex,tuple(uv),rot)
                faces_to_pack[key]=None
                record["uvs"][face]=key
        entries.append(cubes)
    # Crop original source texture regions. Java 16-unit UV coords scaled by PNG size.
    cropped={}
    for key in faces_to_pack:
        texture,box,rot=key
        img=Image.open(texture_file(root,ns,texture)).convert("RGBA")
        iw,ih=img.size
        # If an animated texture is vertically stacked, use the first frame.
        frame_h=min(ih,iw)
        sx=iw/16;sy=frame_h/16
        coords=[int(round(box[0]*sx)),int(round(box[1]*sy)),
                int(round(box[2]*sx)),int(round(box[3]*sy))]
        left,top,right,bottom=coords
        if right<=left or bottom<=top:raise ValueError("UV rect non-positive")
        tile=img.crop(coords)
        if rot:tile=tile.rotate(rot,expand=True, resample=Image.Resampling.NEAREST)
        cropped[key]=tile
        if ih>iw:issues.append("animated texture: static frame only "+texture)
    # Pack rectangular UV tiles with one-pixel separation.
    placements={};x=y=row_h=0;MAX_ROW=2048
    for key,img in sorted(cropped.items(),key=lambda item:(-item[1].height,-item[1].width)):
        if x+img.width+1>MAX_ROW and x>0:
            y+=row_h+1;x=0;row_h=0
        placements[key]=(x,y);x+=img.width+1;row_h=max(row_h,img.height)
    height=max(1,y+row_h);width=max(1,max(x,*(px+img.width for key,img in cropped.items() for px,py in [placements[key]])))
    atlas=Image.new("RGBA",(width,height))
    for key,img in cropped.items():atlas.paste(img,placements[key])
    bones=[]
    for i,source_cubes in enumerate(entries):
        cubes=[]
        for record in source_cubes:
            el=record["el"];frm=el["from"];to=el["to"]
            cube={"origin":[frm[0]-8,frm[1]+16*i,frm[2]-8],
                  "size":[to[n]-frm[n] for n in range(3)],"uv":{}}
            for face,key in record["uvs"].items():
                px,py=placements[key];tile=cropped[key]
                cube["uv"][face]={"uv":[px,py],"uv_size":[tile.width,tile.height]}
            if el.get("rotation"):
                r=el["rotation"]
                if r.get("rescale"): raise ValueError("rotated rescale element requires baking")
                cube["pivot"]=[r["origin"][0]-8,r["origin"][1]+16*i,r["origin"][2]-8]
                cube["rotation"]=[r["angle"] if v==r["axis"] else 0 for v in ("x","y","z")]
            cubes.append(cube)
        bones.append({"name":"block_part_"+str(i),"pivot":[0,0,0],"cubes":cubes})
    geometry={"format_version":"1.12.0","minecraft:geometry":[{
        "description":{"identifier":ident,"texture_width":width,"texture_height":height,
                       "visible_bounds_width":3,"visible_bounds_height":4,
                       "visible_bounds_offset":[0,1,0]},
        "bones":bones
    }]}
    return geometry,atlas,issues

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--namespace",required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    names=set()
    for pre in RESOURCE_PREFIXES:
        folder=args.root/pre/"assets"/args.namespace/"models"/"block"
        if folder.exists():names.update(f.stem for f in folder.glob("*.json"))
    converted=0;failure=[]
    for name in sorted(names):
        if name.endswith("_top") and name.removesuffix("_top")+"_bottom" in names:continue
        upper=name.removesuffix("_bottom")+"_top" if name.endswith("_bottom") else None
        group=[name,upper] if upper in names else [name]
        rel=["block/"+x for x in group]
        try:
            result,atlas,warn=convert(args.root,args.namespace,rel,
                "geometry.minizin."+args.namespace+"."+re.sub("[^a-z0-9_]","_",name.lower()))
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/(name+".geo.json")).write_text(json.dumps(result,indent=2)+"\n")
            atlas.save(args.output/(name+".png"))
            converted+=1
        except Exception as error:
            failure.append({"name":name,"error":str(error)})
    report={"namespace":args.namespace,"total":converted+len(failure),
            "converted":converted,"failed":len(failure),"failures":failure}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!="failures"}))
    print("First 8 failure categories:",failure[:8])
    if converted==0:sys.exit(2)
if __name__=="__main__":main()
