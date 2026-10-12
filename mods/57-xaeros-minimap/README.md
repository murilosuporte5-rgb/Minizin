# 57 — Xaero's Minimap

- **Fonte de referência:** https://www.curseforge.com/minecraft/mc-mods/xaeros-minimap
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** Pesquisa
- **Dificuldade estimada:** Muito alta
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Minimapa, waypoints e marcadores.

## Engenharia reversa / leitura de código
Documentar comportamentos publicamente observáveis; referência de UI sem descompilar/redistribuir material proprietário.

## Plano de adaptação Bedrock
Waypoints coordenados com HUD simplificada, bússola e lista de pontos; mapa real requer recursos do cliente.

## Dependências e riscos
All Rights Reserved; não publicar código e assets de Xaero. Limites de renderização Bedrock.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
