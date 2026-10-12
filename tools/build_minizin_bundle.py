#!/usr/bin/env python3
"""Package the two currently available prototypes into one Bedrock .mcaddon.

Contains Waystones and Mowzie Bluff only. NOT the fourteen finished Java mods.
"""
from __future__ import annotations
import io,zipfile
from build_bedrock_packs import validate,zipped,ROOT

def build_combined(root=ROOT):
    out=root/"build"/"Minizin_Combined_Prototype.mcaddon"
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_STORED) as bundle:
        for mod in ("waystones","mowzie"):
            rp,bp,n=validate(root/"bedrock"/"packs"/mod)
            if n<1:raise ValueError("No entity for "+mod)
            for short,folder in (("RP",rp),("BP",bp)):
                data=zipped(folder)
                with zipfile.ZipFile(io.BytesIO(data)) as package:
                    if "manifest.json" not in package.namelist():raise ValueError("Missing manifest: "+mod+"/"+short)
                bundle.writestr(mod+"_"+short+".mcpack",data)
    with zipfile.ZipFile(out) as z:
        assert len(z.namelist())==4,z.namelist()
        print("Pack created:",out,"size:",out.stat().st_size,"inner:",z.namelist())
    return out

if __name__=="__main__":build_combined()
