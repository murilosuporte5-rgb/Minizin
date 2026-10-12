#!/usr/bin/env python3
"""Offline hierarchical heightfield LOD study. Does not replace Bedrock renderer."""
import argparse,json,math,sys
from pathlib import Path
def pyramid(rows,max_levels=20):
    if not rows or not isinstance(rows,list) or not all(isinstance(r,list) for r in rows):raise ValueError("empty or invalid rows")
    w=len(rows[0]);h=len(rows)
    if w<1 or any(len(r)!=w for r in rows):raise ValueError("nonrectangular rows")
    if h*w>4000000:raise ValueError("too many cells")
    if not 1<=max_levels<=32:raise ValueError("invalid max_levels")
    cells=[]
    for row in rows:
        c=[]
        for n in row:
            if not isinstance(n,(int,float)) or isinstance(n,bool) or not math.isfinite(n):raise ValueError("nonfinite height")
            c.append({"min":float(n),"max":float(n),"sum":float(n),"count":1})
        cells.append(c)
    levels=[]
    for i in range(max_levels):
        levels.append({"level":i,"cell_size":2**i,"height":len(cells),"width":len(cells[0]),
          "cells":[[{"min":c["min"],"max":c["max"],"mean":c["sum"]/c["count"],"samples":c["count"]} for c in row] for row in cells]})
        if len(cells)==1 and len(cells[0])==1:break
        out=[]
        for z in range(0,len(cells),2):
            line=[]
            for x in range(0,len(cells[0]),2):
                group=[cells[j][k] for j in (z,z+1) if j<len(cells)
                      for k in (x,x+1) if k<len(cells[0])]
                line.append({"min":min(c["min"] for c in group),"max":max(c["max"] for c in group),
                             "sum":sum(c["sum"] for c in group),"count":sum(c["count"] for c in group)})
            out.append(line)
        cells=out
    return {"schema":"minizin:heightfield_lod_pyramid_v1","original_size":[w,h],
            "levels":levels,"notice":"Data prototype only; no Distant Horizons file import or rendering"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        obj=json.loads(a.source.read_text())
        result=pyramid(obj["heightmap"])
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+"\n")
        print("Levels:",len(result["levels"]),"saved:",a.output)
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
