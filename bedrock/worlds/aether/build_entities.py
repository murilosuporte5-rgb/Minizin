"""Convert original pinned Aether Java ModelPart rigs into Bedrock geometry packs.

Only outputs into ignored build/. Cubes, texture offsets and parent hierarchy
are parsed from the original createBodyLayer() implementations; Bedrock poses
for motion are explicitly marked adapted, not original Mojang runtime output.
Unsupported procedural/model statements are listed in an audit report.
"""
from __future__ import annotations
import json
import math
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JAVA_MODELS = ROOT / "mods/41-the-aether/upstream/src/main/java/com/aetherteam/aether/client/renderer/entity/model"
ORIGINAL_TEXTURES = ROOT / "mods/41-the-aether/upstream/src/main/resources/assets/aether/textures/entity"
MOD_NAMESPACE = "minizin_aether"
MOBS = {
    "slider": {"model": "SliderModel.java", "texture": "mobs/slider/slider_awake.png",
               "health": 400, "attack": 15, "collision": [2.0, 2.1], "movement": 0.24, "hostile": True},
    "valkyrie_queen": {"model": "ValkyrieModel.java", "texture": "mobs/valkyrie_queen/valkyrie_queen.png",
                       "health": 500, "attack": 13.5, "collision": [0.9, 2.1], "movement": 0.30, "hostile": True},
    "sun_spirit": {"model": "SunSpiritModel.java", "texture": "mobs/sun_spirit/sun_spirit.png",
                   "health": 500, "attack": 10, "collision": [1.2, 2.0], "movement": 0.34,
                   "hostile": True, "flying": True},
    "zephyr": {"model": "ZephyrModel.java", "texture": "mobs/zephyr/zephyr.png",
               "health": 20, "attack": 5, "collision": [1.3, 1.3], "movement": 0.30,
               "hostile": True, "flying": True},
    "aechor_plant": {"model": "AechorPlantModel.java", "texture": "mobs/aechor_plant/aechor_plant.png",
                     "health": 25, "attack": 4, "collision": [0.9, 1.7], "movement": 0,
                     "hostile": True},
    "fire_minion": {"model": "SunSpiritModel.java", "texture": "mobs/sun_spirit/sun_spirit.png",
                     "health": 30, "attack": 6, "collision": [0.7, 1.1], "movement": .26,
                     "hostile": True, "flying": True},
    "aerbunny": {"model": "AerbunnyModel.java", "texture": "mobs/aerbunny/aerbunny.png",
                  "health": 10, "attack": 0, "collision": [0.5, 0.5], "movement": .28,
                  "hostile": False},
    "cockatrice": {"model": "BipedBirdModel.java", "texture": "mobs/cockatrice/cockatrice.png",
                    "health": 25, "attack": 5, "collision": [0.8, 1.2], "movement": .32,
                    "hostile": True},
    "sheepuff": {"model": "SheepuffModel.java", "texture": "mobs/sheepuff/sheepuff.png",
                  "health": 12, "attack": 0, "collision": [1.0, 1.0], "movement": .2,
                  "hostile": False},
    "valkyrie": {"model": "ValkyrieModel.java", "texture": "mobs/valkyrie/valkyrie.png",
                  "health": 45, "attack": 8, "collision": [0.8, 2.0], "movement": .33,
                  "hostile": True},
    "aerwhale": {"model": "AerwhaleModel.java", "texture": "mobs/aerwhale/aerwhale.png",
                  "health": 35, "attack": 0, "collision": [3.2, 2.2], "movement": .22,
                  "hostile": False, "flying": True},
    "mimic": {"model": "MimicModel.java", "texture": "mobs/mimic/normal.png",
              "health": 30, "attack": 7, "collision": [1.0, 1.0], "movement": .25,
              "hostile": True},
    "phyg": {"model": "QuadrupedWingsModel.java", "texture": "mobs/phyg/phyg.png",
             "wings_texture": "mobs/phyg/phyg_wings.png",
             "vanilla_base": "geometry.pig.v3", "wing_offset": 10.0,
             "health": 12, "attack": 0, "collision": [1.0, 1.1], "movement": .26,
             "hostile": False, "flying": True},
    "flying_cow": {"model": "QuadrupedWingsModel.java", "texture": "mobs/flying_cow/flying_cow.png",
                   "wings_texture": "mobs/flying_cow/flying_cow_wings.png",
                   "vanilla_base": "geometry.cow.v2", "wing_offset": 0.0,
                   "health": 14, "attack": 0, "collision": [1.0, 1.3], "movement": .23,
                   "hostile": False, "flying": True},
    "moa": {"model": "BipedBirdModel.java", "texture": "mobs/moa/black_moa.png",
            "health": 18, "attack": 0, "collision": [0.85, 1.5], "movement": .3,
            "hostile": False},
    "cloud_minion": {"model": "CloudMinionModel.java",
                     "texture": "miscellaneous/cloud_minion/cloud_minion.png",
                     "health": 12, "attack": 2, "collision": [.75, .75], "movement": .25,
                     "hostile": True, "flying": True},
}
# Original boss drops are converted by convert_loot.py.
BOSSES = ("slider", "valkyrie_queen", "sun_spirit")
KNOWN_ANIMATION_BONES = {
    "slider": {"slider": [0, 0, 12]},
    "valkyrie_queen": {"right_arm": [35, 0, -12], "left_arm": [-15, 0, 10]},
    "sun_spirit": {"left_arm": [-38, 0, 10], "right_arm": [-38, 0, -10]},
    "zephyr": {"body": [0, 15, 0]},
    "aechor_plant": {"head": [12, 0, 10]},
    "fire_minion": {"left_arm": [-38, 0, 10], "right_arm": [-38, 0, -10]},
    "aerbunny": {"head": [10, 0, 0]},
    "cockatrice": {"head": [18, 0, 0]},
    "sheepuff": {"head": [8, 0, 0]},
    "valkyrie": {"right_arm": [35, 0, -12]},
    "aerwhale": {"body": [0, 7, 0]},
    "mimic": {"lid": [25, 0, 0]},
    "phyg": {"body": [4, 0, 0]},
    "flying_cow": {"body": [4, 0, 0]},
    "moa": {"head": [10, 0, 0]},
    "cloud_minion": {"cloudMinion": [0, 15, 0]},
}
FLOAT = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[FfDd])?$")


def floatv(value: str) -> float:
    value = value.strip()
    # These are literal constants of the pinned Minecraft Java Mth class,
    # not arbitrary Java expression execution.
    constants = {"Mth.HALF_PI": math.pi / 2,
                 "Mth.PI": math.pi,
                 "Mth.TWO_PI": math.tau,
                 "Mth.DEG_TO_RAD": math.pi / 180}
    if value in constants:
        return constants[value]
    if not FLOAT.fullmatch(value):
        raise ValueError(f"Non-literal Java geometry argument: {value}")
    return float(value.rstrip("FfDd"))


def split_arguments(source: str) -> list[str]:
    depth = 0
    splits, start = [], 0
    for idx, ch in enumerate(source):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            splits.append(source[start:idx].strip())
            start = idx + 1
    splits.append(source[start:].strip())
    return splits


def matched_parentheses(src: str, left: int) -> tuple[str, int]:
    assert src[left] == "("
    level = 1
    for idx in range(left + 1, len(src)):
        if src[idx] == "(":
            level += 1
        elif src[idx] == ")":
            level -= 1
            if level == 0:
                return src[left + 1:idx], idx + 1
    raise ValueError("Unterminated Java call")


def parse_pose(src: str, offset: float = 0.) -> tuple[list[float], list[float]]:
    if src == "PartPose.ZERO":
        return [0.0] * 3, [0.0] * 3
    m = re.match(r"PartPose\.(offset|offsetAndRotation)\(", src)
    if not m:
        raise ValueError(f"Unsupported pose {src[:120]}")
    args, _ = matched_parentheses(src, m.end() - 1)
    n = []
    for x in split_arguments(args):
        if x.endswith("+ offset"):
            n.append(floatv(x.split("+", 1)[0]) + offset)
        else:
            n.append(floatv(x))
    if m.group(1) == "offset" and len(n) == 3:
        return n, [0., 0., 0.]
    if m.group(1) == "offsetAndRotation" and len(n) == 6:
        return n[:3], [round(math.degrees(v), 5) for v in n[3:]]
    raise ValueError(f"Unsupported pose arity: {src}")


def parse_cubes(builder: str) -> list[dict]:
    cubes = []
    for match in re.finditer(r"\.addBox\(", builder):
        args, _ = matched_parentheses(builder, match.end() - 1)
        fields = split_arguments(args)
        named = bool(fields and re.fullmatch(r'"[^"]+"', fields[0]))
        start = 1 if named else 0
        if len(fields) < start + 6:
            raise ValueError(f"Malformed Java box: {args}")
        x, y, z, w, h, d = [floatv(v) for v in fields[start:start+6]]
        if min(w, h, d) < 0:
            raise ValueError(f"Negative size in cube: {args}")
        prev = builder[:match.start()]
        uv_matches = list(re.finditer(r"\.texOffs\((\d+),\s*(\d+)\)", prev))
        if named and len(fields) >= start + 9:
            # Named Java cubes specify UV at the end of each addBox call.
            u, v = [int(floatv(k)) for k in fields[-2:]]
        elif uv_matches:
            u, v = [int(k) for k in uv_matches[-1].groups()]
        else:
            raise ValueError("Java box missing explicit UV")
        inflate = 0.
        deformation = fields[start + 6] if len(fields) > start + 6 else ""
        if "CubeDeformation(" in deformation:
            m = re.search(r"CubeDeformation\(([^()]+)\)", deformation)
            inflate = floatv(m.group(1)) if m else 0.
        cubes.append({"x": x - inflate, "y": y - inflate,
                      "z": z - inflate, "w": w + 2 * inflate,
                      "h": h + 2 * inflate, "d": d + 2 * inflate,
                      "uv": [u, v]})
    return cubes


def extract_parts(source: str, offset: float = 0.) -> list[dict]:
    parts = []
    # Each Java declaration is terminated by ';'; intermediate chained
    # calls use nested parentheses. This also catches the complex Valkyrie rig.
    expression = re.compile(
        r"(?:(?:PartDefinition)\s+(?P<variable>\w+)\s*=\s*)?"
        r"(?P<parent>\w+)\.addOrReplaceChild\(")
    for m in expression.finditer(source):
        args, _ = matched_parentheses(source, m.end() - 1)
        terms = split_arguments(args)
        if len(terms) != 3:
            continue
        nm = re.fullmatch(r'"([a-zA-Z_0-9]+)"', terms[0])
        if not nm or not terms[1].startswith("CubeListBuilder.create()"):
            continue
        try:
            pose, rotation = parse_pose(terms[2], offset)
            cubes = parse_cubes(terms[1])
        except ValueError:
            continue
        parts.append({"name": nm.group(1), "variable": m.group("variable"),
                      "parent_variable": m.group("parent"),
                      "offset": pose, "rotation": rotation, "cubes": cubes})
    return parts


def convert_model(source: str, mob: str, offset: float = 0.) -> tuple[dict, dict]:
    size = re.search(r"LayerDefinition\.create\(\s*\w+,\s*(\d+),\s*(\d+)\s*\)", source)
    if size is None:
        raise ValueError(f"No Java texture size for {mob}")
    width, height = map(int, size.groups())
    parts = extract_parts(source, offset)
    if not parts:
        raise ValueError(f"No directly recoverable Java model parts for {mob}")
    parents = {"partDefinition": ("__root__", (0., 0., 0.))}
    bone_names = set()
    bones, cube_count = [], 0
    for part in parts:
        parent_variable = part["parent_variable"]
        previous = parents.get(parent_variable)
        if previous is None:
            # Do not guess parentage for Java procedural geometry.
            continue
        parent_name, parent_absolute = previous
        px, py, pz = (parent_absolute[i] + part["offset"][i] for i in range(3))
        parents[part["variable"] or "unbound_" + part["name"]] = (part["name"], (px, py, pz))
        if part["name"] in bone_names:
            continue
        bone_names.add(part["name"])
        bone = {"name": part["name"], "pivot": [px, 24 - py, pz]}
        if parent_name != "__root__":
            bone["parent"] = parent_name
        if any(part["rotation"]):
            rx, ry, rz = part["rotation"]
            bone["rotation"] = [-rx, -ry, rz]
        cubes = []
        for c in part["cubes"]:
            cubes.append({"origin": [
                round(px + c["x"], 5),
                round(24 - (py + c["y"] + c["h"]), 5),
                round(pz + c["z"], 5)],
                "size": [round(c["w"], 5), round(c["h"], 5), round(c["d"], 5)],
                "uv": c["uv"]})
        if cubes:
            bone["cubes"] = cubes
            cube_count += len(cubes)
        bones.append(bone)
    if cube_count == 0:
        raise ValueError(f"No printable cuboids in Java source for {mob}")
    geo = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.minizin_aether.{mob}",
                "texture_width": width, "texture_height": height,
                "visible_bounds_width": 4 if mob == "slider" else 3,
                "visible_bounds_height": 4 if mob == "slider" else 3,
                "visible_bounds_offset": [0, 1.2, 0],
            },
            "bones": bones,
        }],
    }
    return geo, {"java_model_parts": len(parts), "converted_bones": len(bones),
                 "converted_cubes": cube_count, "texture_size": [width, height],
                 "potential_unconverted": len(parts) - len(bones)}


def entity_bp(mob: str, spec: dict) -> dict:
    identifier = MOD_NAMESPACE + ":" + mob
    hostile = spec["hostile"]
    components = {
        "minecraft:type_family": {"family": ["mob", "monster", "minizin_aether",
                                              "boss" if mob in BOSSES else "wild"]},
        "minecraft:health": {"value": int(spec["health"]), "max": int(spec["health"])},
        "minecraft:collision_box": {"width": spec["collision"][0],
                                    "height": spec["collision"][1]},
        "minecraft:physics": {"has_gravity": not spec.get("flying", False),
                              "has_collision": True},
        "minecraft:movement": {"value": spec["movement"]},
        "minecraft:attack": {"damage": int(spec["attack"])},
        "minecraft:nameable": {},
        "minecraft:behavior.look_at_player": {"priority": 5, "look_distance": 18,
                                               "probability": .8},
    }
    if mob not in BOSSES and mob != "aechor_plant":
        if spec.get("flying", False):
            components["minecraft:navigation.fly"] = {"can_path_over_water": True,
                                                        "can_open_doors": False}
            components["minecraft:movement.fly"] = {}
        else:
            components["minecraft:navigation.walk"] = {"can_path_over_water": True,
                                                        "avoid_damage_blocks": True}
            components["minecraft:movement.basic"] = {}
        components["minecraft:behavior.random_stroll"] = {
            "priority": 7, "speed_multiplier": .7}
        if hostile:
            components["minecraft:behavior.nearest_attackable_target"] = {
                "priority": 1, "within_radius": 22,
                "entity_types": [{"filters": {"test": "is_family", "subject": "other",
                                               "value": "player"}, "max_dist": 22}]}
            components["minecraft:behavior.melee_attack"] = {
                "priority": 3, "speed_multiplier": 1.1, "track_target": True}
    if mob in BOSSES:
        components["minecraft:boss"] = {
            "should_darken_sky": mob == "sun_spirit",
            "hud_range": 30,
            "name": mob.replace("_", " ").title()}
    if hostile:
        components["minecraft:experience_reward"] = {"on_death": 80 if mob in BOSSES else 5}
    loot = "loot_tables/minizin_aether/entities/" + mob + ".json"
    components["minecraft:loot"] = {"table": loot}
    return {"format_version": "1.21.80", "minecraft:entity": {
        "description": {"identifier": identifier,
                        "is_spawnable": mob not in BOSSES,
                        "is_summonable": True, "is_experimental": False},
        "components": components,
    }}


def animations(mob: str) -> dict:
    target = KNOWN_ANIMATION_BONES[mob]
    # Angles are adapted gameplay clips. The bones themselves and model UV
    # originate from Java. No original authored animation keyframes existed.
    idle = {name: {"rotation": [
        "math.sin(query.anim_time*80.0)*1.5", 0, 0]} for name in target}
    # Bedrock accepts animation poses as vectors; a mode change uses playAnimation
    return {"format_version": "1.8.0", "animations": {
        f"animation.minizin_aether.{mob}.idle": {
            "loop": True, "animation_length": 2,
            "bones": idle},
        f"animation.minizin_aether.{mob}.attack": {
            "loop": False, "animation_length": .65,
            "bones": {name: {"rotation": v} for name, v in target.items()}},
    }}


def client_entity(mob: str) -> dict:
    spec = MOBS[mob]
    wings = bool(spec.get("vanilla_base"))
    # Phyg/FlyingCow Java has a stock quadruped torso PLUS authored wing mesh.
    # Reuse Bedrock vanilla body geometry without fabricating pig/cow cuboids.
    desc = {
        "identifier": MOD_NAMESPACE + ":" + mob,
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/entity/minizin_aether/{mob}"},
        "geometry": {"default": spec["vanilla_base"] if wings
                     else f"geometry.minizin_aether.{mob}"},
        "render_controllers": ["controller.render.minizin_aether.mob"],
        "animations": {
            "idle": f"animation.minizin_aether.{mob}.idle",
            "attack": f"animation.minizin_aether.{mob}.attack"},
        "scripts": {"animate": ["idle"]},
    }
    if wings:
        desc["geometry"]["wings"] = f"geometry.minizin_aether.{mob}"
        desc["textures"]["wings"] = f"textures/entity/minizin_aether/{mob}_wings"
        desc["render_controllers"].append("controller.render.minizin_aether.wings")
    return {"format_version": "1.10.0", "minecraft:client_entity": {
        "description": desc}}


def write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_all(bp: Path, rp: Path) -> dict:
    results = {}
    for mob, spec in MOBS.items():
        modelpath = JAVA_MODELS / spec["model"]
        texture = ORIGINAL_TEXTURES / spec["texture"]
        if not modelpath.is_file():
            raise FileNotFoundError(f"Original Java source missing: {modelpath}")
        if not texture.is_file():
            raise FileNotFoundError(f"Original texture missing: {texture}")
        geo, stats = convert_model(modelpath.read_text(encoding="utf-8"), mob,
                                   spec.get("wing_offset", 0.0))
        write(bp / "entities" / f"{mob}.json", entity_bp(mob, spec))
        write(rp / "models/entity" / f"{mob}.geo.json", geo)
        write(rp / "entity" / f"{mob}.entity.json", client_entity(mob))
        write(rp / "animations" / f"{mob}.animation.json", animations(mob))
        dest = rp / "textures/entity/minizin_aether" / f"{mob}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(texture, dest)
        if spec.get("wings_texture"):
            wing_src = ORIGINAL_TEXTURES / spec["wings_texture"]
            if not wing_src.is_file():
                raise FileNotFoundError(f"Original wings missing: {wing_src}")
            shutil.copyfile(wing_src, rp / "textures/entity/minizin_aether" / f"{mob}_wings.png")
        results[mob] = {**stats, "original_java_model": str(modelpath.relative_to(ROOT)),
                        "original_texture": str(texture.relative_to(ROOT)),
                        "animations_exact_java": False, "behavior_exact_java": False}
    write(rp / "render_controllers/minizin_aether.render_controllers.json", {
        "format_version": "1.8.0", "render_controllers": {
            "controller.render.minizin_aether.mob": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"]},
            "controller.render.minizin_aether.wings": {
                "geometry": "Geometry.wings",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.wings"]}}})
    return results
