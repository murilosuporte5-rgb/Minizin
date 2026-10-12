"""Regression tests for source-backed Aether mobs/loot and all 68 BoP biome JSON.

Static contracts only; engine animation, native biome selection and combat
require validation on a real Bedrock Android client.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


models = load("model_converter", "bedrock/worlds/aether/build_entities.py")
loot = load("loot_converter", "bedrock/worlds/aether/convert_loot.py")
biomes = load("all_bop_biomes", "bedrock/worlds/bop/worldgen_full.py")


class OriginalAetherEntityTests(unittest.TestCase):
    def test_three_bosses_and_seven_sourced_mobs_have_real_models(self):
        for name in ("slider", "valkyrie_queen", "sun_spirit"):
            self.assertIn(name, models.MOBS)
            self.assertIn(name, models.BOSSES)
        self.assertGreaterEqual(len(models.MOBS), 9)
        for name, cfg in models.MOBS.items():
            path = models.JAVA_MODELS / cfg["model"]
            self.assertTrue(path.is_file(), str(path))
            self.assertTrue((models.ORIGINAL_TEXTURES / cfg["texture"]).is_file())
            geo, report = models.convert_model(path.read_text(), name)
            self.assertGreaterEqual(report["converted_cubes"], 1)
            self.assertTrue(geo["minecraft:geometry"][0]["bones"])
            self.assertTrue(all(b["name"] for b in geo["minecraft:geometry"][0]["bones"]))

    def test_composite_native_quadruped_body_with_original_java_wings(self):
        self.assertEqual(len(models.MOBS), 16)
        for mob, body in (("phyg", "geometry.pig.v3"),
                          ("flying_cow", "geometry.cow.v2")):
            descriptor = models.client_entity(mob)["minecraft:client_entity"]["description"]
            self.assertEqual(descriptor["geometry"]["default"], body)
            self.assertEqual(descriptor["geometry"]["wings"],
                             f"geometry.minizin_aether.{mob}")
            self.assertTrue(descriptor["textures"]["wings"].endswith(mob + "_wings"))
            self.assertIn("controller.render.minizin_aether.wings",
                          descriptor["render_controllers"])
            spec = models.MOBS[mob]
            self.assertTrue((models.ORIGINAL_TEXTURES / spec["wings_texture"]).is_file())
        source = (models.JAVA_MODELS / "CloudMinionModel.java").read_text()
        _, audit = models.convert_model(source, "cloud_minion")
        self.assertEqual(audit["converted_cubes"], 5)

    def test_bosses_recover_model_counts_and_health_from_java(self):
        expected = {"slider": (400, 1), "valkyrie_queen": (500, 42),
                    "sun_spirit": (500, 11)}
        for name, (hp, cubes) in expected.items():
            self.assertEqual(models.MOBS[name]["health"], hp)
            src = (models.JAVA_MODELS / models.MOBS[name]["model"]).read_text()
            _, report = models.convert_model(src, name)
            self.assertEqual(report["converted_cubes"], cubes, name)
            bp = models.entity_bp(name, models.MOBS[name])
            self.assertEqual(bp["minecraft:entity"]["components"]["minecraft:health"]["max"], hp)
            self.assertEqual(bp["minecraft:entity"]["description"]["identifier"],
                             "minizin_aether:" + name)

    def test_source_derived_animation_bones_are_declared(self):
        for mob, bones in models.KNOWN_ANIMATION_BONES.items():
            anim = models.animations(mob)
            clips = anim["animations"]
            self.assertIn(f"animation.minizin_aether.{mob}.attack", clips)
            self.assertIn(f"animation.minizin_aether.{mob}.idle", clips)
            self.assertTrue(bones)
            self.assertNotEqual(clips[f"animation.minizin_aether.{mob}.attack"],
                                clips[f"animation.minizin_aether.{mob}.idle"])

    def test_original_boss_keys_in_loot_mapping(self):
        for tier in ("bronze", "silver", "gold"):
            id_ = f"{tier}_dungeon_key"
            self.assertIn(id_, loot.ITEM_SOURCE)
            self.assertTrue((loot.ITEM_TEXTURES / loot.ITEM_SOURCE[id_]).is_file())
        tables = loot.original_tables()
        for b in models.BOSSES:
            self.assertIn("aether:entities/" + b, tables)
        self.assertGreaterEqual(len(tables), 35)
        a = tables["aether:entities/slider"]
        names = [x.get("name") for pool in a["pools"] for x in pool["entries"]]
        self.assertIn("aether:bronze_dungeon_key", names)

    def test_missing_java_loot_never_becomes_fake_item(self):
        registered = {"holystone", "sun_altar"}
        self.assertIsNone(loot.item_name("aether:unported_power_sword", registered))
        self.assertEqual(loot.item_name("aether:bronze_dungeon_key", registered),
                         "minizin_aether:bronze_dungeon_key")
        self.assertEqual(loot.item_name("minecraft:golden_sword", registered),
                         "minecraft:golden_sword")

    def test_boss_combat_fights_have_distinct_gates(self):
        src = (ROOT / "bedrock/worlds/aether/bosses.js").read_text()
        self.assertIn("chargeSlider", src)
        self.assertIn("queenCombat", src)
        self.assertIn("sunCombat", src)
        self.assertIn("minecraft:snowball", src)
        self.assertIn("spawnDungeonBoss", src)
        self.assertIn("DUNGEON_REWARDS", src)
        self.assertIn("dungeon_cleared", src)


class FullBopTests(unittest.TestCase):
    def test_native_replacements_are_dimension_scoped(self):
        self.assertIsNotNone(biomes.native_replacement("end_reef"))
        self.assertIsNone(biomes.native_replacement("glowing_grotto"))
        self.assertIsNone(biomes.native_replacement("spider_nest"))
        self.assertEqual(biomes.native_replacement("redwood_forest")["dimension"],
                         "minecraft:overworld")
        self.assertEqual(biomes.native_replacement("erupting_inferno")["dimension"],
                         "minecraft:nether")
        for name in ("redwood_forest", "lavender_field", "erupting_inferno"):
            rule = biomes.native_replacement(name)
            self.assertGreater(rule["amount"], 0)
            self.assertTrue(rule["targets"])
            self.assertLessEqual(rule["amount"], 1)
            self.assertLessEqual(rule["noise_frequency_scale"], 100)

    def test_all_pinned_java_biomes_mapped_without_fake_end_generation(self):
        src = ROOT / "mods/19-biomes-o-plenty/upstream/common/src/generated/resources/data/biomesoplenty/worldgen/biome"
        names = [p.stem for p in src.glob("*.json")]
        self.assertEqual(len(names), 68)
        self.assertEqual(len(biomes.NETHER), 5)
        self.assertTrue(biomes.NETHER.issubset(set(names)))
        self.assertEqual(biomes.CAVE, {"glowing_grotto", "spider_nest"})
        self.assertTrue(biomes.CAVE.issubset(set(names)))
        for p in src.glob("*.json"):
            data = json.loads(p.read_text())
            out = biomes.convert_biome(p.stem, data)
            self.assertEqual(out["biome"]["minecraft:biome"]["description"]["identifier"],
                             f"minizin_bop:{p.stem}")
            self.assertEqual(out["biome"]["minecraft:biome"]["components"]["minecraft:climate"]["temperature"],
                             data["temperature"])
            components = out["biome"]["minecraft:biome"]["components"]
            self.assertEqual("minecraft:replace_biomes" in components,
                             p.stem not in biomes.CAVE)

    def test_biome_dimensions_are_grounded_in_original_java_registry(self):
        registry = (ROOT / "mods/19-biomes-o-plenty/upstream/common/src/main/java/biomesoplenty/api/biome/BOPBiomes.java").read_text()
        nether_source = "\\n".join(
            (ROOT / ("mods/19-biomes-o-plenty/upstream/common/src/main/java/"
                     "biomesoplenty/worldgen/" + filename)).read_text()
            for filename in ("BOPNetherRegionCommon.java", "BOPNetherRegionRare.java")
        )
        for name in biomes.NETHER:
            self.assertIn(f"BOPBiomes.{name.upper()}", nether_source, name)
        for name in ("end_reef", "end_wilds", "volcano", "volcanic_plains"):
            self.assertIn(f'registerOverworld("{name}")', registry, name)
            self.assertEqual(biomes.native_replacement(name)["dimension"], "minecraft:overworld")

    def test_mapped_java_decorations_use_registered_species(self):
        tree, flower = biomes.selected_feature(
            "redwood_forest", ["biomesoplenty:redwood_tree"],
            {"redwood_log", "redwood_leaves", "lavender"})
        self.assertEqual(tree, "redwood")
        self.assertIsNone(flower)
        missing, _ = biomes.selected_feature("mystery", ["unregistered_feature"], set())
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
