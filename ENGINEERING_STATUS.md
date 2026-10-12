# Estado técnico verificado — Minizin

Revisão: 2026-10-12. Este documento distingue **código-fonte estudado**, **geometria convertida**, **build validado** e **teste no Minecraft Android**.

## Engenharia reversa e conversão já executadas

| Família / projeto | Evidência | Resultado | Limitação |
|---|---|---|---|
| Waystones | [Java block atlas job](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202663686) | 17/21 modelos JSON de bloco convertidos com atlas de textura | Sem validar orientação, visual e jogo |
| Biomes O' Plenty | [Java block atlas job](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202663686) | 275/1133 modelos de bloco convertidos com atlas | 858 formatos não suportados; geração de biomas ainda não portada |
| The Aether | [Java block atlas job](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202663686) | 74/202 modelos de bloco convertidos com atlas | 128 modelos não convertidos; dimensão ainda não portada |
| Ice and Fire | [Tabula batch job](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202331340) | 192/192 modelos/poses Tabula convertidos como geometrias individuais | Poses não são clips de animação; IA, movimento e rig QA pendentes |
| Ice and Fire | [Fire dragon converter](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202119655) | Fire Dragon Base Male: 104 bones, 92 cuboids, 256×128 atlas | Ainda não verificado visualmente dentro do jogo |
| Alex's Caves | [Atlatitan extractor](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202266122) | Atlatitan: 32 bones, 50 cuboids a partir do modelo base e subclasse, 512×512 | 13 avisos técnicos, sem animação, rig/faces requerem QA |
| Mowzie's Mobs | [Prototype build](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38201840416) | Bluff com geometria e textura originais, idle adaptada e BP simples | IA/ataques originais não portados |
| Waystones | [Prototype build](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38201840416) | Protótipo de ativação e teleporte, textura e modelo original convertido | Não é a réplica funcional integral, nem testado no Android |

**Nota:** total de conversões geométricas de famílias distintas: **366 modelos de bloco (17+275+74), 192 modelos/poses Tabula, Atlatitan e Bluff**. Essas contagens NÃO representam 560 entidades jogáveis ou 14 mods portados. Os artefatos do GitHub Actions contêm os arquivos gerados e relatórios; estão sujeitos a retenção.

## Inventário dos 14 mods — estado real

| Mod | Inspeção de fonte | Conversão em código | Comportamento Bedrock |
|---|---|---|---|
| 15 Waystones | Sim | 17 block models; protótipo BP/RP | Protótipo parcial |
| 16 Ice and Fire | Sim | 192 geometrias Tabula | Pendente |
| 19 Biomes O' Plenty | Sim | 275 modelos de bloco | Pendente |
| 33 MCA Reborn | Árvore/recursos analisados | Pendente | Pendente |
| 34 Carry On | Árvore/código analisados | Pendente | Pendente |
| 41 The Aether | Sim | 74 modelos de bloco | Pendente |
| 42 Alex's Caves | Sim | Atlatitan 32 bones / 50 cuboids | Pendente |
| 43 Cataclysm | Fonte oficial GitHub confirmada | 41/70 modelos Java convertidos | IA/animações pendentes |
| 44 Mowzie's Mobs | Sim | Bluff geo + idle | Protótipo parcial |
| 53 Immersive Portals | Código do renderizador estudado superficialmente | Não convertível via add-on comum | Não suportado integralmente |
| 54 RFTools | Fontes/OBJ/Blend identificados | Pendente | Pendente |
| 55 Origins | Fontes de powers/UI identificadas | Pendente | Pendente |
| 57 Xaero's Minimap | Gramática de waypoints verificada | Importador somente leitura com testes aprovados | Sem minimapa nativo |
| 58 Distant Horizons | Árvore GitLab auditada (534 arquivos) | Pirâmide de dados LOD offline | Sem render nativo Bedrock |

## Recuperar resultados

- **Dois packs .mcaddon (Waystones/Mowzie):** [GitHub Actions — Bedrock prototypes](https://github.com/murilosuporte5-rgb/Minizin/actions/workflows/bedrock-prototypes.yml).
- **Geometrias e atlases de Waystones/BOP/Aether:** [GitHub Actions — Atlas converter](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202663686).
- **192 Tabula de Ice and Fire:** [GitHub Actions — Dragon batch](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202331340).
- **Atlatitan:** [GitHub Actions — Alex's Caves](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202266122).

Os resultados de CI aprovados verificam **estrutura, scripts e geração dos pacotes**. Nenhum pacote foi executado ou benchmarkado no Minecraft Android nesta sessão.

## Continuar sem refazer modelagem

1. Criar **testes visuais reais** dos 2 protótipos BP/RP e registrar erros de conteúdo.
2. Importar as geometrias Tabula/Alex's Caves para Blockbench, conferir pivôs, rotação, texel UV, textura, modelos grandes e sprites finos.
3. Animar e portar IA/efeitos de Ice and Fire, Alex's Caves e Mowzie; montar BP com entidades de produção.
4. Expandir os modelos com parent templates faltantes, crossblock, stairs e textures atlas; só modelar manualmente o que não exista na fonte.
5. Implementar lógica dos outros mods (MCA, Carry On, Origins, RFTools, worldgen, dimensão Aether).
6. Cataclysm fonte pública vinculada; Xaero exige binário autorizado para análise de assets e render. Confirmar os direitos específicos de redistribuição antes de publicar derivados.
7. Não prometer port integral de Immersive Portals, Distant Horizons ou minimapa nativo apenas com resource/behavior packs Bedrock.
8. Benchmark no Android: chunks, FPS, temperatura, memória, multitarefa, salvamento e multiplayer.

## Comandos reproduzíveis

```bash
git clone --recurse-submodules https://github.com/murilosuporte5-rgb/Minizin.git
cd Minizin
python tools/build_bedrock_packs.py waystones
python tools/build_bedrock_packs.py mowzie
node --test tests/java_model_to_bedrock.test.mjs
python -m unittest discover -s tests
python -m pip install Pillow
python tools/block_atlas_to_bedrock.py --root mods/15-waystones/upstream --namespace waystones --output build/atlas/waystones
python tools/tabula_batch_to_bedrock.py mods/16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/models/tabula --output build/tabula_bedrock
```

Não publicar como mod completo até passar a execução dentro do Minecraft Bedrock em dispositivo real.

## Pacote experimental combinado

O job [Minizin-Bedrock-Prototypes](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38202861342) passou e anexou três arquivos `.mcaddon`: `Minizin_waystones.mcaddon`, `Minizin_mowzie.mcaddon` e `Minizin_Combined_Prototype.mcaddon`. O combinado inclui **os dois packs RP/BP existentes**, e **não os 14 mods**. Ainda não testado no Minecraft Android.

## Atualização dos 3 mods faltantes (12/10/2026)

- **Cataclysm:** fonte oficial github.com/lender544/new1.20.1 confirmada; 70 modelos Java, 236 PNG de entidades, 34 arquivos Java de animação, 188 NBT e 232 OGG. CI: https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38234148217 — **41/70 modelos** com geometria recuperada; 29 precisam de parser adicional ou correções. Não é port de IA/animações.
- **Xaero's Minimap:** CI https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38234333289 — importador somente leitura de waypoints para JSON, com preservação de mundo/dimensão; **não desenha minimapa**.
- **Distant Horizons:** CI https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38234659523 — **534 caminhos** da árvore GitLab catalogados e protótipo independente de LOD de alturas com 3 níveis validado; **não reproduz renderização distante**.

Os três trabalhos foram executados e aprovados no GitHub Actions. Nenhum desses três mods foi portado integralmente para Minecraft Bedrock Android nem testado no dispositivo.
