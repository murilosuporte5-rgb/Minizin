import zipfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CombinedAetherEquipmentTests(unittest.TestCase):
    def test_combined_candidate_keeps_virtual_java_accessory_slots(self):
        candidates = sorted(ROOT.glob('build/combined_all_*_v104*'))
        if not candidates:
            self.skipTest('combined Aether candidate not built yet')
        addon = max(candidates, key=lambda path: (path / 'Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon').stat().st_mtime)
        archive_path = addon / 'Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon'
        with zipfile.ZipFile(archive_path) as outer:
            with zipfile.ZipFile(outer.open('Minizin_Mobile_BP.mcpack')) as bp:
                runtime = bp.read('scripts/aether_equipment.js').decode('utf-8')
                main = bp.read('scripts/main.js').decode('utf-8')
                self.assertIn('{id:"ring",label:"Anéis",count:2}', runtime)
                self.assertIn('{id:"pendant",label:"Pendants",count:1}', runtime)
                self.assertIn('{id:"accessory",label:"Acessórios",count:2}', runtime)
                self.assertIn('!aether slots', runtime)
                self.assertIn('world.afterEvents.itemUse', runtime)
                self.assertIn('aether_equipment.js', main)
