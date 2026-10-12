# Waystones — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** TwelveIterations/Waystones

## Recursos encontrados
Modelos JSON de blocos; 91 texturas de blocos; 3 estruturas NBT.

## Exemplos concretos para procurar
- `common/src/generated/resources/assets/waystones/models/block/andesite_waystone_bottom.json`
- `common/src/main/resources/assets/waystones/textures/block/andesite_waystone.png`

## Plano reaproveitar antes de modelar
JSON block/item -> geometria/UV Bedrock; teletransporte por Script API.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
