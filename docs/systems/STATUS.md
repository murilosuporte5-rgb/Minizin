# Minizin — Systems workstream (2026-10-12)

Branch: `feature/minizin-systems` • PR: https://github.com/murilosuporte5-rgb/Minizin/pull/5

## Source and baseline

The current `main` repository has independently versioned experimental packs
(manifest 0.1.0); it does **not** contain a source snapshot independently
identified as the user's Minizin v0.2.8. This PR therefore does **not**
claim integration or testing against that unprovided composite package.
The work only changes owned pack paths, tests, CI and this document;
it does not modify other workstream branches, shared script loaders or assets.

## Functional implementation

| System | Implemented in Bedrock | Known gap versus Java |
| --- | --- | --- |
| Waystones | Custom placeable block with reused original-source converted geometry/UV atlas; server-authoritative activation and persistent discoveries, rename, legacy marker migration, teleport between dimensions, unloaded-chunk exception handling, post-arrival check and rollback | Distant travel still depends on the engine loading destination chunks; neither source-correct costs nor all Waystone variants or Java teleport reliability proven |
| The Aether | Original item icons for the Aether accessory families, 32 catalogued accessories, Java-shaped virtual slots (2 rings plus pendant/gloves/cape/shield/accessory slots), persistent state and offhand migration from the old prototype | Bedrock cannot add a native inventory tab through the public API; accessory 3D renderers, full passive abilities, complete recipes/AI and Android QA remain pending |
| MCA Reborn | Ten actual summonable NPC types with original layered skins, simplified humanoid geometry and new Molang walk animation; per-player affinity, social cooldown, marriage, divorce, persistent family identities, seven Java-sourced profession identities, and adapted guard/archer combat | Not the full Java NPC AI, trades, profession clothing, family tree UI or schedules; Bedrock birth event/render state requires Android QA |
| Carry On | Move original entities without despawn/copy, pickup/place actual supported blocks with saved World-mode structures, carry persistent between world loads, refuse adjacent chests, use Java-derived blacklist boundaries, and block duplication after uncertain writes | No held-block animated 3D rendering; liquid/special block states and complete cross-mod entity coverage still require Android QA. Ambiguous placement deliberately locks cargo for inspection/recovery |
| RFTools | Real custom generator, persistent energy, adjacent network transfer, original converted Machine Frame, normal/simple/advanced/creative Power Cell tiers, coal fuel, recipes derived from pinned Java JSON and lamp consumer | Internal Minizin energy units are not Forge FE; the indicator-based lamp is a custom consumer, not an exact original Java device; GUI containers, factories, dimensions and long-distance Power Cell behavior absent |
| Origins | All ten origin selectors persisted, active Elytrian boost and Enderian teleport, Arachnid actual cobweb placement plus crouch-wall climb impulse, Phantom temporary/crouch invisibility, Feline fall cancellation and sprint jump, Blazeborn fire immunity/burning wrath/water vulnerability, Merling breathing/vision/swim speed, Avian slow falling, Shulk resistance/haste | 61 Java/Apoli powers are NOT completely ported. Phantom does not phase through blocks, Shulk native extra inventory unavailable, Elytrian has no automatic Java elytra component. Effects are still incomplete and need Android QA |
| Sophisticated Backpacks | Independent 27-slot item-identity storage, checked metadata transfer, per-item persistence and per-session locks, legacy migration, atomic whole-stack bulk deposit, sorting and a real craftable filtering upgrade | No larger tiers, original Java 2D inventory/container screen, worn 3D backpack or all Sophisticated upgrades. Unsupported metadata-bearing items are rejected. Duplicated item identity/security requires multiplayer testing |

## Survival crafting

The Waystone block, four RFTools power blocks and base backpack are craftable
from vanilla ingredients. The backpack-filter upgrade is craftable and can be
installed in one physical bag; it restricts the bag's bulk-deposit operation
to chosen item identifiers. These recipes use original gameplay intent, not
verified 1:1 Java crafting grids.

## Art and rights

- MCA and RFTools geometry / PNG were reused from the repository's
  `generated-bedrock` branch, not reconstructed from scratch.
- MCA model is a simplified Bedrock humanoid. The Molang animation here is
  an adaptation, not a Java animation binary.
- RFTools lamp uses the original converted power-relay visual; it is not
  represented as the original Java lamp model.
- No modern Sophisticated Backpacks art/source was copied: the current
  project lists **All Rights Reserved**, as shown at
  https://github.com/P3pp3rF1y/SophisticatedBackpacks .
- Audit redistribution compliance and preserve required license/credit
  materials for MCA (GPL-3.0) and RFTools (MIT) before any public release.

## Automated checks

`Minizin Systems QA` workflow:
1. `node --check` for all six relevant script modules.
2. `node --test tests/systems_*.test.mjs`: mocked unit and regression tests.
3. `python tests/systems_pack_integrity.py`: BP/RP dependency UUIDs, resolved geometry IDs, PNG atlases, all ten NPC client/server skins and animations.
4. JSON parsing and archive integrity; upload a standalone
   `Minizin_Systems_Experimental.mcaddon` as a GitHub Actions artifact.

CI passing confirms structural integrity **only**. No actual Bedrock engine
has been run in GitHub Actions; FPS/RAM, Script API runtime behavior and
Android touch controls cannot be certified by these tests.

## Android acceptance steps (in a backed-up test world)

1. Minecraft Bedrock supporting Script API 2.0.0; import experimental addon,
   activate all six BP/RP packs and inspect the Content Log.
2. Craft two Waystones, activate, rename, verify persistence, run distant
   1000+ block and cross-dimension teleport tests, including obstructed
   landing and unloaded chunks.
3. Craft two backpacks and one filter upgrade. Transfer enchanted/damaged
   items, install filter, bulk deposit, sort, share each bag across players,
   then relog and reopen. Different backpack IDs must remain isolated.
4. Pick up a full chest, place it, relog and verify every slot is identical.
   Reproduce interrupted placement under test, refuse adjacent double chests.
   An uncertain cargo must not be silently recreated.
5. Craft generator, cable, cell and lamp. Feed coal, check transfers and light
   state, break a cable, relog and verify stored energy remains.
6. Use crouch + paper with generated MCA NPCs, test personal affinity,
   wedding/divorce, family identity and a real baby that grows up.
7. Use the Origins UI, test cooldowns, cobweb cleanup, fall damage
   cancellation, Phantom visibility and explicit absence of native phasing.

**Release gate:** do not mark Java parity or v0.2.8 integration complete
until those in-game tests, source-rights review and integration are proven.
