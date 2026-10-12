# Minizin — pesquisa de mods para Minecraft Bedrock Mobile

Repositório de **engenharia reversa e implementação independente** de funcionalidades inspiradas em 14 mods populares do Minecraft Java, com foco em Android/Bedrock.

> **Estado atual:** inventário técnico e plano de desenvolvimento. **Não** contém os 14 mods originais, `.jar` convertidos, nem um `.mcaddon` funcional. O código Java não é executável diretamente no Bedrock.

## Índice — 14 mods

| Nº | Referência | Meta Bedrock | Prioridade |
| --- | --- | --- | --- |
| 15 | [Waystones](mods/15-waystones/README.md) | Teleporte, destinos salvos e custo opcional | P0 |
| 16 | [Ice and Fire: Dragons](mods/16-ice-and-fire/README.md) | Dragões, montarias e criaturas | P2 |
| 19 | [Biomes O' Plenty](mods/19-biomes-o-plenty/README.md) | Biomas, vegetação e estruturas | P2 |
| 33 | [Minecraft Comes Alive Reborn](mods/33-mca-reborn/README.md) | Aldeões sociais, profissões e relacionamentos | P1 |
| 34 | [Carry On](mods/34-carry-on/README.md) | Carregar blocos/entidades | P0 |
| 41 | [The Aether](mods/41-the-aether/README.md) | Dimensão, portais e ilhas | P2 |
| 42 | [Alex's Caves](mods/42-alexs-caves/README.md) | Cavernas temáticas e criaturas | P2 |
| 43 | [L_Ender's Cataclysm](mods/43-cataclysm/README.md) | Bosses, arenas e equipamentos | P2 |
| 44 | [Mowzie's Mobs](mods/44-mowzies-mobs/README.md) | Criaturas com IA e animações especiais | P2 |
| 53 | [Immersive Portals](mods/53-immersive-portals/README.md) | Protótipo de viagem entre áreas; visão contínua fora do escopo inicial | Pesquisa |
| 54 | [RFTools](mods/54-rftools/README.md) | Máquinas, energia e automações | P1 |
| 55 | [Origins](mods/55-origins/README.md) | Origens, poderes e desvantagens | P0 |
| 57 | [Xaero's Minimap](mods/57-xaeros-minimap/README.md) | Waypoints e navegação; minimapa completo depende do cliente | Pesquisa |
| 58 | [Distant Horizons](mods/58-distant-horizons/README.md) | Estudo de LOD; sem promessa de renderização nativa alterada | Pesquisa |

## Estrutura

- `mods/NN-nome/README.md`: referência original, mecanismos de interesse, estratégia Bedrock, riscos e entregáveis.
- `bedrock/ARCHITECTURE.md`: arquitetura do conjunto de add-ons.
- `bedrock/IMPLEMENTATION_PLAN.md`: fases, gates, desempenho e ordem de execução.
- `bedrock/PERFORMANCE_MOBILE.md`: orçamento de memória e testes em Android.
- `RESEARCH_RULES.md`: procedência, licenças e reprodutibilidade.

## Princípios

1. Consultar o código original quando público; inspecionar downloads e binários apenas conforme licença e escopo aplicáveis.
2. **Não republicar** os `.jar`, modelos, texturas, músicas ou código de terceiros sem autorização/licença compatível.
3. Criar lógica, nomes internos e recursos independentes para o Bedrock; registrar inspiração e atribuições.
4. Distinguir `VERIFICADO`, `HIPÓTESE`, `NÃO TESTADO` e `LIMITAÇÃO`.
5. Projetar para Android: budgets de memória, carregamento de entidades, escala de animações e modo de desempenho.
6. Modificação de renderizador (portais visíveis, minimapa completo, distant LOD) **não está disponível como port de Java** via behavior/resource packs convencionais.
7. API experimental de dimensões customizadas exige checagem de versão e não equivale a portar o The Aether automaticamente.

## Estado

- [x] Repositório criado pelo usuário.
- [x] Índice técnico e mapeamento de fontes.
- [ ] Experimentos de add-on Bedrock.
- [ ] Testes em dispositivo e medição real de FPS/memória.
- [ ] Compatibilidade multiplayer.
- [ ] Pacote `.mcaddon` instalável.

**Última revisão:** 2026-10-11.
## Código-fonte vinculado (12 submódulos)

Doze diretórios `mods/*/upstream` são **git submodules**, apontando para commits fixos de repositórios públicos dos respectivos autores. Isso permite estudar as fontes sem copiá-las como se fossem código próprio.

```bash
git clone --recurse-submodules https://github.com/murilosuporte5-rgb/Minizin.git
# Para uma cópia já clonada:
git submodule update --init --recursive
```

**Atenção:** clonagem recursiva de todos os mods Java pode consumir muito espaço; não é recomendada diretamente em celulares com pouco armazenamento. Os submódulos não rodam no Minecraft Bedrock. A licença e os créditos do upstream permanecem aplicáveis.

**Submódulo Cataclysm confirmado:** o repositório oficial lender544/new1.20.1 contém código de Cataclysm, além de depender da Lionfish API. **Ainda sem submódulo:** Xaero's Minimap (proprietário) e Distant Horizons (fonte no GitLab; auditada em CI).

## Conversores e resultados — 12/10/2026

[Relatório técnico verificado](ENGINEERING_STATUS.md). Conversores, builds experimentais e jobs do GitHub Actions foram publicados. Os testes de geração foram aprovados, mas **a engenharia reversa completa e os 14 ports jogáveis ainda não foram concluídos**. Não criar modelos novos antes de tentar reaproveitar `.bbmodel`, `.geo.json`, Tabula `.tbl`, `AdvancedModelBox`, `.obj`, `.blend`, JSON de blocos e PNG/OGG originais.

## Branch de conversões pronta para o Codex

Arquivos gerados pela CI foram publicados em [generated-bedrock](https://github.com/murilosuporte5-rgb/Minizin/tree/generated-bedrock/generated), com scripts/conversores originais na branch `main`. Leia [CODEX_HANDOFF.md](CODEX_HANDOFF.md) antes de alterar modelos, itens ou lógica.

A extração/compilação de 375 definições de itens, 10 NPCs MCA e 69 modelos de blocos MCA/RFTools passou no [GitHub Actions](https://github.com/murilosuporte5-rgb/Minizin/actions/runs/38238336803). Nenhuma dessas compilações equivale a 14 mods totalmente jogáveis no Minecraft Android.
