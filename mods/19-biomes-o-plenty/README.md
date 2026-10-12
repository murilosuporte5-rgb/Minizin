# 19 — Biomes O' Plenty

- **Fonte de referência:** https://github.com/Glitchfiend/BiomesOPlenty
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P2
- **Dificuldade estimada:** Alta
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Biomas, plantas, árvores, efeitos ambientais e estruturas.

## Engenharia reversa / leitura de código
Mapear conjuntos de biomas, distribuição, regras de vegetação e geração dependente da versão.

## Plano de adaptação Bedrock
Começar por 2-3 áreas temáticas com blocos e árvores personalizados; validar mecanismos atuais de worldgen Bedrock.

## Dependências e riscos
Worldgen não é traduzível 1:1 entre Java e Bedrock; testar compatibilidade por versão.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
