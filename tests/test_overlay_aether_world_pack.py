import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools/overlay_aether_world_pack.py"
spec = importlib.util.spec_from_file_location("overlay_aether_world_pack", SCRIPT)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class OverlayAetherTests(unittest.TestCase):
    def test_flipbook_is_merged_at_bedrock_root_with_combined_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            destination = root / "textures/flipbook_texture.json"
            source.write_text(json.dumps([{
                "flipbook_texture": "textures/blocks/minizin_aether_aether_portal",
                "atlas_tile": "minizin_aether_aether_portal",
                "frames": list(range(32)),
                "ticks_per_frame": 2,
            }]), encoding="utf-8")
            destination.parent.mkdir(parents=True)
            destination.write_text(json.dumps([{
                "flipbook_texture": "textures/blocks/existing",
                "atlas_tile": "existing",
                "ticks_per_frame": 4,
            }]), encoding="utf-8")

            overlay.overlay_flipbook(source, destination)
            entries = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(entries), 2)
            aether = entries[1]
            self.assertEqual(
                aether["flipbook_texture"],
                "textures/aether_full_v3/blocks/minizin_aether_aether_portal",
            )
            self.assertEqual(aether["atlas_tile"], "aether_full_v3_minizin_aether_aether_portal")
            self.assertEqual(aether["frames"], list(range(32)))
            self.assertEqual(aether["ticks_per_frame"], 2)


if __name__ == "__main__":
    unittest.main()
