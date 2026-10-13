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

`tools/package_independent_candidates.py --build-root build/final_20261013_compat` packages twelve individually installable, **experimental** `.mcaddon` files as `Minizin_12_Packs_Independentes_CANDIDATOS.zip`: 2,356,566 bytes, SHA-256 `5a3c7a278f37068906a7e1b4b7daaf1297c2f6cfb6f681a9754b3fd905acae0c`. The independent Sophisticated Backpacks pack uses its item-bound runtime, filter upgrade and original-source inventory icon. Each archive passed ZIP integrity and its source BP/RP passed structural validation. These independent builds have different feature coverage from the combined pack; test one at a time in a fresh world. No standalone Android installation was verified and independent packs are not claimed to coexist with the integrated pack.

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

## Continuation: dragon armor candidate v0.3.5

The user will perform the Minecraft Android validation. The combined source now binds the 32 Ice and Fire armor pieces to four persistent dragon slots. Its client entity has synchronized ordinal properties for head, neck, body and tail, and the render controller selects the corresponding original 512×256 transparent texture layers from the pinned Java source. The material ordinals follow `ItemDragonArmor.DragonArmorType` (iron, gold, diamond, silver, dragonsteel fire, dragonsteel ice, copper, dragonsteel lightning). Armor rating is recalculated from the occupied slots and applied through `minecraft:armor` component groups. In Survival, swapping a piece in the same slot returns the old piece to the selected inventory slot. The old v0.3.3 creature aliases remain available, but this new rendering path belongs to the current `minizin_iceandfire:*dragon` identifiers.

The private v0.3.5 retest archive is `build/final_20261013_v035/Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v035.mcaddon` (4,590,666 bytes; SHA-256 `6aed0bb7c8df29300c78d90b22ea75eb812b8c0833b7c41076af4b15f3954902`). The independent candidates archive is `Minizin_12_Packs_Independentes_CANDIDATOS.zip` in the same directory (3,010,603 bytes; SHA-256 `adb686de4f85b151e49dc66ffb6f16da9de3affd498f16bb4d319b1e8a48cee4`). The integrated archive retains all identifiers from the supplied v0.3.3 and has 49 entities, 399 blocks, 50 scripts and 67 animation definitions. Offline checks passed: 36 Python project tests, 28 world tests, 18 Node test files, and nested archive integrity. The armor integration test checks original PNG dimensions and BP/RP links for three dragons. These results do **not** establish that Bedrock Android renders `entity_multitexture` with four overlays correctly, that armor protects in combat, or that inventory/armor survives a relog. Those are the exact physical checks to perform next.

This remains an experimental candidate. The known Java feature gaps in the scope matrix above still apply, especially natural cave biome generation, the full boss and creature rosters, Java GUI parity, and machine coverage. A successful offline build is not a claim that all 12 mods are complete.

## Continuação: reconstrução privada v0.3.7

Branch exclusiva `work/minizin-final-20261013`, PR #7 em rascunho. O build reutiliza os submódulos fixados, `generated/` e o binário v0.3.3 enviado pelo usuário (SHA-256 `0c4ed7e822763037e01e156ea34c848bd2f9eb3a2f777589628ba70d5eaa0ce4`). O relatório `build/final_20261013_recovered_b/BUILD_REPORT.json` registra os commits das fontes. Branches de outros agentes não foram alteradas.

O código final deste ciclo está no commit remoto `2f3c3df82e2ad417fb2dad8170cc17989a06d6fc` (árvore `613b2374f6cc97f4dc0937169c840f1bfb0f0c44`). O campo `source_commit` do relatório de build foi capturado antes do commit final de testes/documentação e da correção do JSON da expansão; o build usou essa correção já presente na árvore de trabalho. O JSON resultante e a árvore final foram verificados após o empacotamento.

O gerador dos quatro sistemas agora usa os scripts mantidos de Carry On e RFTools, em vez dos protótipos antigos do snapshot. O Carry On bloqueia a colocação se o chunk original não estiver carregado e oferece `!carryon recuperar` para cargas incertas. Os oito slots persistentes do Aether incluem dois anéis e dois espaços de acessórios/relíquias; dados corrompidos são retidos, e encantamentos dos acessórios passam por ida e volta. A mochila individual mantém 27 espaços de base e oferece duas expansões fabricáveis, para 54 e 81, com páginas, depósito e organização. O ícone do filtro usa `filter_upgrade.png` e a expansão adaptada usa `upgrade_base.png` da fonte Java fixada. Esta expansão de espaços é uma adaptação Bedrock, sem equivalência comprovada aos upgrades de pilha do Java.

Arquivos reconstruídos e preservados para teste privado:

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v037.mcaddon` | 4.597.619 | `a6b0ca8c535cb7bf12a273cd303de084d55bac97dbd40c0e162cb10e0223e3f2` |
| `Minizin_12_Packs_Independentes_CANDIDATOS.zip` | 3.019.072 | `16cf1a474f2820fc6850b43933688e3c57b5ff139da440a39c92f8a243b1a07f` |

Verificação local executada: 36 testes Python do projeto, 28 testes de mundos e 18 arquivos de testes Node; validação estrutural do integrado (49 entidades, 399 blocos, 50 scripts, 67 definições de animação e oito referências de áudio), referências BP/RP, manifestos, JSON e integridade ZIP aninhada no empacotador. O BP integrado contém 900 definições de itens e 69 biomas; contagem de arquivos não comprova sua geração ou comportamento no jogo. O usuário fará o teste Android, ainda pendente. Verificar importação, Content Log, ícones, armaduras equipadas, animações, portal/retorno, biomas em mundo novo, persistência da mochila após reinício, Carry On entre chunks, FPS e memória. Permanecem incompletos os catálogos completos de mobs, máquinas, upgrades, poderes, arenas e sistemas originais Java descritos na matriz anterior. Não declarar os 12 mods concluídos nem publicar a arte de terceiros sem confirmar o direito de redistribuição.
