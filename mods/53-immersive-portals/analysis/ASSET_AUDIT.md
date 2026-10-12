# Immersive Portals — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** iPortalTeam/ImmersivePortalsMod

## Recursos encontrados
Java renderer/shaders; poucos recursos de modelos; repositório arquivado.

## Exemplos concretos para procurar
- `src/main/java/qouteall/imm_ptl/core/compat/iris_compatibility/IrisPortalRenderer.java`
- `src/main/resources/assets/immersive_portals/textures`

## Plano reaproveitar antes de modelar
Renderizador Java não portável via .mcaddon comum; sem redesenho 3D.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
