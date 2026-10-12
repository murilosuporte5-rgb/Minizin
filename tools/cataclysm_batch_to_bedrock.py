#!/usr/bin/env python3
"""Batch extract Cataclysm entity models from original Java Citadel model code.

Creates one .geo.json per statically recovered model, reports skip/reason for
Mojang ModelPart / procedural models. Animation, AI and UV fidelity need QA.
"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from citadel_java_to_bedrock import recover_models

def convert_all(source:Path,output:Path):
    output.mkdir(parents=True,exist_ok=True)
    files=sorted(source.glob("*_Model.java"))
    result=[]
    for file in files:
        row={"source":file.name,"status":"skipped"}
        code=file.read_text(encoding="utf-8")
        if "new AdvancedModelBox(this)" not in code:
            row["reason"]="Non-Citadel or procedural model; dedicated Mojang ModelPart converter required"
        else:
            try:
                geo,report=recover_models([code],
                    "geometry.minizin.cataclysm."+re.sub(r"[^a-z0-9_]","_",file.stem.lower()))
                if report["box_total"]==0:raise ValueError("No static boxes recovered")
                dest=output/(file.stem+".geo.json")
                dest.write_text(json.dumps(geo,indent=2)+"\n",encoding="utf-8")
                row.update(status="converted",boxes=report["box_total"],bones=report["bones"],
                    texture=report["texture"],issues=report["unsupported"])
            except Exception as e:row["reason"]=str(e)
        result.append(row)
    report={"scanned":len(result),"converted":sum(x["status"]=="converted" for x in result),
            "skipped":sum(x["status"]=="skipped" for x in result),"models":result}
    (output/"audit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="models"}))
    for x in result:
        if x["status"]!="converted":print("SKIP",x["source"],x.get("reason",""))
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--minimum",type=int,default=1)
    a=p.parse_args()
    try:
        report=convert_all(a.source,a.output)
        if report["converted"]<a.minimum:sys.exit(2)
    except Exception as e: print("ERROR",e,file=sys.stderr);sys.exit(1)
