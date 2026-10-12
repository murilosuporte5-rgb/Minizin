# 34 — Carry On

- **Fonte de referência:** https://github.com/Tschipp/CarryOn
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P0
- **Dificuldade estimada:** Média
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Carregar/transportar blocos e entidades.

## Engenharia reversa / leitura de código
Inspecionar whitelist/blacklist, serialização de block entities e regras de interação.

## Plano de adaptação Bedrock
Sistema de pegar/colocar entidades permitidas; representação visual e armazenamento de estado do objeto carregado.

## Dependências e riscos
Evitar duplicação de inventário e perda de dados de blocos com contêiner.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
