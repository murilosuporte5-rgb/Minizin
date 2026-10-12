# Minizin — checkpoint de integração 2026-10-12

## Estado do checkout

- Branch local de integração: `integration/kuroko-minizin-20261012`.
- Base: `main` (`0377de200d9f58eedcf6ce41d90e2af60119eb7e`).
- PRs integrados localmente: #4 (worlds), #3 (creatures), #5 (systems) e #2 (original models/gameplay).
- A branch remota `integration/minizin-full-test-20261012` foi preservada; não foi sobrescrita.
- Os artefatos versionados de `origin/generated-bedrock` foram recuperados antes de gerar novos recursos.

Os PRs continuam abertos no GitHub. Esta integração local não é uma declaração de merge remoto nem de equivalência final.

## Validação executada

| Gate | Resultado | Evidência |
|---|---|---|
| Testes Python | **26/26 OK** | `python -m unittest discover -s tests -v` |
| Testes Node | **36/36 OK** | `node --test tests/*.test.mjs` |
| Validação estrutural de packs | **OK** | 4 packs: 12 entidades, 5 blocos, 9 scripts, 2 animações |
| Build dos quatro packs seguintes | **OK** | `build/next_four_extended/` |
| Build de entidades/blocos convertidos | **OK** | `build/stages23_packs/` |
| Pacote combinado de 12 mods | **OK estrutural** | `build/combined_all/REPORT.json` |
| Teste no Minecraft Bedrock Android | **PENDENTE** | nenhum cliente/dispositivo Android disponível nesta execução |

O pacote combinado registrou 19 entidades, 352 blocos, 20 scripts, 10 animações e 8 sons. Esses números são artefatos presentes no pacote, não porcentagens de portabilidade.

## Matriz factual do pacote combinado

| Mod | Incluído no pacote | O que está presente | Limites ainda abertos |
|---|---:|---|---|
| Waystones | Sim | bloco colocável, ativação, renomeação, persistência, teleporte com chegada segura e migração limitada | teste de jogo, multiplayer, reconexão e migração real pendentes |
| Ice and Fire | Sim | três entidades de dragão, texturas e poses convertidas para clipes Bedrock | IA/voo/domesticação/ovos/armaduras 1:1 e QA visual pendentes |
| Biomes O’ Plenty | Sim | 275 geometrias/atlases de blocos convertidos | distribuição/geração de biomas e estruturas não validadas |
| The Aether | Sim | 74 geometrias/atlases de blocos convertidos | dimensão/portal/worldgen/bosses não validados neste pacote |
| Alex’s Caves | Sim | Atlatitan com geometria/textura e entidade experimental | IA, animações e mecânicas originais pendentes |
| Cataclysm | Sim | Ender Guardian, Ignis e Harbinger com geometrias/texturas e estados de boss experimentais | IA, fases, ataques e animações 1:1 pendentes |
| Mowzie’s Mobs | Sim | Bluff com geometria, textura e idle Bedrock corrigida | ataques/IA originais e QA no jogo pendentes |
| MCA Reborn | Sim | NPCs, skins, relações, casamento/família e nascimento experimental | diálogos, profissões, skins completas e teste multiplayer pendentes |
| Carry On | Sim | transporte persistido de entidades/blocos conforme o pack experimental | casos de contêiner, relog, multiplayer e perda de conexão pendentes |
| RFTools | Sim | itens, modelos, gerador/célula/cabos/lâmpada e rede experimental | cobertura de máquinas, GUI, automações e equivalência de energia pendentes |
| Origins | Sim | escolhas, persistência e poderes ativos experimentais | cobertura integral dos 61 poderes, cooldowns e desvantagens pendente |
| Sophisticated Backpacks | Sim | identidade individual, 27 espaços, upgrades/filtros e migração protegida | GUI nativa equivalente, multiplayer e teste Android pendentes |

Immersive Portals e Xaero’s Minimap permanecem excluídos. Distant Horizons continua apenas em investigação de LOD; nenhum renderizador fictício foi incluído.

## Correções feitas neste checkpoint

1. Resolvidos os três conflitos entre os PRs compartilhando scripts MCA, Origins e Waystones; foi preservada a implementação de sistemas baseada em bloco/persistência.
2. Corrigida a serialização das mochilas para não persistir campos `undefined` que o JSON remove durante a migração.
3. Tornados os harnesses Node independentes de CRLF no Windows.
4. Corrigido o fixture Xaero para escrever UTF-8 explicitamente.
5. Corrigido o validador para geometrias como string, arquivos UTF-8 e ícones vanilla `chest`/`hopper`.
6. Convertido o canal `vector/easing` do idle do Bluff para canais de posição/rotação Bedrock válidos.

## Próximo gate obrigatório

Instalar o `.mcaddon` em um cliente Bedrock Android identificado, habilitar os packs em um mundo novo e registrar versão do cliente, Content Log, FPS, memória, carregamento, salvamento, morte, reconexão e multiplayer. Até esse gate, o projeto deve ser descrito como **integração experimental estruturalmente validada**, nunca como 12/12 concluído.
