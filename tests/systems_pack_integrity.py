"""Validate cross-pack resource references for Minizin Systems (offline, no game runtime)."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]/"bedrock/packs"
def data(path):
    return json.loads(path.read_text(encoding="utf-8"))
def check(condition,message):
    if not condition: raise AssertionError(message)
def resources(path):
    return list(path.rglob("*.json"))
def geometry_ids(rp):
    ids=set()
    for path in (rp/"models").rglob("*.geo.json"):
        for model in data(path).get("minecraft:geometry",[]):
            ids.add(model["description"]["identifier"])
    return ids
def main():
    bp=ROOT/"next_four/BP"; rp=ROOT/"next_four/RP"
    way_bp=ROOT/"waystones/BP"; way_rp=ROOT/"waystones/RP"
    bag_bp=ROOT/"sophisticated_backpacks/BP"; bag_rp=ROOT/"sophisticated_backpacks/RP"
    pairs=[(bp,rp),(way_bp,way_rp),(bag_bp,bag_rp)]
    all_uuids=set()
    for b,r in pairs:
        bman=data(b/"manifest.json"); rman=data(r/"manifest.json")
        rp_id=rman["header"]["uuid"]; version=rman["header"]["version"]
        check(any(x.get("uuid")==rp_id and x.get("version")==version
            for x in bman["dependencies"]),f"RP link missing in {b}")
        for pack in (bman,rman):
            uuids=[pack["header"]["uuid"]]+[m["uuid"] for m in pack["modules"]]
            for identifier in uuids:
                check(identifier not in all_uuids,f"Duplicate manifest UUID {identifier}")
                all_uuids.add(identifier)
    for b,r,names in [(bp,rp,["rftools_generator","rftools_cell","rftools_cable","rftools_lamp"]),
                      (way_bp,way_rp,["andesite_waystone_block"])]:
        known=geometry_ids(r)
        atlas=data(r/"textures/terrain_texture.json")["texture_data"]
        for name in names:
            block=data(b/"blocks"/(name+".json"))["minecraft:block"]
            component=block["components"]
            geometry_spec=component["minecraft:geometry"]
            geom=geometry_spec.get("identifier") if isinstance(geometry_spec,dict) else geometry_spec
            alias=component["minecraft:material_instances"]["*"]["texture"]
            check(geom in known,f"No resource geometry for {name}: {geom}")
            check(alias in atlas,f"No atlas alias for {name}: {alias}")
            texture=atlas[alias]["textures"]
            check((r/(texture+".png")).is_file(),f"Missing PNG for {name}: {texture}")
    mca_ids=geometry_ids(rp)
    animation=data(rp/"animations/mca_walk.animation.json")["animations"]
    check("animation.minizin.mca.walk" in animation,"MCA locomotion animation absent")
    for sex in ("female","male"):
        for i in range(5):
            name=f"mca_{sex}_{i}"
            server=data(bp/"entities"/f"{name}.json")["minecraft:entity"]["description"]
            client=data(rp/"entity"/f"{name}.entity.json")["minecraft:client_entity"]["description"]
            check(server["identifier"]==client["identifier"],f"NPC ID mismatch: {name}")
            check(client["geometry"]["default"] in mca_ids,f"NPC geometry not found: {name}")
            tex=client["textures"]["default"]
            check((rp/(tex+".png")).is_file(),f"NPC skin missing: {name}")
            check(client["animations"]["walk"] in animation,f"NPC animation missing: {name}")
    check(data(bag_bp/"items/backpack.json")["minecraft:item"]["description"]["identifier"]=="minizin:backpack","Backpack ID mismatch")
    print("PASS: 3 pack pairs, 5 functional blocks, 10 NPCs, skin/geometry/animation references, unique UUIDs")
if __name__=="__main__":main()
