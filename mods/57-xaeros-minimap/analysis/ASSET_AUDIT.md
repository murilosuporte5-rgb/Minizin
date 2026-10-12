# Xaero's Minimap — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** CurseForge (proprietário)

## Recursos encontrados
Código-fonte público não verificado; .jar autorizado necessário.

## Exemplos concretos para procurar
- `https://www.curseforge.com/minecraft/mc-mods/xaeros-minimap`
- `https://www.curseforge.com/minecraft/mc-mods/xaeros-minimap`

## Plano reaproveitar antes de modelar
Mapear texturas/UI do arquivo oficial; minimapa completo depende do renderer.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
