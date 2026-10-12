# 53 — Immersive Portals

- **Fonte de referência:** https://github.com/iPortalTeam/ImmersivePortalsMod
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** Pesquisa
- **Dificuldade estimada:** Extrema
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Visão e movimento contínuos através de portais.

## Engenharia reversa / leitura de código
Revisar arquitetura de renderização de múltiplas cenas, recursão, clipping e sincronização.

## Plano de adaptação Bedrock
Prototipar transição funcional sem visualização contínua; documentar requisitos de motor para efeito real.

## Dependências e riscos
O repositório GitHub consultado está arquivado; um add-on padrão não injeta renderizador nativo.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
