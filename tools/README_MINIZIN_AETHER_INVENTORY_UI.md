# Aether Inventory UI — optional patch for Work (Bedrock Android)

**Target:** experimental combined `.mcaddon` from Work v0.3.8+ that includes `minizin:aether_accessories_v2` with exactly 8 virtual slots.

**What this patch actually does**
- Shows 8 **visual indicators** in the standard and Pocket inventory screen: two rings, pendant, gloves, cape, shield and two relics.
- Adds an icon to each choice in the **existing working** Aether `ActionFormData` equip/remove menu.
- Preserves the current per-player dynamic-property storage and existing Aether effects. All equip/unequip actions still run through the original runtime.
- **Does not add a Relicário item or any new hotbar item.** Open the accessory menu by using a held Aether accessory, or sneaking and interacting empty-handed with a block, as in the existing runtime.
- Fails safely if Work changes the menu implementation or the input is missing the 8-slot Aether backend. Never overwrites the source archive.

**What this does NOT do**
- Cannot create 8 actual clickable, engine-owned inventory slots: the Java accessory API does not exist in Bedrock. The drawn indicators are **visual only** and do not reflect equipped items automatically; their appearance is not the final Java equivalent.
- Does not repair missing PNGs, malformed mob rigs, Waystone or portal behavior. Those are separate findings documented in [the Android QA report](../docs/ANDROID_QA_REAL_REPORT_2026-10-13.md).
- Cannot prove compatibility with all Android screen scales until tested on a real device.

## Build a private candidate

```bash
python -m pip install Pillow
python -m unittest tests/test_minizin_inventory_accessories_ui.py -v
python tools/minizin_inventory_accessories_ui.py \
  build/final_20261013_v038/Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v038.mcaddon \
  build/final_20261013_v038/Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v038_UI.mcaddon
```

Substitute the actual private input location; example path is illustrative, **not verified**. Requires a combined v0.3.8+ candidate containing the current 8-slot script and both nested RP/BP packs. Source `.mcaddon` will not be overwritten.

**Important:** This script is an optional post-build overlay. Work should review/port it into its build pipeline only after validating namespace collisions, JSON UI layout on Pocket, icon loading, native hotbar behavior, and coexistence with existing Resource Packs. Never package third-party copyrighted art publicly without authorizations.

## Acceptance checks on Android

1. Confirm inventory opens properly with the Resource Pack active, both in Survival and Creative, without hiding vanilla armor slots.
2. Confirm the 8 guides appear, **without claiming them to be clickable slots**.
3. Hold an Aether ring, open the original menu, equip/remove, close/reopen and verify item persists.
4. Verify cape/gloves/pendant/2 relic slots; existing in-game bonuses and enchantment preservation.
5. Confirm **no new hotbar item** appears because of this overlay.
6. Check small screen scaling on a 16:9 phone, inventory resized/full-screen, and UI fallback when a conflicting pack is installed.

**Owner:** Work PR #7. Branch intentionally separate; no changes to Codex or Work working branches.