# RFTools — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** McJtyMods/RFTools

## Recursos encontrados
2 BLEND; 2 OBJ/MTL; 292 PNG em textures; modelos JSON.

## Exemplos concretos para procurar
- `art/powercell.blend`
- `src/main/resources/assets/rftools/models/block/powercell.obj`

## Plano reaproveitar antes de modelar
Importar malha existente no Blender/Blockbench e exportar geometria Bedrock.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
