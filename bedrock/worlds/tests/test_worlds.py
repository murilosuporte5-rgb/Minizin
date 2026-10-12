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
            self.assertEqual(bp["header"]["min_engine_version"], [1, 21, 110] if mod == "bop" else [1, 21, 80])
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

    def test_directional_original_textures_for_logs_and_grass(self):
        self.assertEqual(worlds.FACES["aether"]["aether_grass"]["up"],
                         "natural/aether_grass_block_top.png")
        for mod, materials in worlds.FACES.items():
            for name, faces in materials.items():
                item = worlds.block_def(mod, name)["minecraft:block"]
                for face, source in faces.items():
                    self.assertTrue(source.endswith(".png"))
                    self.assertEqual(
                        item["components"]["minecraft:material_instances"][face]["texture"],
                        f"{worlds.NAMESPACE[mod]}_{name}_{face}")

    def test_pin_java_biome_climate_and_water(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "lavender_field.json"
            original.write_text(json.dumps({
                "temperature": 0.8, "downfall": 0.7,
                "effects": {"water_color": "#3f76e4", "grass_color": "#a1c36d"}
            }), encoding="utf-8")
            with patch.object(worlds, "BIOME_SOURCE", Path(tmp)):
                spec = worlds.java_biome_spec("lavender_field", worlds.BIOMES["lavender_field"])
                self.assertEqual(spec["temp"], .8)
                self.assertEqual(spec["rain"], .7)
                self.assertEqual(spec["water"], "#3f76e4")
                self.assertEqual(spec["grass_color"], "#a1c36d")
                with self.assertRaises(FileNotFoundError):
                    worlds.java_biome_spec("mystic_grove", worlds.BIOMES["mystic_grove"])

    def test_original_aether_skyroot_biome_references(self):
        import unittest.mock as mock
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in worlds.AETHER_BIOME_DENSITIES:
                (root / f"{name}.json").write_text(json.dumps({
                    "temperature": 0.8, "downfall": 0,
                    "features": [[f"aether:{name}_trees"], ["aether:cold_aercloud"]]
                }), encoding="utf-8")
            with mock.patch.object(worlds, "AETHER_BIOME_SOURCE", root):
                profiles = worlds.aether_biome_profiles()
            self.assertEqual(len(profiles), 4)
            self.assertTrue(all(p["java_tree_feature"] in p["java_feature_refs"] for p in profiles))
            self.assertGreater(profiles[0]["tree_attempts"], profiles[2]["tree_attempts"])

    def test_silver_dungeon_blocks_are_not_fake_breakable_ornaments(self):
        for name in ("locked_angelic_stone", "boss_doorway_angelic_stone"):
            self.assertIn(name, worlds.ASSETS["aether"])
            components = worlds.block_def("aether", name)["minecraft:block"]["components"]
            self.assertIs(components["minecraft:destructible_by_mining"], False)
            self.assertIs(components["minecraft:destructible_by_explosion"], False)

    def test_portal_collision_is_disabled_and_axis_is_recorded(self):
        b = worlds.block_def("aether", "aether_portal")["minecraft:block"]
        self.assertEqual(b["description"]["states"]["minizin_aether:axis"], ["x", "z"])
        self.assertIs(b["components"]["minecraft:collision_box"], False)
        self.assertEqual(len(b["permutations"]), 1)

    def test_nine_biomes_are_independent_and_linked(self):
        self.assertEqual(len(worlds.BIOMES), 9)
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
        self.assertIn("placeOriginalDungeon", src)
        self.assertIn('from "./biome_profiles.js"', src)
        self.assertIn("quicksoilTick", src)
        self.assertIn("aercloudTick", src)
        self.assertIn("await generateCell(cx, cz)", src)
        self.assertIn("addExitFrame(dim, exitHeight, cx, cz)", src)
        self.assertIn("player.setDynamicProperty(RETURN_KEY", src)
        self.assertNotIn("eval(", src)
        bop = (SCRIPT.parent / "bop/main.js").read_text(encoding="utf-8")
        self.assertIn("world.setDynamicProperty(key, true)", bop)
        self.assertIn("PLACEMENTS_PER_TICK", bop)
        self.assertIn("minecraft:overworld", bop)


if __name__ == "__main__":
    unittest.main()
