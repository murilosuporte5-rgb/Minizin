# Biomes O' Plenty — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** Glitchfiend/BiomesOPlenty

## Recursos encontrados
1348 modelos JSON; 663 texturas; JSON worldgen.

## Exemplos concretos para procurar
- `common/src/generated/resources/assets/biomesoplenty/models/block/black_flower_petal_block.json`
- `common/src/main/resources/assets/biomesoplenty/textures/block`

## Plano reaproveitar antes de modelar
Blocos JSON e texturas -> RP; reconstruir regras de worldgen no BP.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
