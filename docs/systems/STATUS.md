# Minizin systems — verified and unverified status

Date: 2026-10-12. Branch: feature/minizin-systems, created from repository main.

## Baseline
The checked main branch contains prototype BP/RP manifests at version 0.1.0. An actual v0.2.8 source snapshot is NOT established by these repository files; merging into a separate v0.2.8 addon still requires integration. Reused existing runtime work from feature/original-models-gameplay only for the requested systems, without merging the branch or modifying shared loaders.

## Modules added or changed
- Waystones: placeable stone with original existing geometry/texture, persistent activation/name/ownership and destinations, legacy-entity migration, real dimension teleport with an unloaded-chunk fallback and post-arrival safety check. Cross-dimension/distant chunk-loading reliability is UNTESTED on Android.
- Sophisticated Backpacks: dedicated BP/RP, unique item-bound 27-slot storage, slot UI, metadata roundtrip validation, concurrent-session lock and old player-storage migration. Container and special NBT formats are rejected when fidelity cannot be guaranteed. Not a native Java inventory-screen clone.
- MCA Reborn: persisted player NPC identity, per-player affinities and social cooldowns, marriage and attempted real baby-villager birth (rejects if ageable component does not confirm baby). Java social AI, schedules and deep genealogy remain missing.
- Carry On: actual entity transport and placeable blocks via StructureManager world-save/world-place (including block entity data for supported single blocks). Rejects multiblocks/double chests. Full chest NBT, lag, relog and anti-duplication require on-device testing.
- RFTools: custom generator/cell/cable/lamp blocks; consumption of coal/charcoal, physical cable network (bounded BFS), persistent energy and real lamp lighting. Old lodestone energy model remains reachable. Native energy units are not Forge FE; most original Java machines are absent. Models/skins are temporary vanilla references.
- Origins: ten catalogued choices, original passive effects plus active Enderian teleport, Elytrian impulse, additional water/shulk modifiers and cooldown. Remaining Apoli 61-power parity including true phasing is not implemented.

## Verification and limitations
Six JS sources compiled using JavaScript parser checks. Mocked unit tests and structure/package JSON checks are committed under tests/systems_*.test.mjs and .github/workflows/minizin-systems.yml, but passing CI must be confirmed separately. Minecraft Bedrock Android import, Content Log, performance, multiplayer, v0.2.8 merge, original Java mechanics and source licensing/asset QA have NOT been confirmed. Do not advertise full Java parity.

## Android test checklist
1. Activate/rename two waystone blocks. Test within loaded range, distant 1000+ blocks, cross-dimension, blocked arrival and reopening after relog.
2. Give two backpacks (/give @s minizin:backpack), deposit in each, relog and share between two real players. Try metadata-rich enchanted tools; unsupported item classes must be refused.
3. Carry and place a single chest/barrel with contents by crouching + stick; compare item metadata and inventory across relog. Verify double chests are refused, dropped entities are not cloned.
4. MCA: interact with villager crouch+paper, gift emerald, verify relationships and marriage after relog; check real baby age via component/visual and genealogy.
5. RFTools: place generator, cable, cell and lamp; feed coal, observe changing energy and actual light, disconnect cable and confirm off state.
6. Origins: select via !minizin origins; crouch+feather for Enderian/Elytrian active, verify cooldown, effects, water interactions and any deviations from Java.

## Packaging and redistribution
CI builds Minizin_Systems_Experimental.mcaddon from the three corresponding pack pairs (six embedded packs). This is an EXPERIMENTAL addon and does not contain the larger original assets from the generated-bedrock branch. Confirm redistribution rights before release.
