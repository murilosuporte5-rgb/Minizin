# 15 — Waystones

- **Fonte de referência:** https://github.com/TwelveIterations/Waystones
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P0
- **Dificuldade estimada:** Média
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Teleporte entre marcos ativados; registro de destinos, propriedade e XP/custo.

## Engenharia reversa / leitura de código
Rastrear WaystoneTeleportManager, validações do destino, eventos, persistência, dimensionamento, cooldown e animais.

## Plano de adaptação Bedrock
Bloco de marco e ativação por jogador; registro persistente por world/player; seleção por formulário; validação de destino; teleporte por Script API.

## Dependências e riscos
Evitar destinos em chunks indisponíveis, coordenadas não seguras e loops de teleporte.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
