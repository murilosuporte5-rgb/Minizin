# Minizin — Work checkpoint, 2026-10-13

## Base and evidence

- Work branch: `work/minizin-final-20261013`, based on PR #6 head `04020062f2b42ed378185084c143b5c1d4f8c2a5`. PRs #2–#5 remain open; none was modified. `main` was at `e3eec9adff5c5f85721fa6c92201dd37a8452ecc` when auditing.
- User supplied v0.3.0 SHA-256 `3d54880c63cafa980abb697ff296e0fb623949dd3443d60bd1149fe1282f3360` and v0.3.3 SHA-256 `0c4ed7e822763037e01e156ea34c848bd2f9eb3a2f777589628ba70d5eaa0ce4`. Both nested archives passed ZIP integrity checks.
- The v0.3.3 upload had 764 item IDs, 372 block IDs, 25 entity IDs and 69 biome IDs. It added scrolls and a blue portal texture over v0.3.0, but its Aether script deliberately disabled wildlife and boss spawning because the corresponding assets were absent in that build. Version numbers alone did not identify the most complete implementation.
- The source rebuilt candidate incorporates the pinned Java submodules, the converted `generated/` resources, Waystones, six staged mod families, the four gameplay systems, the source Aether and BOP world packs, and the item-bound Sophisticated Backpacks runtime. Its compatibility pass retains **every** item, block, entity and biome ID from the attached v0.3.3. The six restored creature aliases have their former runtime; the four legacy RFTools blocks retain the physical grid runtime alongside newer tiered machines.

## Concrete corrections

1. Aether exploration used to generate adjacent cells and put a return portal in *each* cell. `generateCell` now builds terrain without an exit frame; `visitAether` creates and persists one frame only for the destination linked by an actual incoming player portal. Existing frames in saved worlds are not removed automatically.
2. The combination procedure left Waystones out before a repair stage that expected it. The new builder includes its independent pack and keeps the placed block item instead of creating a duplicate item ID.
3. World overlays previously copied script files without importing them. They now wire the Aether and BOP entrypoints, retain Freezer/Incubator imports, and set the Aether beta Script API dependency. Atlas icon keys are rewritten with their item definitions.
4. The BOP/Aether catalog had overlapping block IDs after overlay. Existing entries are retained and overlaps reported (`74` Aether, `262` BOP); newly supported world elements are added without duplicate identifiers.
5. The earlier combined build installed a 91-line shared backpack implementation even though the independent systems pack had a 340-line per-item version with filter, sort and deposit. The new builder uses that source and includes its filter upgrade item and recipe.
6. Repairing only before the Aether world overlay left some original recipes unresolved. Repairing again after the overlay registered `110` Aether recipe definitions (including 22 stonecutting, 9 smelting and 9 blasting); the earlier intermediate produced `92`.
7. The `v0.3.3` compatibility overlay restored five missing creature item IDs, four RFTools block IDs, six creature entity IDs and `minizin:aether_highlands`; the backpack upgrade is now generated directly from source. Legacy item aliases use original-source icons already present in the integrated pack, instead of vanilla placeholders.

## Candidate and tests

The private Android retest candidate is `Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v0.3.4.mcaddon` under `build/final_20261013_compat/`.

| Evidence | Result |
|---|---:|
| Archive bytes | 3,936,996 |
| SHA-256 | `febf243facbcf7dcaf00159ea80738e0968067f029b405d9a988ff985df911d8` |
| Structural counts | 49 entities, 399 blocks, 49 scripts, 67 animations, 8 sound definitions |
| Item and biome definitions | 899 items, 69 biomes (68 BOP plus legacy Aether Highlands) |
| Unit tests | 35 Python project tests; 28 world builder tests; 17 Node test files, all passing |
| Pack checks | Both nested ZIPs, manifests, BP/RP dependency, unique item/block/entity/biome/recipe IDs, icons, PNG paths, geometry, imports and audio references passed local checks |
| Android in-game test | **Not run**; loading, visual fidelity, generation, control, FPS, memory, relog and multiplayer remain unverified |

The input archives, converted art and binary candidate stay under ignored `build/` or the user's private file space; they are not committed to the public PR. The candidate uses Bedrock beta Script API for the Aether custom dimension. Java license/redistribution scopes remain to be checked before a public release. Minecraft Android 1.21.120+ with the required experiments is the manifest minimum; the exact client compatibility has not been verified.

## Scope matrix

“Verified” in this table means offline structure or scripted tests, **not** in-game Java equivalence. An exhaustive denominator of Java features for each pinned source has not been established, so no completion percentage is assigned.

| Mod | Source-backed content carried into candidate | Offline verification | Material gaps / Android checks |
|---|---|---|---|
| The Aether | Experimental sky dimension, glowstone/water portal, 46 world blocks plus catalog, 21 entities, 21 converted structures, 40 converted loot tables, bosses/fauna, Freezer, Incubator, accessories and recipes | World builder tests, script syntax, cross-pack references, portal-link regression | Java noise/worldgen, boss timing and UV/animations not equivalent; only linked cells receive new exits; verify portal blue surface, dungeon spawn, return and persistence on device |
| Biomes O’ Plenty | 68 source definitions, 61 Overworld replacements, 5 Nether replacements, 2 cave IDs without surface replacement; blocks/vegetation | JSON/atlas and classification checks | Definitions do not prove appearance; cave generation and Java biome router are not reproduced; find and log actual biomes in a new Android world |
| Ice and Fire | Three dragon species, eggs, controls, elemental attack logic and 32 material/part armor items; six legacy creature IDs retained across mod families | Script tests, unique IDs, original icon references | Equipped 3D armor, flight touch controls, stage visuals, AI and persistence untested on device |
| Alex’s Caves | Atlatitan, source rig/texture and limited behavior/items | Entity and references checked | Cave environments, remaining fauna, machines and animations are incomplete |
| Mowzie’s Mobs | Bluff and Umvuthi/Umvuthana adapters with converted resources | Attack/script tests and references | Boss roster, animation sync and phase fidelity incomplete |
| L_Ender’s Cataclysm | Ignis, Ender Guardian and Harbinger adapters, phase/attack code and converted resources | Script tests and references | Arenas, other bosses, gear and exact attack choreography incomplete |
| Waystones | Placeable block, discovery/naming, distant travel guard, four scroll types, Warp Stone, migration path | Runtime tests, item/atlas/geometry checks | Visual block and loaded-chunk arrival need Android verification |
| MCA Reborn | Ten NPCs, source skins, relationships, marriage/family and profession identifiers | Runtime and data tests | Full routines, genetics, professions/wardrobe and visual parity incomplete |
| Carry On | Real entity/block transfer with bounded structure storage and protections | State/blacklist tests | Third-person held rendering and inventory state across relog/chunk unloading need device tests |
| RFTools | Four legacy grid blocks and v2 state plus newer generator, cables, cells, tiers, lamp and recipes | Runtime tests and both ID families checked | Forge FE interop does not exist; advanced machines/UI and real energy persistence need testing |
| Origins | Selection, persistent adapted powers and Shulker 9-slot inventory | Runtime/round-trip tests | Full Java power catalog and native inventory UI unavailable in current implementation |
| Sophisticated Backpacks | Per-item ID, 27 slots, filter upgrade, sort and deposit from systems source | Unit tests and item/recipe checks | Native Java GUI, all upgrade tiers, equipped 3D visuals and crash/relog safety on Android unverified |

## Standalone packs and extra renderers

Local builders also produced independent staged worlds, creatures, Waystones and four gameplay packs. These builds have separate UUIDs and retain the limitations in their own reports; the combined addon is the only deliverable checked for the complete 12-mod coexistence graph here. Sophisticated Backpacks has standalone BP/RP source, but this checkpoint does not claim a verified standalone Android installation.

Immersive Portals, Xaero's Minimap and Distant Horizons were not added to the candidate. Existing source audits contain waypoint and offline LOD data, not a proved live portal camera, minimap renderer or distant chunk renderer on Android.

## Rebuild and next gate

With submodules initialized, `generated/` from `origin/generated-bedrock`, Pillow and `nbtlib` installed, and the Sophisticated Backpacks source available at the pinned checkout, run:

```bash
python tools/build_final_candidate.py --output build/new_retest \
  --previous-addon /absolute/path/to/Minizin_Integrado_v0.3.3_Codex_Sistemas_12MODS_ANDROID_TESTE.mcaddon
python -m unittest discover -s tests -q
python -m unittest discover -s bedrock/worlds/tests -q
node --test tests/*.test.mjs
```

The build records pinned submodule revisions and SHA-256 in `BUILD_REPORT.json`. For the Android gate, install into a *copy* of a world, enable both packs and required experiments, record exact Bedrock version and Content Log, then test Waystones, portal returns, BOP biome discovery, dragon armor equipped, backpack filter/relog, RFTools legacy and new grids, boss rendering, touch controls, FPS and memory at 5/15/30 minutes. Record screenshots and logs against this archive's SHA before marking any visual defect fixed.

No release or merge is justified by these offline tests alone. Source licenses and any permission to publish original/derived art must be reviewed per mod before placing the binary on a public GitHub release.
