"""Regression gates for a linked Aether portal and runnable world overlays."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.overlay_aether_world_pack import overlay


ROOT = Path(__file__).resolve().parents[1]


class WorldIntegrationRegressions(unittest.TestCase):
    def test_exploration_does_not_place_return_frames(self):
        source = (ROOT / "bedrock/worlds/aether/main.js").read_text(encoding="utf-8")
        generation = source.split("async function generateCell", 1)[1].split("function enqueue", 1)[0]
        visit = source.split("async function visitAether", 1)[1].split("function returnOverworld", 1)[0]
        self.assertNotIn("addExitFrame(", generation)
        self.assertIn("addExitFrame(", visit)
        self.assertIn("world.getDynamicProperty(key)", visit)
        self.assertIn("world.setDynamicProperty(key, true)", visit)

    def test_overlay_connects_runtime_and_keeps_machine_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, aether, bop = (root / name for name in ("combined", "aether", "bop"))
            (source / "BP/scripts/aether_full_v3").mkdir(parents=True)
            (source / "BP/scripts/main.js").write_text('import "./creatures.js";\n')
            (source / "BP/scripts/aether_full_v3/main.js").write_text(
                'import "./aether_freezer.js";\nimport "./aether_incubator.js";\n')
            (source / "BP/manifest.json").write_text(json.dumps({"dependencies": [
                {"module_name": "@minecraft/server", "version": "2.0.0"}]}))
            for world_pack in (aether, bop):
                (world_pack / "BP/scripts").mkdir(parents=True)
                (world_pack / "BP/scripts/main.js").write_text("const worldGenerationActive = true;\n")
                (world_pack / "RP").mkdir()
            first, final = root / "first", root / "final"
            overlay(source, aether, first)
            overlay(first, bop, final, "bop_full_v3")
            entry = (final / "BP/scripts/main.js").read_text()
            self.assertEqual(entry.count('import "./aether_full_v3/main.js";'), 1)
            self.assertEqual(entry.count('import "./bop_full_v3/main.js";'), 1)
            aether_entry = (final / "BP/scripts/aether_full_v3/main.js").read_text()
            self.assertIn("worldGenerationActive", aether_entry)
            self.assertIn('import "./aether_freezer.js";', aether_entry)
            self.assertIn('import "./aether_incubator.js";', aether_entry)
            dependencies = json.loads((final / "BP/manifest.json").read_text())["dependencies"]
            self.assertEqual(dependencies[0]["version"], "beta")


if __name__ == "__main__":
    unittest.main()
