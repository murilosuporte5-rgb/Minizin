# Minizin — matriz de paridade visual e funcional dos itens

Atualização: 2026-10-13. As referências visuais são as galerias e links preservados em `origin/main:docs/visual-references/README.md`; imagens externas não são autorização de redistribuição. “Implementado” abaixo significa presença de asset/código verificável, não teste no cliente Android.

| Mod | Java ID / versão | Referência visual | Bedrock ID | Inventário | Mão/equipado | Receita | Mecânica | Teste Android | Estado |
|---|---|---|---|---|---|---|---|---|---|
| The Aether | `aether:*`, 1.21.1 pinado | Ilhas, portal, anéis e acessórios | `minizin_aether:*` | Ícones source-backed; 32 acessórios | Slots virtuais `!aether slots`; sem renderer 3D nativo | Receitas/Freezer/Altar catalogados | Efeitos principais, Zanite e desgaste de luvas adaptados | Não testado | Parcialmente implementado |
| Biomes O’ Plenty | `biomesoplenty:*` pinado | Redwood, vegetação e biomas | `minizin_bop:*` | Blocos e ícones atlas | Colocação disponível; worldgen não 1:1 | Catálogo de blocos | Overlay determinístico/native biome adaptado | Não testado | Parcialmente implementado |
| Ice and Fire | `iceandfire:*` pinado | Dragões, ovos e armaduras | `minizin_iceandfire:*` | Itens e ovos com ícones originais | Armadura em quatro camadas; voo adaptado | Receitas parciais | Domesticação, incubação, crescimento e ataques adaptados | Não testado | Parcialmente implementado |
| Alex’s Caves | `alexscaves:*` pinado | Cavernas, Atlatitan e itens | `minizin_alexscaves:*` | Atlatitan/item catalogado | Modelo source-backed | Parcial | IA e cavernas completas ausentes | Não testado | Parcialmente implementado |
| Mowzie’s Mobs | `mowziesmobs:*` pinado | Wroughtnaut, Umvuthi e Bluff | `minizin_mowzies:*` | Bosses source-backed | Geometrias/texturas/animations source-backed | Parcial | IA/partículas e catálogo completo incompletos | Não testado | Parcialmente implementado |
| Cataclysm | `cataclysm:*` pinado | Ignis, Harbinger e Ender Guardian | `minizin_cataclysm:*` | Spawn eggs/assets presentes | Modelos convertidos; camadas limitadas | Parcial | Ataques/fases adaptados; arenas/loot incompletos | Não testado | Parcialmente implementado |
| Waystones | `waystones:*` pinado | Bloco e menu de destinos | `minizin:andesite_waystone_block` | Ícone e block placer | Bloco real source-backed; entidade só migração legada | Scrolls e bloco | Persistência/teleporte seguro adaptados | Não testado | Implementado, mas não testado no jogo |
| MCA Reborn | `mca:*` pinado | NPCs, skins e anéis sociais | `minizin_mca:*` | Itens sociais parciais | Skin em camadas; UI simplificada | Parcial | Relações/família/profissões adaptadas | Não testado | Parcialmente implementado |
| Carry On | `carryon:*` pinado | Bloco/baú carregado em terceira pessoa | `minizin_carryon:*` | Item/estado persistente | Sem renderer 3D Java 1:1 | Parcial | Transferência real com limites | Não testado | Parcialmente implementado |
| RFTools | `rftools:*` pinado | Máquinas, cabos e GUI | `minizin_rftools:*` | Ícones/modelos convertidos | Máquinas e cabos colocáveis | Receitas parciais | Energia persistente adaptada; GUI/fábricas ausentes | Não testado | Parcialmente implementado |
| Origins | `origins:*`, poderes Apoli pinados | Orb, seleção e ícones | `minizin_origins:*` | Ícones e menu | UI server-side | Orb/itens parciais | 10 origens e poderes principais; catálogo 61 incompleto | Não testado | Parcialmente implementado |
| Sophisticated Backpacks | `sophisticatedbackpacks:*` | Mochila, grid e upgrades | `minizin_backpacks:*` | Item individual persistente | Sem modelo equipado/UI Java | Crafting/filter parcial | 27 slots, sort, bulk deposit e migração | Não testado | Parcialmente implementado |

## Evidência e limites

- Os testes atuais comprovam estrutura, referências, persistência simulada e sintaxe; não comprovam renderização, toque, FPS, memória, multiplayer ou carregamento no Android.
- `origin/main:docs/visual-references/README.md` foi consultado para a lista de referências. O arquivo não está presente como caminho de trabalho nesta branch; a comparação imagem-a-imagem permanece pendente.
- Immersive Portals e Xaero’s Minimap permanecem excluídos conforme a especificação; Distant Horizons só deve ser incluído se houver LOD real, não um placeholder.
