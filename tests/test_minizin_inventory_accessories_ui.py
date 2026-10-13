"""Offline checks for optional 8-slot Aether JSON UI; Minecraft Android is not emulated.

Run: python -m unittest tests/test_minizin_inventory_accessories_ui.py -v
Needs Pillow, but never copies or publishes original Java model art.
"""
import importlib.util
import io
import json
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools/minizin_inventory_accessories_ui.py"
spec = importlib.util.spec_from_file_location("minizin_aether_ui_patch", MODULE)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

EXISTING_JS = """import {world,system} from "@minecraft/server";
const SLOTS=[{id:"ring",count:2},{id:"accessory",count:2}];
const SLOT_KEY="minizin:aether_accessories_v2";
function menu(player){
const rows=[];const form={button(){return this}};
for(let index=0;index<COUNT;index++){const ref=slotFor(index);form.button(ref.slot.label+" "+(ref.ordinal+1)+": "+label(rows[index]));}
}
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{if(EQUIPMENT[itemStack?.typeId]?.accessory)system.run(()=>menu(source));});
"""


class OverlayTests(unittest.TestCase):
    def test_existing_backend_and_no_hotbar_item(self):
        bp = {"scripts/aether_equipment.js": EXISTING_JS.encode()}
        patch.patch_backend(bp)
        js = bp["scripts/aether_equipment.js"].decode()
        self.assertIn(patch.MARKER, js)
        self.assertIn("MINIZIN_SLOT_ICONS", js)
        self.assertIn("form.button", js)
        self.assertEqual(set(bp), {"scripts/aether_equipment.js"})
        self.assertNotIn("relicario", js.lower())

    def test_no_fake_slots_on_legacy_candidate(self):
        with self.assertRaisesRegex(ValueError, "8-slot"):
            patch.patch_backend({"scripts/aether_equipment.js": b"const SLOTS=[];"})

    def test_visual_guide_for_android_and_desktop(self):
        rp = {}
        patch.patch_ui(rp)
        self.assertIn("ui/inventory_screen_pocket.json", rp)
        self.assertIn("ui/inventory_screen.json", rp)
        for target, key in (("ui/inventory_screen_pocket.json", "recipe_inventory_screen_content_pocket"),
                            ("ui/inventory_screen.json", "recipe_inventory_screen_content")):
            data = patch.parse(rp[target])
            self.assertEqual(data[key]["modifications"][0]["operation"], "insert_back")
        self.assertEqual(len([x for x in rp if x.endswith(".png")]), 6)
        ui = patch.parse(rp["ui/minizin_aether_inventory.json"])
        self.assertEqual(len(ui["overview"]["controls"]), 4)
        self.assertIn("ui/minizin_aether_inventory.json", patch.parse(rp["ui/_ui_defs.json"])["ui_defs"])

    def test_idempotent_overlay_and_fail_closed_double_patch(self):
        rp = {}
        patch.patch_ui(rp)
        first = rp["ui/inventory_screen_pocket.json"]
        patch.patch_ui(rp)
        self.assertEqual(rp["ui/inventory_screen_pocket.json"], first)
        bp = {"scripts/aether_equipment.js": EXISTING_JS.encode()}
        patch.patch_backend(bp)
        with self.assertRaisesRegex(ValueError, "already applied"):
            patch.patch_backend(bp)


if __name__ == "__main__":
    unittest.main()
