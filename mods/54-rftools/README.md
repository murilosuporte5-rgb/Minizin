# 54 — RFTools

- **Fonte de referência:** https://github.com/McJtyMods/RFTools
- **Alvo:** Minecraft Bedrock Android (versão exata a fixar antes de implementar)
- **Prioridade:** P1
- **Dificuldade estimada:** Alta
- **Status:** levantamento, **não implementado**

## O que queremos reproduzir
Máquinas, energia, automação e dispositivos.

## Engenharia reversa / leitura de código
Separar sistemas do RFTools original e dependências; avaliar versões mais recentes nos módulos do autor.

## Plano de adaptação Bedrock
Rede discreta de energia com máquinas, processamento por ticks limitado e UI de status.

## Dependências e riscos
Evitar loops custosos e inconsistência entre chunks/máquinas; repo consultado é de geração antiga.

## Entregáveis esperados
1. Registrar versões exatas, licença e permissões de uso da fonte.
2. Localizar classes, assets e configuração que controlam a funcionalidade.
3. Especificar comportamento reproduzível e casos de teste no Bedrock.
4. Desenvolver comportamento independente, sem redistribuir arquivos não licenciados.
5. Medir no Android: FPS, memória, tempo de carregamento, travamentos e compatibilidade multiplayer.

**Legenda:** esta pasta é documentação inicial; não contém a versão original do mod nem um `.mcaddon` pronto.
