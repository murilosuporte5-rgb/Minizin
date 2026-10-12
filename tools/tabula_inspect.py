#!/usr/bin/env python3
"""Inspect Ice & Fire .tbl Tabula ZIPs, retaining source model structure losslessly.

This is a decoder/extractor, NOT yet a high-fidelity Bedrock dragon exporter.
Use it before rig conversion so Codex does not redesign 192 existing poses.
"""
import argparse, json, sys, zipfile
from collections import Counter
from pathlib import Path

def inspect_tabula(source: Path, out: Path|None=None):
    if not zipfile.is_zipfile(source): raise ValueError("Expected ZIP-based Tabula .tbl")
    with zipfile.ZipFile(source) as arc:
        names=arc.namelist()
        matches=[name for name in names if name.endswith("model.json")]
        if not matches: raise ValueError(f"No model.json in Tabula archive: {names}")
        model=json.loads(arc.read(matches[0]))
        if out:
            out.mkdir(parents=True,exist_ok=True)
            (out/"model.json").write_text(json.dumps(model,indent=2,ensure_ascii=False),encoding="utf-8")
            for entry in arc.infolist():
                if entry.is_dir() or entry.filename==matches[0]: continue
                # No unchecked ZIP path traversal
                target=(out/entry.filename).resolve()
                if not target.is_relative_to(out.resolve()): raise ValueError("Unsafe zip entry "+entry.filename)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(arc.read(entry))
        def summarize(obj):
            counts=Counter()
            def walk(value):
                if isinstance(value,dict):
                    counts.update(["object"])
                    for k,v in value.items():
                        counts.update(["key:"+k]);walk(v)
                elif isinstance(value,list):
                    counts.update(["array"])
                    for v in value:walk(v)
            walk(obj)
            return counts
        return {"source":str(source),"zip_entries":names,"top_keys":sorted(model),
                "model_name":model.get("modelName"),"texture_width":model.get("textureWidth"),
                "texture_height":model.get("textureHeight"),
                "cubeCountHint":summarize(model).get("key:dimensions",0),
                "saved_to":str(out) if out else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("--extract-to",type=Path)
    a=p.parse_args()
    try: print(json.dumps(inspect_tabula(a.source,a.extract_to),indent=2))
    except Exception as error: print(str(error),file=sys.stderr);sys.exit(1)
if __name__=="__main__":main()
