"""Java -> Bedrock NBT structure conversion contract tests using synthetic fixtures.

Requires nbtlib, numpy. Does not test rendering or placement in Minecraft.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

import nbtlib

SCRIPT = Path(__file__).resolve().parents[1] / "aether" / "convert_structures.py"
spec = importlib.util.spec_from_file_location("convert_structures", SCRIPT)
convert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert)


def nlist(cls, values):
    return nbtlib.List[cls]([cls(v) for v in values])


def fixture(root: Path, ids: list[str], size=(2, 2, 3)):
    # Minimal genuine Java structure-template tag layout (big-endian, gzip)
    blocks = [
        nbtlib.Compound({
            "pos": nlist(nbtlib.Int, [0, 0, 0]),
            "state": nbtlib.Int(0),
        }),
        nbtlib.Compound({
            "pos": nlist(nbtlib.Int, [1, 1, 2]),
            "state": nbtlib.Int(len(ids)-1),
        }),
    ]
    src = root / "bronze_dungeon" / "sample.nbt"
    src.parent.mkdir(parents=True, exist_ok=True)
    nbtlib.File({
        "size": nlist(nbtlib.Int, size),
        "palette": nbtlib.List[nbtlib.Compound]([
            nbtlib.Compound({"Name": nbtlib.String(name)}) for name in ids
        ]),
        "blocks": nbtlib.List[nbtlib.Compound](blocks),
        "entities": nbtlib.List[nbtlib.Compound]([]),
    }).save(src, gzipped=True, byteorder="big")
    return src


class ConverterTests(unittest.TestCase):
    def test_mapped_java_blocks_roundtrip_little_endian(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = fixture(Path(tmp), ["aether:holystone", "minecraft:glowstone"])
            output = Path(tmp) / "bronze.mcstructure"
            from unittest.mock import patch
            with patch.object(convert, "JAVA_STRUCTURES", Path(tmp)):
                result = convert.convert_file(src, output, {"minizin_aether:holystone"})
            self.assertIn(result["status"], ("converted", "converted_with_omissions"))
            self.assertEqual(result["placed"], 2)
            self.assertEqual(result["size"], [2, 2, 3])
            m = nbtlib.load(output, gzipped=False, byteorder="little")
            self.assertEqual([int(x) for x in m["size"]], [2, 2, 3])
            self.assertEqual(len(m["structure"]["block_indices"]), 2)
            self.assertEqual(len(m["structure"]["block_indices"][0]), 12)
            self.assertEqual(len(m["structure"]["block_indices"][1]), 12)
            palette = [str(x["name"]) for x in
                       m["structure"]["palette"]["default"]["block_palette"]]
            self.assertEqual(palette, ["minizin_aether:holystone", "minecraft:glowstone"])
            # Position flattening must follow Bedrock X * Y * Z ordering.
            blocks = m["structure"]["block_indices"][0]
            self.assertEqual(int(blocks[0]), 0)
            self.assertEqual(int(blocks[11]), 1)
            self.assertTrue(all(int(x) == -1 for x in blocks[1:11]))

    def test_missing_custom_blocks_are_not_turned_into_generic_stone(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = fixture(Path(tmp), ["aether:holystone", "aether:unknown_locked_boss"])
            dest = Path(tmp) / "unmapped.mcstructure"
            from unittest.mock import patch
            with patch.object(convert, "JAVA_STRUCTURES", Path(tmp)):
                report = convert.convert_file(src, dest, {"minizin_aether:holystone"})
            self.assertEqual(report["omitted_palette"], {"aether:unknown_locked_boss": 1})
            m = nbtlib.load(dest, gzipped=False, byteorder="little")
            self.assertEqual(int(m["structure"]["block_indices"][0][11]), -1)

    def test_size_limits_fail_before_allocating_huge_volumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = fixture(Path(tmp), ["minecraft:air"], size=(384, 384, 384))
            with self.assertRaises(ValueError):
                convert.convert_file(src, Path(tmp) / "oversized.mcstructure", set())

    def test_block_aliases_and_no_faked_java_equivalence(self):
        self.assertEqual(convert.translate_block(
            "aether:aether_grass_block", {"minizin_aether:aether_grass"}),
            "minizin_aether:aether_grass")
        self.assertIsNone(convert.translate_block("aether:missing_material", set()))
        self.assertIsNone(convert.translate_block("minecraft:structure_void", set()))


if __name__ == "__main__":
    unittest.main()
