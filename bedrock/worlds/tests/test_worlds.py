"""Structural checks for the isolated Minizin Worlds builder.

These do not simulate Minecraft Bedrock. Actual chunk generation, rendering,
Beta API behavior and Android performance require on-device tests.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "build_worlds.py"
spec = importlib.util.spec_from_file_location("build_worlds", SCRIPT)
worlds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worlds)


class WorldBuilderTests(unittest.TestCase):
    def test_manifests_are_unique_and_connected(self):
        identifiers = []
        for mod in ("aether", "bop"):
            bp = worlds.manifest(mod, "BP")
            rp = worlds.manifest(mod, "RP")
            self.assertEqual(bp["dependencies"][0]["uuid"], rp["header"]["uuid"])
            self.assertEqual(bp["header"]["min_engine_version"], [1, 21, 80])
            identifiers.extend([bp["header"]["uuid"], rp["header"]["uuid"],
                                bp["modules"][0]["uuid"], rp["modules"][0]["uuid"]])
            self.assertEqual(bp, worlds.manifest(mod, "BP"))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        beta = worlds.manifest("aether", "BP")["dependencies"][-1]
        self.assertEqual(beta, {"module_name": "@minecraft/server", "version": "beta"})

    def test_aether_ids_and_original_asset_locations(self):
        expect = {"holystone", "aether_grass", "skyroot_log", "skyroot_leaves",
                  "ambrosium_ore", "zanite_ore", "aether_portal"}
        self.assertTrue(expect.issubset(worlds.ASSETS["aether"]))
        self.assertEqual(worlds.ASSETS["aether"]["aether_portal"][0],
                         "miscellaneous/aether_portal.png")
        for mod, names in worlds.ASSETS.items():
            for name, (path, _sound) in names.items():
                self.assertTrue(path.endswith(".png"), name)
                b = worlds.block_def(mod, name)["minecraft:block"]
                self.assertEqual(b["description"]["identifier"],
                                 worlds.NAMESPACE[mod] + ":" + name)
                self.assertIn("minecraft:material_instances", b["components"])

    def test_portal_collision_is_disabled_and_axis_is_recorded(self):
        b = worlds.block_def("aether", "aether_portal")["minecraft:block"]
        self.assertEqual(b["description"]["states"]["minizin_aether:axis"], ["x", "z"])
        self.assertIs(b["components"]["minecraft:collision_box"], False)
        self.assertEqual(len(b["permutations"]), 1)

    def test_four_biomes_are_independent_and_linked(self):
        for name, entry in worlds.BIOMES.items():
            obj = worlds.biome_def(name, entry)["minecraft:biome"]
            self.assertEqual(obj["description"]["identifier"], f"minizin_bop:{name}")
            self.assertIn(name, obj["components"]["minecraft:tags"]["tags"])
            self.assertIn("minecraft:overworld_generation_rules", obj["components"])
            if entry["tree"]:
                feat = worlds.tree_feature(entry["tree"])["minecraft:tree_feature"]
                self.assertEqual(feat["description"]["identifier"],
                                 f"minizin_bop:{entry['tree']}_feature")
                rule = worlds.rule(name, entry["tree"], entry["trees"])
                self.assertEqual(rule["minecraft:feature_rules"]["conditions"]
                                 ["minecraft:biome_filter"]["value"], name)
            if entry["flower"]:
                self.assertEqual(worlds.flower_feature(entry["flower"])
                                 ["minecraft:single_block_feature"]["places_block"],
                                 f"minizin_bop:{entry['flower']}")

    def test_missing_original_asset_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist.png"
            with self.assertRaises(FileNotFoundError):
                worlds.copy_texture(missing, Path(tmp) / "result.png", "bop", "lavender")

    def test_generated_models_are_valid_json_objects(self):
        for name in ("portal", "cross"):
            model = worlds.geometry(name)
            self.assertEqual(model["minecraft:geometry"][0]["description"]["identifier"],
                             f"geometry.minizin_worlds.{name}")
            self.assertTrue(model["minecraft:geometry"][0]["bones"][0]["cubes"])
            self.assertIsInstance(json.loads(json.dumps(model)), dict)

    def test_static_script_uses_beta_registration_and_safe_preload(self):
        src = (SCRIPT.parent / "aether/main.js").read_text(encoding="utf-8")
        self.assertIn("registerCustomDimension(SKY_ID)", src)
        self.assertIn("createTickingArea", src)
        self.assertIn("playerInteractWithBlock", src)
        self.assertIn("world.setDynamicProperty(key, true)", src)
        self.assertIn("removeTickingArea", src)
        self.assertIn("BLOCKS_PER_TICK", src)
        self.assertNotIn("eval(", src)


if __name__ == "__main__":
    unittest.main()
