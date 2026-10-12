# Minizin Worlds — The Aether + Biomes O' Plenty

**Branch exclusiva:** `feature/minizin-worlds`. **Alvo experimental:** packs com versionamento `0.2.8`. A branch Git `main` usada como base não registra uma release ou tag verificável `v0.2.8`; o versionamento dos packs **não prova** correspondência binária com uma v0.2.8 externa.

Este diretório tem código e testes próprios. Não modifica os módulos de outros chats, `generated/`, manifests compartilhados nem submódulos Java. Compila dois add-ons **independentes**.

## Estado atual — componentes implementados, não validação de jogo

> Atualizado após a CI de 26 testes. Os trechos de histórico mais abaixo são
> marcos anteriores; **esta seção descreve o escopo de código mais recente**.

| Área | Estado em código / evidência | O que permanece sem comprovação |
| --- | --- | --- |
| The Aether | 46 blocos definidos com PNGs extraídos dos sources pinados; 4 perfis Skyroot, portais e ilhas | render, dimensão Beta e geração em Android |
| Criaturas | 21 registros Bedrock: **16** rigs Java `ModelPart`/herdados convertidos, **3** skins Swet/Sentry sobre a geometria slime vanilla real e **2** Whirlwinds sem geometria estática (colunas de partículas com impulso físico). Phyg/Flying Cow combinam corpo vanilla e asas Java originais | animação original integral, IA/partículas e materiais/UV/collision testados no Android |
| Bosses | Slider (400 HP), Valkyrie Queen (500 HP) e Sun Spirit (500 HP), rotinas distintas de ataque, vulnerabilidade por ferramenta/gelo, lunge/cristal/fogo, spawn e recompensa de progressão vinculados às estruturas | sequências/timing exatos do Java, multiplayer, reentradas e crash-safety |
| Estruturas/loot | 21/21 templates Java NBT exportados, 40 tabelas Java transformadas para JSON Bedrock, com 7/7/9 candidatos representáveis nos pools Bronze/Silver/Gold | loot integral, muitas armas/acessórios ausentes, contents NBT e jigsaw/AI original |
| Biomes O' Plenty | 68 JSON Java representados como bioma Bedrock, **61 substituições parciais no Overworld, 5 no Nether, 2 cavernas sem substituição nativa equivalente**; 20 blocos e catálogo de vegetação baseado nos biomas efetivamente consultados por `getBiome` | biome noise/router Java, all terrain/placed features, geração de cavernas equivalente e validação in-game |

A **dimensão de cada bioma** foi corrigida com base em
`BOPBiomes.java` e `BOPNetherRegionCommon/Rare.java` do commit pinado:
`volcano`, `volcanic_plains` e os biomas com prefixo `end_` aparecem no registro de Overworld; os 5 biomas da região Nether são `crystalline_chasm`, `erupting_inferno`, `undergrowth`, `visceral_heap` e `withered_abyss`. `glowing_grotto` e `spider_nest` são biomas de cavernas que não devem ser inseridos artificialmente na superfície. O Bedrock desde 1.21.110 suporta `minecraft:replace_biomes` no Overworld/Nether; o add-on BOP exige Bedrock >= 1.21.120 e `@minecraft/server` 2.3.0 para a seleção por bioma em runtime. **Substituição parcial não é port integral do worldgen Java**.

Os modelos Java usam animações procedurais `setupAnim` e goals da AI
específicos. O gerador atual recupera rig/cubos, mas os clips de ataque/idle são
**adaptações Bedrock**; não há correspondência integral de keyframes,
curvas e restrições. As 40 loot tables foram serializadas, mas itens Java não
registrados no pack e funções de loot incompatíveis continuam omitidos,
registrados em `build/worlds/aether/loot_conversion_report.json`.
A lista exata de limitações do gerador de biomas está em
`build/worlds/bop/worldgen_conversion_report.json`.

A workflow compila os dois `.mcaddon` em `build/` (ignorado), valida sintaxe
dos scripts, estruturas NBT e identidade dos assets; **não executa Minecraft
Android**. A PR continua Draft. Sem permissão explícita dos detentores dos
recursos com reserva de direitos, **não publique** os pacotes gerados com
texturas e modelos originais.

### Entidades adicionais sem geometria artificial

No código Java, **Blue Swet, Golden Swet e Sentry** herdam um modelo de slime.
São convertidos como entidades independentes que reutilizam as geometrias
`geometry.slime` e `geometry.slime.armor` do Bedrock, com PNGs originais
e animação de compressão. **Passive Whirlwind** e **Evil Whirlwind** usam
`WhirlwindRenderer`, que não possui cubos: a adaptação Bedrock conserva a
representação por partículas e acrescenta sustentação/rotação e, no Evil,
dano com cooldown. Não há port direto do gerador de partículas e
movimentação Java. As 21 entidades são definições BP; nenhuma teve seu
comportamento e suas texturas atestados no cliente Android.

### Recuperação de progresso de masmorras

O runtime registra o estado `dungeon_pending` assim que o chefe morre,
antes de conceder o prêmio, e tenta recuperar a entrega ao reabrir o mundo
próximo da masmorra. `dungeon_rewarded` limita a distribuição e
`dungeon_cleared` marca a conclusão; blocos trancados são alterados em
lotes cooperativos. Essa recuperação é **implementação de código, não
teste de integridade transacional** sob crash, relog ou multiplayer;
estruturas Java ainda têm perdas de NBT, propriedades e loot.

## Proveniência auditada

| Módulo | Fonte Java como submódulo no Minizin | Classes / dados relevantes | Recursos locais aproveitados |
| --- | --- | --- | --- |
| The Aether | `mods/41-the-aether/upstream` gitlink `e07d30e16fbd0f09cc067b39594035e395dcf996` | `src/generated/resources/data/aether/worldgen/`, `src/main/resources/data/aether/structure/`; lógica original não executável no Android | 46 definições de bloco, incluindo modelos de masmorras de Silver Dungeon e múltiplas texturas de origem (holystone, skyroot, golden oak, minerais, portal e faces); texturas copiadas **somente em build/** |
| Biomes O' Plenty | `mods/19-biomes-o-plenty/upstream` gitlink `ef7f13e117faef0b97591f569175e53ea4fe664b` | `common/src/generated/resources/data/biomesoplenty/worldgen/biome/*.json` | 20 definições de bloco, com as texturas originais de troncos, folhas e plantas (incluindo faces superiores de troncos); para todos os 68 biomas **temperatura, chuva, água, cor da folhagem e grama lidas do JSON Java fixado**, quando disponíveis |

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
- O catálogo original de 68 biomas gera documentos Bedrock de biome/client biome, e regras de árvore/flor quando espécies e features têm registro.
- **Geração atual:** `minecraft:replace_biomes` fornece substituição parcial no Overworld/Nether, e `bop/main.js` verifica `Dimension.getBiome` antes de decorar. O ruido/roteamento Java permanece não portado.

## Build e validação (local ou CI)

```sh
git switch feature/minizin-worlds
git submodule update --init mods/19-biomes-o-plenty/upstream mods/41-the-aether/upstream
python -m pip install Pillow nbtlib numpy
node --check bedrock/worlds/aether/main.js
node --check bedrock/worlds/bop/main.js
python -m unittest discover -s bedrock/worlds/tests -v
python bedrock/worlds/build_worlds.py --mod both
```

Saídas locais:
- `build/worlds/Minizin_Worlds_aether_v0.2.8.mcaddon` (inclui templates NBT convertidos localmente e relatório de perdas)
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

## Segunda etapa implementada na mesma branch (12/10/2026)

- **The Aether:** 46 definições de bloco no builder, incluindo os arquivos originais de Aercloud, Quicksoil, Icestone, Gravitite, Carved Stone, Angelic/Hellfire Stone, Pillar e Sentry Stone. Faces superiores originais continuam preservadas. No runtime, Quicksoil concede aceleração temporária, Icestone congela blocos líquidos adjacentes na colocação, Cold Aercloud concede Slow Falling breve e Blue Aercloud aplica impulso vertical com cooldown. São adaptações de comportamento, não reprodução byte-a-byte da física Java.
- **Ilhas:** costa ocasional de Quicksoil; minérios com Gravitite raro; nuvens Aercloud em estratos de altura determinística. Não usa as density functions originais e não há implementação do céu/som/fog nativo do Java.
- **Estruturas:** `aether/convert_structures.py` lê os NBT Java de Bronze/Silver/Gold, reconstrói a paleta registrável e gera arquivos `.mcstructure` little-endian do Bedrock em `build/`, com um `conversion_report.json` registrando perda de estados, tile entities, entidades, omissões e templates grandes demais. Na CI foram exportados **21/21 templates** após declarar os blocos `locked_angelic_stone` e `boss_doorway_angelic_stone`; blocos sem correspondência, propriedades, tile entities, processos de geração e itens continuam registrados como perdas no relatório. O runtime chama `world.structureManager.place` para um template original de boss room ou entrada quando o pack está disponível e utiliza a sala simplificada apenas como fallback. A localização, a montagem modular (jigsaw) e os processadores Java não são reproduzidos.
- **Biomes O' Plenty:** 20 tipos de bloco, 9 definições de bioma Bedrock derivadas das configurações climáticas originais (`coniferous_forest`, `maple_woods`, `jade_cliffs`, `tropics` e `highland` adicionados) e geração em regiões determinísticas de 9 perfis com os respectivos troncos e folhas. Locais de chunks descarregados deixam de ser marcados permanentemente. Não é o roteamento real dos nove biomas Java.
- **Testes:** `test_structure_converter.py` verifica paleta e ordem ZYX, leitura de NBT Java big-endian/comprimido, serialização de estruturas Bedrock little-endian, identidade do bloco ausente como void e limite de volume; CI valida também a existência de estruturas dos três tiers, manifests, JS e os packs separados. Nenhum teste executa o cliente Android.

**Desvios constatados:** Os blocos trancados da Silver Dungeon são resistentes a mineração e explosões, mas a sequência Java de desafio de boss/chave que libera o acesso ainda não existe. A exportação **21/21** é exclusivamente estrutural, não uma prova de jogabilidade nem renderização.  NBT de estrutura contém estados Java e block entities incompatíveis; o conversor intencionalmente descarta propriedades de bloco Java sem mapeamento comprovado, não transporta conteúdos de baús/boss/entidades, e omite nomes não registrados no Bedrock. Mesmo os templates gerados **não são reconstruções perfeitas**. A taxa de 21/21 refere-se apenas à exportação estrutural, não a aparência verificada ou combate a bosses. O maior template Gold é condicionado ao volume máximo de segurança móvel.

### Vinculação de portais distantes

A entrada do jogador agora calcula a célula Aether mais próxima de suas coordenadas X/Z do Overworld (malha de 80 blocos), cria/retoma a respectiva ilha, limpa uma plataforma de pouso segura, acrescenta uma moldura de saída nessa célula e mantém coordenadas de retorno por jogador em propriedade dinâmica. **Não** é o algoritmo de seleção de portal da versão Java; não foi validado em multiplayer, troca de dispositivo ou com portais próximos a bordas de células. A instalação do pack ainda exige a Beta API no Bedrock.

### Variações Skyroot derivadas do Java

A pipeline lê os quatro biomas presentes no submódulo Java **fixado** (`skyroot_forest`, `skyroot_grove`, `skyroot_meadow`, `skyroot_woodland`) em `src/generated/resources/data/aether/worldgen/biome`. Valida o ID `aether:<nome>_trees`, preserva temperatura, chuva e referências a features e escreve `BP/scripts/biome_profiles.js`. O runtime seleciona um perfil por célula determinística e varia o número de árvores, além de introduzir flores brancas/roxas e berry bushes usando PNGs originais. **A densidade e a localização são adaptações**; o Bedrock ainda não tem um biome router nativo nessa dimensão com os algoritmos do Java.

## Referências

- Fontes originais fixadas nos gitlinks citados acima.
- [Minecraft: Custom Dimension API](https://learn.microsoft.com/en-us/minecraft/creator/documents/scripting/custom-dimension-api-tutorial).
- [Minecraft: Custom Biome Tutorial](https://learn.microsoft.com/en-us/minecraft/creator/documents/biomes/custombiometutorial).
- [Minecraft: Overworld Generation Rules (legado para custom biomes)](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/biomesreference/examples/components/minecraftbiomes_overworld_generation_rules).
- [Minecraft: Tree Feature](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/featuresreference/examples/features/minecraft_tree_feature).
