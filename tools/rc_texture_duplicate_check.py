#!/usr/bin/env python3
"""Read an existing Bedrock .mcaddon and report exact PNG-content collisions.

No visual asset is edited; only authoritative byte/pixel evidence is recorded.
Accepts RP/BP nested .mcpack. Requires Pillow. Intended for Codex triage.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,zipfile
from pathlib import Path
from PIL import Image

def audit(path):
    with zipfile.ZipFile(path) as outer:
        rp_name=next((p for p in outer.namelist() if p.endswith("_RP.mcpack")),None)
        bp_name=next((p for p in outer.namelist() if p.endswith("_BP.mcpack")),None)
        if not rp_name or not bp_name:raise ValueError("Two nested RP/BP .mcpack required")
        with zipfile.ZipFile(io.BytesIO(outer.read(rp_name))) as rp:
            with zipfile.ZipFile(io.BytesIO(outer.read(bp_name))) as bp:
                rnames=rp.namelist();bnames=bp.namelist()
                index={}
                for directory in ("items","blocks","entities"):
                    index[directory]=sorted(p for p in bnames
                        if p.startswith(directory+"/") and p.endswith(".json"))
                groups=collections.defaultdict(list)
                for name in sorted(rnames):
                    if not name.endswith(".png") or not name.startswith(("textures/items/","textures/blocks/")):continue
                    with Image.open(io.BytesIO(rp.read(name))) as img:
                        picture=img.convert("RGBA")
                        digest=hashlib.sha256(picture.tobytes()).hexdigest()
                        groups[digest].append({"name":name,"width":picture.width,
                                               "height":picture.height})
                collisions=[]
                for sha,items in sorted(groups.items()):
                    if len(items)>1:collisions.append({"pixel_sha256":sha,"items":items})
                return {
                    "source":str(path),"source_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    "definitions":{k:len(v) for k,v in index.items()},
                    "duplicate_groups":collisions,
                    "duplicate_item_texture_paths":sum(
                        len([x for x in c["items"] if x["name"].startswith("textures/items/")])
                        for c in collisions),
                    "duplicate_block_texture_paths":sum(
                        len([x for x in c["items"] if x["name"].startswith("textures/blocks/")])
                        for c in collisions),
                    "sound_files":[n for n in rnames if n.endswith((".ogg",".wav"))],
                    "sound_definitions":any(n.endswith("sound_definitions.json") for n in rnames),
                    "note":"Duplicate pixels are evidence of repeated art, not proof of intended upstream source. Do not synthesize replacements."
                }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mcaddon",type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    report=audit(a.mcaddon)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("duplicate_groups","sound_files")},indent=2))
if __name__=="__main__":main()
