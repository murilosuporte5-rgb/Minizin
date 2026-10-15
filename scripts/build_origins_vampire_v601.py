#!/usr/bin/env python3
"""Build OriginsPE 6.0.1 (Vampire Nocturnal night vision stability patch).

Based on MIT licensed official OriginsPE v6.0.0.
Replaces original package; never activate simultaneously with v6.0.0 or prior patches.
"""
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

OFFICIAL_URL = "https://github.com/r4isen1920/OriginsPE/releases/download/v6.0.0/OriginsPE-v6.0.0.mcaddon"
BASE = "behavior_packs/BP/"
BP = BASE + "manifest.json"
RP = "resource_packs/RP/manifest.json"
SCRIPT = BASE + "scripts/main.js"
OLD = "t.addEffect(y.NightVision,dc*12,{showParticles:!1})"
NEW = "t.addEffect(y.NightVision,dc*60,{showParticles:!1})"
OUTPUT = Path("releases/OriginsPE_v6.0.1_Vampiro_Nocturnal_Fix.mcaddon")
README = (
    "OriginsPE v6.0.1 Vampire Nocturnal Fix\n"
    "Source: https://github.com/r4isen1920/OriginsPE (MIT license)\n"
    "Changes: NightVision duration 12->60s in Nocturnal only.\n"
    "All original packs, files, UUIDs and license notices preserved.\n"
    "Version bumped for both behavior and resource packs to 6.0.1.\n"
    "IMPORTANT: REPLACE (not combine) original OriginsPE 6.0.0 with v6.0.1.\n"
    "Disable experimental night vision patch v0.1/v0.2 before enabling this.\n"
    "Test on a COPIED world before using Realms. No in-game verification.\n"
)

data = urllib.request.urlopen(OFFICIAL_URL, timeout=90).read()
with zipfile.ZipFile(io.BytesIO(data)) as incoming:
    original_js = incoming.read(SCRIPT).decode("utf-8")
    assert original_js.count(OLD) == 1, "Cannot safely identify original Nocturnal routine"
    modified = {SCRIPT: original_js.replace(OLD, NEW).encode()}
    for key in [BP, RP]:
        obj = json.loads(incoming.read(key))
        assert obj["header"]["version"] == [6, 0, 0]
        obj["header"]["version"] = [6, 0, 1]
        obj["header"]["name"] = "OriginsPE v6.0.1 - Vampire Night Vision Fix"
        obj["header"]["description"] = "MIT OriginsPE 6.0.0 plus Nocturnal vision stability correction."
        for mod in obj.get("modules", []):
            if mod.get("version") == [6, 0, 0]:
                mod["version"] = [6, 0, 1]
        for dep in obj.get("dependencies", []):
            if dep.get("uuid") in {
                "6a7bdced-90c9-457b-8db2-78871e5d5705",
                "7cf56d1a-5c7b-40f7-8d90-f8b8d3931390",
            }:
                dep["version"] = [6, 0, 1]
        modified[key] = json.dumps(obj, indent=2, ensure_ascii=False).encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as target:
        for entry in incoming.infolist():
            target.writestr(entry, modified.get(entry.filename, incoming.read(entry)))
        target.writestr(BASE + "NIGHT_VISION_FIX_v6.0.1.txt", README)
with zipfile.ZipFile(OUTPUT) as test:
    assert test.testzip() is None
    assert test.read(SCRIPT).decode().count(NEW) == 1
    assert len(test.namelist()) == len(zipfile.ZipFile(io.BytesIO(data)).namelist()) + 1
print("BUILT:", OUTPUT)
print("SIZE:", OUTPUT.stat().st_size)
print("SHA256:", hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
