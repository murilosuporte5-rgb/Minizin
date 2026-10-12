#!/usr/bin/env python3
"""Batch convert every Tabula .tbl in permissioned sources to Bedrock geometry.

Reports per-file failures without stopping the whole batch. Does not assert
that each pose is an animation clip. Every .tbl is a static model pose.
"""
import argparse, collections, json, sys
from pathlib import Path
from tabula_to_bedrock import read_tabula,export_tabula

def batch(source,out):
    models=sorted(source.rglob("*.tbl"))
    if not models:raise ValueError("No Tabula .tbl files found")
    rows=[]
    for file in models:
        relative=file.relative_to(source)
        ident="geometry.minizin.tabula_"+str(relative.with_suffix("")).replace("/","_").replace("-","_").lower()
        target=out/relative.with_suffix(".geo.json")
        result={"original":relative.as_posix(),"output":target.relative_to(out).as_posix()}
        try:
            m=read_tabula(file)
            geom,report=export_tabula(m,ident)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(geom,indent=2)+"\n")
            result.update(status="ok",bones=report["bones"],cubes=report["model_boxes"],
                          atlas=report["atlas"],modelName=report["source_name"],
                          issues=report["issues"])
        except Exception as e:
            result.update(status="failed",error=str(e))
        rows.append(result)
    ok=sum(x["status"]=="ok" for x in rows)
    failures=[x for x in rows if x["status"]!="ok"]
    report={"source":str(source),"total":len(models),"converted":ok,
            "failed":len(failures),"results":rows}
    out.mkdir(parents=True,exist_ok=True)
    (out/"batch_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"total":len(models),"converted":ok,"failed":len(failures),
                      "sample_failures":failures[:6]},indent=2))
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--min-success",type=int,default=1)
    opts=ap.parse_args()
    try:
        report=batch(opts.source,opts.output)
        if report["converted"] < opts.min_success:sys.exit(2)
    except Exception as e:
        print("batch error:",e,file=sys.stderr);sys.exit(1)
