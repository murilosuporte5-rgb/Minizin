import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.split_next_four_packs import MODS, build_one, unique_uuid


class IndependentBedrockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.staged = base / "staged"
        self.out = base / "split"
        self.bp = self.staged / "BP"
        self.rp = self.staged / "RP"
        for root, kind in ((self.bp, "BP"), (self.rp, "RP")):
            root.mkdir(parents=True)
            self.write_json(root / "manifest.json", {
                "format_version": 2,
                "header": {"name": "Combined", "uuid": "shared-uuid",
                           "version": [0, 1, 0], "min_engine_version": [1, 21, 0]},
                "modules": [{"type": "data", "uuid": "data-uuid", "version": [0, 1, 0]}]
                + ([{"type": "script", "uuid": "script-uuid", "language": "javascript",
                     "entry": "scripts/main.js", "version": [0, 1, 0]}]
                   if kind == "BP" else []),
                "dependencies": ([{"uuid": "shared-rp", "version": [0, 1, 0]},
                                  {"module_name": "@minecraft/server", "version": "2.0.0"},
                                  {"module_name": "@minecraft/server-ui", "version": "2.0.0"}]
                                 if kind == "BP" else []),
            })
        for name in ("core", "mca", "carryon", "rftools", "origins", "catalog"):
            dest = self.bp / "scripts" / (name + ".js")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("export const ok = true;\n")
        for name in ("mca", "rftools", "origins"):
            self.write_json(self.bp / "items" / f"minizin_{name}_test.json",
                            {"source": name})
            png = self.rp / "textures" / "items" / "minizin" / name / "test.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"PNG fixture")
        self.write_json(self.bp / "entities" / "mca_female_0.json", {"id": "mca"})
        self.write_json(self.rp / "entity" / "mca_female_0.entity.json", {"id": "mca"})
        self.write_json(self.rp / "models" / "entity" / "rftools_machine.geo.json",
                        {"id": "rftools"})
        self.write_json(self.rp / "textures" / "item_texture.json", {
            "resource_pack_name": "combined", "texture_name": "atlas.items",
            "texture_data": {
                f"minizin_{name}_test": {
                    "textures": f"textures/items/minizin/{name}/test"}
                for name in ("mca", "rftools", "origins")
            }
        })
        self.write_json(self.staged / "asset_report.json", {
            "source_files": [{"upstream": name, "source": name + "/asset.png"}
                             for name in MODS]
        })
        for name in MODS:
            p = self.staged / "licenses" / (name + ".txt")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("license for " + name)

    @staticmethod
    def write_json(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj), encoding="utf-8")

    def test_four_independent_packs_and_no_resource_bleed(self):
        rp_uuids = set()
        bp_uuids = set()
        for mod in MODS:
            report = build_one(mod, self.staged, self.out)
            self.assertEqual(report["mod"], mod)
            addon = self.out / mod / report["mcaddon"]
            self.assertTrue(addon.is_file())
            with zipfile.ZipFile(addon) as bundle:
                self.assertEqual(len(bundle.namelist()), 2)
                with zipfile.ZipFile(io.BytesIO(bundle.read(
                        f"Minizin_{mod}_BP.mcpack"))) as bp:
                    bp_files = set(bp.namelist())
                    bp_manifest = json.loads(bp.read("manifest.json"))
                    self.assertIn("scripts/main.js", bp_files)
                    self.assertIn("scripts/core.js", bp_files)
                    self.assertIn(f"scripts/{mod}.js", bp_files)
                    for other in MODS:
                        if other != mod:
                            self.assertNotIn(f"scripts/{other}.js", bp_files)
                            self.assertNotIn(f"items/minizin_{other}_test.json", bp_files)
                    self.assertEqual("entities/mca_female_0.json" in bp_files,
                                     mod == "mca")
                with zipfile.ZipFile(io.BytesIO(bundle.read(
                        f"Minizin_{mod}_RP.mcpack"))) as rp:
                    rp_files = set(rp.namelist())
                    rp_manifest = json.loads(rp.read("manifest.json"))
                    self.assertEqual("entity/mca_female_0.entity.json" in rp_files,
                                     mod == "mca")
                    self.assertEqual(
                        "models/entity/rftools_machine.geo.json" in rp_files,
                        mod == "rftools")
                    if mod != "carryon":
                        atlas = json.loads(rp.read("textures/item_texture.json"))
                        self.assertEqual(list(atlas["texture_data"]),
                                         [f"minizin_{mod}_test"])
                    else:
                        self.assertNotIn("textures/item_texture.json", rp_files)
                    rp_uuids.add(rp_manifest["header"]["uuid"])
                bp_uuids.add(bp_manifest["header"]["uuid"])
                self.assertTrue(any(
                    d.get("uuid") == rp_manifest["header"]["uuid"]
                    for d in bp_manifest["dependencies"]
                ))
            self.assertEqual(len(report["original_asset_provenance"]), 1)
        self.assertEqual(len(rp_uuids), 4)
        self.assertEqual(len(bp_uuids), 4)

    def test_deterministic_uuids(self):
        self.assertEqual(unique_uuid("origins", "RP-header"),
                         unique_uuid("origins", "RP-header"))
        self.assertNotEqual(unique_uuid("origins", "RP-header"),
                            unique_uuid("mca", "RP-header"))

    def test_missing_source_icon_fails_loudly(self):
        (self.rp / "textures/items/minizin/origins/test.png").unlink()
        with self.assertRaisesRegex(ValueError, "missing icon"):
            build_one("origins", self.staged, self.out)


if __name__ == "__main__":
    unittest.main()
