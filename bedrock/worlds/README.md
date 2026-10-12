# Minizin Worlds — The Aether + Biomes O' Plenty

**Branch exclusiva:** `feature/minizin-worlds`. **Alvo experimental:** packs com versionamento `0.2.8`. A branch Git `main` usada como base não registra uma release ou tag verificável `v0.2.8`; o versionamento dos packs **não prova** correspondência binária com uma v0.2.8 externa.

Este diretório tem código e testes próprios. Não modifica os módulos de outros chats, `generated/`, manifests compartilhados nem submódulos Java. Compila dois add-ons **independentes**.

## Proveniência auditada

| Módulo | Fonte Java como submódulo no Minizin | Classes / dados relevantes | Recursos locais aproveitados |
| --- | --- | --- | --- |
| The Aether | `mods/41-the-aether/upstream` gitlink `e07d30e16fbd0f09cc067b39594035e395dcf996` | `src/generated/resources/data/aether/worldgen/`, `src/main/resources/data/aether/structure/`; lógica original não executável no Android | 11 definições de bloco, com 13 texturas de origem distintas (holystone, skyroot, golden oak, minerais, portal e faces); texturas copiadas **somente em build/** |
| Biomes O' Plenty | `mods/19-biomes-o-plenty/upstream` gitlink `ef7f13e117faef0b97591f569175e53ea4fe664b` | `common/src/generated/resources/data/biomesoplenty/worldgen/biome/*.json` | 8 definições de bloco, com 11 texturas de origem distintas (incluindo faces superiores de troncos); para quatro biomas **temperatura, chuva, água, cor da folhagem e grama lidas do JSON Java fixado**, quando disponíveis |

**Licenças:** Aether `LICENSE-ASSETS.txt` e Biomes O' Plenty `LICENSE` indicam **ALL RIGHTS RESERVED** para recursos. Código disponível publicamente ou autorização de estudar **não autoriza automaticamente redistribuir os PNGs**. O Git armazena somente código que consome os arquivos originais; todos os PNG, pacotes finais e derivados permanecem em `build/` (gitignored) até registrar autorização expressa de adaptação/redistribuição. **Não publique os .mcaddon gerados na CI nem em releases públicas sem tal autorização.**

## Funcionalidade implementada em código

### The Aether

- Registra `minizin_aether:sky` por `dimensionRegistry.registerCustomDimension` durante `system.beforeEvents.startup`; dimensão do tipo **void**, sem gerador do Java.
- Portal vertical 4x5 em glowstone, interior 2x3, ativado por interação com balde de água na moldura; bloqueio de colisão do portal; eixo X ou Z.
- Teleporte de entrada e retorno Overworld, com registro de posição anterior por jogador, cooldown de 100 ticks e plataforma segura em `(0, 0)`.
- Ilhas determinísticas em células de 80 blocos: holystone, grama/dirt do Aether, minério de ambrosium/zanite. Árvores skyroot e golden oak, templos/masmorras simples com baú sem tabela de loot original.
- Gerador sob demanda, um job por vez, fila limitada, `tickingAreaManager` para preloading, limites cooperativos por tick. Progresso do mundo marcado apenas após terminar cada célula.

### Biomes O' Plenty

- Blocos com as texturas originais: lavender, glowflower, magic/redwood/umbran wood e leaves.
- Quatro perfis: `lavender_field`, `mystic_grove`, `redwood_forest`, `ominous_woods` com documentos Bedrock de biome/client biome e feature rules para árvores e flores.
- **Adaptação executável em mundos atuais:** `bop/main.js` distribui árvores e plantas em regiões determinísticas de 48 blocos, sobre solo natural carregado no Overworld. É um **overlay**: não troca os IDs dos biomas vanilla, não modifica seu ruído, não implementa o biome router do Java. Mantém regiões processadas em propriedades dinâmicas e não regenera após reconectar. O recorte do recurso é intencional e compatível com a separação dos packs.

## Build e validação (local ou CI)

```sh
git switch feature/minizin-worlds
git submodule update --init mods/19-biomes-o-plenty/upstream mods/41-the-aether/upstream
python -m pip install Pillow
node --check bedrock/worlds/aether/main.js
node --check bedrock/worlds/bop/main.js
python -m unittest discover -s bedrock/worlds/tests -v
python bedrock/worlds/build_worlds.py --mod both
```

Saídas locais:
- `build/worlds/Minizin_Worlds_aether_v0.2.8.mcaddon`
- `build/worlds/Minizin_Worlds_bop_v0.2.8.mcaddon`

A workflow isolada `.github/workflows/minizin-worlds-validation.yml` testa sintaxe, construção, manifests, dados vinculados e estrutura ZIP. **Passar CI não equivale a testar em Minecraft Android.** Os testes do Python cobrem funções puras e validação estática.

## Teste em Minecraft Bedrock Android — pendente até execução no aparelho

Criar **cópia de um mundo** antes de instalar. Importar cada pack individualmente (RP + BP) e conferir o Content Log. Para Aether habilitar **Beta APIs/experimentos** compatíveis com a versão real instalada; a API de dimensões ainda é experimental. Criar portal glowstone com 4 de largura e 5 de altura e usar balde de água sobre a moldura; pisar na superfície interior, verificar ida/volta, ilha inicial, árvores, marcação persistente e ausência de travamentos. No BoP, percorrer áreas **novas** do Overworld para que árvores e flores surjam nas regiões processadas; verificar suas texturas, desempenho e construção não destrutiva. Capturar FPS, memória, posição, logs, a versão exata do jogo e se features precisam de flags extras.

**Testes não realizados nesta sessão:** compilação/execução contra o runtime Minecraft Android, performance/latência/RAM/FPS, colisões com outros add-ons, multiplayer, persistência em versões diferentes, reentrada em dimensões, portal sob lag e geometrias no renderizador. Não há declaração de funcionamento comprovado no cliente, nem equivalência ao Java.

## Limitações do engine e lacunas reais

1. A API `dimensionRegistry` gera dimensão **vazia**. Scripts devem colocar ilhas, árvores e estruturas manualmente, limitados por chunks carregados, quotas de ticking areas, memória e ticks. Java custom dimension noise settings, arquivos NBT de estruturas, dungeon loot/progressão original, biomas sky e mobs do Aether **não** foram portados.
2. `minecraft:overworld_generation_rules` é **legado e não atribui naturalmente novos biomas personalizados** no roteador atual (Caves & Cliffs); os quatro JSONs de bioma são dados para testes/integrações futuras, enquanto o gerador de regiões do BoP implementa apenas decoração no Overworld. No Java, temperatura/chuva, vegetal, clima, vegetação e noise router envolvem registros distintos; conversão do JSON não reproduz biomas reais.
3. Os modelos de `generated/conversions/block_atlases` estão em branch separada e não foram mesclados para evitar conflitos e redistribuição indevida. O builder usa **PNGs originais**, mas a geometria de portal/plantas é **adaptação** Bedrock, não modelo idêntico ao Java.
4. Sem equipamento Android conectado, a adequação dos componentes dos JSONs e APIs Beta é **hipótese técnica** até teste do jogo. Erros no content log devem ser reportados e corrigidos com a versão exata do Minecraft.
5. Troncos e aether grass têm texturas superiores/inferiores originais com materiais direcionais; resta verificar orientação e UV dentro do Minecraft. O portal animado Java é atualmente um único frame, sem animação. Estrutura simples de templo não equivale às masmorras Bronze/Silver/Gold.

## Referências

- Fontes originais fixadas nos gitlinks citados acima.
- [Minecraft: Custom Dimension API](https://learn.microsoft.com/en-us/minecraft/creator/documents/scripting/custom-dimension-api-tutorial).
- [Minecraft: Custom Biome Tutorial](https://learn.microsoft.com/en-us/minecraft/creator/documents/biomes/custombiometutorial).
- [Minecraft: Overworld Generation Rules (legado para custom biomes)](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/biomesreference/examples/components/minecraftbiomes_overworld_generation_rules).
- [Minecraft: Tree Feature](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/featuresreference/examples/features/minecraft_tree_feature).
