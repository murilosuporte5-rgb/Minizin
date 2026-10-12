# Arquitetura proposta — Bedrock Mobile

**Estado:** design inicial, ainda não executado no Minecraft.

## Separação
- **Behavior Pack (BP):** entidades, itens, blocos, recipes, loot, scripts e persistência.
- **Resource Pack (RP):** geometria, texturas originais/licenciadas, animation controllers e sons.
- **Script API:** eventos, forms, regras, timers, tags e propriedades dinâmicas.
- **Módulos independentes:** cada recurso pode ser ativado/desativado sem apagar o progresso dos outros.

## Núcleo compartilhado (a implementar)
1. Registro de `feature_id` e `version` por módulo.
2. Persistência por jogador e por mundo com esquema versionado e migração.
3. Scheduler por orçamento de ticks, com tarefas escalonadas e limites por dimensão.
4. Gerenciamento de entidades próximas ao jogador; suspender IA distante.
5. Menu de opções: qualidade/partículas/distância/max mobs/modos de desempenho.
6. API de eventos internos para não acoplar dragões, bosses, máquinas e teleportes.
7. Preflight do mundo e cópia de segurança antes de mudanças de schema.

## Não suportado como conversão direta
- Executar código Forge/NeoForge/Fabric dentro do Bedrock.
- Portais com renderização contínua só via packs comuns.
- LOD de terreno por alteração do renderizador do cliente.
- Reprodução automática de código, models e texturas que pertençam a terceiros.

## Dimensões
Verificar APIs e flags experimentais por versão. Referência inicial: https://github.com/MicrosoftDocs/minecraft-creator/blob/main/creator/Documents/scripting/custom-dimension-api-tutorial.md
