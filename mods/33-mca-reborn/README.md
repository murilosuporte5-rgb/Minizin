# 33 — Minecraft Comes Alive Reborn (MCA Reborn)

- **Fonte de referência:** https://github.com/Luke100000/minecraft-comes-alive
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P1
- **Dificuldade estimada:** Alta
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Aldeões com identidades, relações, profissões e diálogos.

## Engenharia reversa / leitura de código
Investigar ciclo de vida NPC, reputação, persistência de relacionamento e eventos de interação.

## Plano de adaptação Bedrock
Entidades NPC com propriedades dinâmicas, diálogos por formulários e estados persistentes de reputação.

## Dependências e riscos
Salvar sem corromper mundos; limitar ciclos de IA em segundo plano.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
