# Mowzie's Mobs — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** BobMowzie/MowziesMobs-Public

## Recursos encontrados
21 BBModels; 24 arquivos geo; 14 animações; 186 PNG em textures; 253 OGG.

## Exemplos concretos para procurar
- `src/main/resources/assets/mowziesmobs/geo/bluff.geo.json`
- `assets/bluff.bbmodel`

## Plano reaproveitar antes de modelar
Bluff: reusar geo+PNG diretamente; converter animação Molang e portar IA depois.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
