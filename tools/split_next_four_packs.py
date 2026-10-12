#!/usr/bin/env python3
"""Split already-converted four-mod Bedrock resources into four independent addons.

Consumes build/next_four created by existing Minizin tools. Never fabricates
textures/models or reads raw Java .jar files. Each output has unique RP/BP UUIDs,
only the corresponding resources, its own Script API entrypoint and provenance.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODS = ("mca", "carryon", "rftools", "origins")
SCRIPT_MAP = {
    "mca": ("core.js", "mca.js"),
    "carryon": ("core.js", "carryon.js"),
    "rftools": ("core.js", "rftools.js"),
    "origins": ("core.js", "origins.js", "catalog.js"),
}
ENTRYPOINTS = {
    "mca": '''import {installMCA} from "./mca.js";
installMCA();
''',
    "carryon": '''import {world,system} from "@minecraft/server";
import {installCarryOn,release} from "./carryon.js";
import {tell} from "./core.js";
installCarryOn();
world.beforeEvents.chatSend.subscribe(ev=>{
  const cmd=ev.message.trim().toLowerCase();
  if(cmd!=="!carryon soltar"&&cmd!=="!minizin soltar")return;
  ev.cancel=true;
  system.run(()=>{
    if(!release(ev.sender))tell(ev.sender,"Você não está carregando um animal.");
  });
});
''',
    "rftools": '''import {world,system} from "@minecraft/server";
import {openMachine} from "./rftools.js";
world.beforeEvents.chatSend.subscribe(ev=>{
  const cmd=ev.message.trim().toLowerCase();
  if(cmd!=="!rftools maquina"&&cmd!=="!rftools máquina"&&
     cmd!=="!minizin maquina"&&cmd!=="!minizin máquina")return;
  ev.cancel=true;
  system.run(()=>openMachine(ev.sender));
});
''',
    "origins": '''import {world,system} from "@minecraft/server";
import {installOrigins,chooseOrigin,currentOrigin} from "./origins.js";
installOrigins();
world.beforeEvents.chatSend.subscribe(ev=>{
  const cmd=ev.message.trim().toLowerCase();
  if(!["!origins","!origins escolher","!origins atual",
       "!minizin origins","!minizin origens","!minizin origem"].includes(cmd))return;
  ev.cancel=true;
  system.run(()=>{
    if(cmd==="!origins atual"||cmd==="!minizin origem")currentOrigin(ev.sender);
    else chooseOrigin(ev.sender);
  });
});
''',
}


def unique_uuid(mod: str, identifier: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
        f"https://github.com/murilosuporte5-rgb/Minizin/bedrock/{mod}/{identifier}"))


def include_resource(mod: str, kind: str, path: str) -> bool:
    """Select resources by *path ownership*, not fuzzy substring matching."""
    if kind == "BP":
        return (path.startswith(f"items/minizin_{mod}_")
                or (mod == "mca" and path.startswith("entities/mca_")))
    if path == "textures/item_texture.json":
        return False  # filtered and regenerated separately
    if path.startswith(f"textures/items/minizin/{mod}/"):
        return True
    if mod == "mca" and path.startswith("textures/items/minizin/mca_generated/"):
        return True
    if path.startswith(f"textures/minizin/{mod}/"):
        return True
    if mod == "mca":
        return (path.startswith("textures/entity/minizin/mca_")
                or path.startswith("entity/mca_")
                or path.startswith("models/entity/minizin_mca_")
                or path.startswith("render_controllers/minizin_mca."))
    if mod == "rftools":
        return (path.startswith("textures/entity/minizin/rftools_")
                or path.startswith("models/entity/rftools_"))
    return False


def manifest(mod: str, kind: str, template: dict) -> dict:
    result = json.loads(json.dumps(template))
    label = {"mca": "MCA Reborn", "carryon": "Carry On",
             "rftools": "RFTools", "origins": "Origins"}[mod]
    result["header"]["name"] = f"Minizin {label} - {kind} (experimental)"
    result["header"]["description"] = (
        f"Standalone Bedrock experimental port: {label}; original resources reused.")
    result["header"]["uuid"] = unique_uuid(mod, f"{kind}-header")
    for i, module in enumerate(result["modules"]):
        module["uuid"] = unique_uuid(mod, f"{kind}-module-{i}")
    if kind == "BP":
        rp_uuid = unique_uuid(mod, "RP-header")
        for dep in result.get("dependencies", []):
            if "uuid" in dep:
                dep["uuid"] = rp_uuid
        if mod in ("carryon",):
            result["dependencies"] = [
                d for d in result["dependencies"]
                if d.get("module_name") != "@minecraft/server-ui"
            ]
    return result


def write_json(dest: Path, data: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def build_one(mod: str, staged: Path, output: Path) -> dict:
    if mod not in MODS:
        raise ValueError(f"Unknown mod {mod}")
    for kind in ("BP", "RP"):
        if not (staged / kind / "manifest.json").is_file():
            raise FileNotFoundError(f"Staged pack not found: {staged / kind}")
    target = output / mod
    if target.exists():
        shutil.rmtree(target)
    counts = {"BP": 0, "RP": 0}
    for kind in ("BP", "RP"):
        original = staged / kind
        for path in sorted(original.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(original).as_posix()
            if not include_resource(mod, kind, rel):
                continue
            dest = target / kind / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            counts[kind] += 1
        template = json.loads((original / "manifest.json").read_text(encoding="utf-8"))
        write_json(target / kind / "manifest.json", manifest(mod, kind, template))

    src_scripts = staged / "BP/scripts"
    dest_scripts = target / "BP/scripts"
    dest_scripts.mkdir(parents=True, exist_ok=True)
    for name in SCRIPT_MAP[mod]:
        source = src_scripts / name
        if not source.is_file():
            raise FileNotFoundError(f"Required script missing: {source}")
        shutil.copy2(source, dest_scripts / name)
    (dest_scripts / "main.js").write_text(ENTRYPOINTS[mod], encoding="utf-8")

    # Include *only* icons belonging to this mod; IDs remain unchanged so
    # existing item definitions still resolve to their original PNGs.
    texture_registry = staged / "RP/textures/item_texture.json"
    icon_count = 0
    if texture_registry.is_file():
        registry = json.loads(texture_registry.read_text(encoding="utf-8"))
        filtered = {
            key: value for key, value in registry.get("texture_data", {}).items()
            if key.startswith(f"minizin_{mod}_")
        }
        if filtered:
            registry["texture_data"] = filtered
            registry["resource_pack_name"] = f"minizin_{mod}"
            write_json(target / "RP/textures/item_texture.json", registry)
            icon_count = len(filtered)
            for ident, data in filtered.items():
                refs = data.get("textures", [])
                if isinstance(refs, str):
                    refs = [refs]
                for ref in refs:
                    texture = target / "RP" / (ref + ".png")
                    if not texture.is_file():
                        raise ValueError(f"{mod}: missing icon for {ident}: {texture}")

    # Licenses and provenance are stored next to the addon (outside its archive).
    license_file = staged / "licenses" / f"{mod}.txt"
    if license_file.is_file():
        shutil.copy2(license_file, target / "LICENSE_UPSTREAM.txt")
    source_report = staged / "asset_report.json"
    origins = []
    if source_report.is_file():
        report = json.loads(source_report.read_text(encoding="utf-8"))
        origins = [r for r in report.get("source_files", []) if r.get("upstream") == mod]
    summary = {
        "mod": mod, "converted_resource_counts": counts,
        "icon_registry_entries": icon_count,
        "original_asset_provenance": origins,
        "limits": [
            "Experimental Bedrock script/runtime only, not Java feature parity.",
            "Source files and original rendering need QA in Minecraft Bedrock Android.",
            "Verify applicable asset reuse and redistribution licenses before sharing."
        ]
    }
    write_json(target / "PROVENANCE.json", summary)
    addon = target / f"Minizin_{mod}_Standalone_Prototype.mcaddon"
    with zipfile.ZipFile(addon, "w", compression=zipfile.ZIP_STORED) as z:
        for kind in ("BP", "RP"):
            z.writestr(f"Minizin_{mod}_{kind}.mcpack", pack(target / kind))
    validate_bundle(addon, mod)
    summary["mcaddon"] = addon.name
    summary["bytes"] = addon.stat().st_size
    write_json(target / "PROVENANCE.json", summary)
    return summary


def pack(directory: Path) -> bytes:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for file in sorted(directory.rglob("*")):
            if file.is_file():
                z.write(file, file.relative_to(directory).as_posix())
    return data.getvalue()


def validate_bundle(addon: Path, mod: str) -> None:
    with zipfile.ZipFile(addon) as z:
        expected = {f"Minizin_{mod}_{k}.mcpack" for k in ("BP", "RP")}
        if set(z.namelist()) != expected:
            raise ValueError(f"Unexpected archive components: {z.namelist()}")
        manifests = {}
        for kind in ("BP", "RP"):
            with zipfile.ZipFile(io.BytesIO(z.read(f"Minizin_{mod}_{kind}.mcpack"))) as p:
                manifests[kind] = json.loads(p.read("manifest.json"))
                if kind == "BP" and "scripts/main.js" not in p.namelist():
                    raise ValueError(f"{mod}: missing script entrypoint")
        expected_rp = manifests["RP"]["header"]["uuid"]
        deps = manifests["BP"].get("dependencies", [])
        if not any(dep.get("uuid") == expected_rp for dep in deps):
            raise ValueError(f"{mod}: dependency UUID mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", type=Path, default=ROOT / "build/next_four")
    parser.add_argument("--output", type=Path, default=ROOT / "build/independent")
    parser.add_argument("--mod", choices=(*MODS, "all"), default="all")
    args = parser.parse_args()
    selected = MODS if args.mod == "all" else (args.mod,)
    if args.output.resolve() == args.staged.resolve():
        parser.error("Output and staging directories must differ")
    results = [build_one(mod, args.staged, args.output) for mod in selected]
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
