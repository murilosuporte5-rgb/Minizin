# 58 — Distant Horizons

- **Fonte de referência:** https://gitlab.com/distant-horizons-team/distant-horizons
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** Pesquisa
- **Dificuldade estimada:** Extrema
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
LOD e visualização de terreno a distâncias grandes.

## Engenharia reversa / leitura de código
Estudar estrutura de níveis de detalhe e pipeline de chunks; medir custos e limitações.

## Plano de adaptação Bedrock
Experimentar ilusão visual com neblina, distância e estruturas; LOD nativo não cabe em add-on comum.

## Dependências e riscos
Precisa de modificação do cliente/renderização; foco em pesquisa, não promessa de port funcional.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
