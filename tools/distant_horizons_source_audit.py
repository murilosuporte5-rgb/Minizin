#!/usr/bin/env python3
"""Source tree classifier for actual DH GitLab repo (filename evidence only)."""
import argparse,json,re
from pathlib import Path
PATTERNS={"rendering":r"render|shader|glsl|gpu|opengl|vertex|frustum",
"lod_data":r"lod|fullData|dataSource|detailLevel|levelOfDetail|quadTree",
"persistence":r"database|sqlite|repository|dataStore|fileHandler|cache",
"worldgen":r"worldGen|generator|chunk|terrain|heightMap",
"api":r"(^|/)api(/|$)|IDhApi"}
def classify(names):
    matches={k:[] for k in PATTERNS}
    for file in names:
        for group,pattern in PATTERNS.items():
            if re.search(pattern,file,re.I):matches[group].append(file)
    return {"source":"https://gitlab.com/distant-horizons-team/distant-horizons",
      "file_count":len(names),"categories":{k:{"count":len(v),"examples":v[:15]} for k,v in matches.items()},
      "is_bedrock_renderer":False,
      "warning":"Filename-level reverse engineering. No native renderer or Minecraft Bedrock LOD."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("tree_file",type=Path)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    obj=classify(a.tree_file.read_text().splitlines())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps({"file_count":obj["file_count"],"counts":{k:v["count"] for k,v in obj["categories"].items()}}))
