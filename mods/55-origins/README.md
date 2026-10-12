# 55 — Origins

- **Fonte de referência:** https://github.com/apace100/origins-fabric
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P0
- **Dificuldade estimada:** Média
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Origens selecionáveis, passivos, habilidades e fraquezas.

## Engenharia reversa / leitura de código
Estudar catálogo de powers, triggers, recursos, cooldowns e persistência.

## Plano de adaptação Bedrock
Seleção de origem via formulário, tags/propriedades dinâmicas, efeitos periódicos e cooldowns.

## Dependências e riscos
Garantir que atributos persistam após morte, relog e mudança de dimensão.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
