# 44 — Mowzie's Mobs

- **Fonte de referência:** https://github.com/BobMowzie/MowziesMobs-Public
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P2
- **Dificuldade estimada:** Alta
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Criaturas especiais, animação e combate.

## Engenharia reversa / leitura de código
Localizar máquinas de estado, temporizadores, ataques e interações com ambiente.

## Plano de adaptação Bedrock
Criaturas autorais com animation controllers, state machines e combate orientado por eventos.

## Dependências e riscos
Performance de animação/partículas e licenças de recursos visuais.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
