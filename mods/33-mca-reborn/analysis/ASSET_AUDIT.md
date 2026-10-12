# MCA Reborn — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** Luke100000/minecraft-comes-alive

## Recursos encontrados
1317 PNG no repo; 100 OGG; modelos JSON e NPC Java.

## Exemplos concretos para procurar
- `common/src/generated/resources/assets/mca/models/item/black_acacia_crib.json`
- `common/src/main/resources/assets/mca`

## Plano reaproveitar antes de modelar
Reusar skins, objetos, interfaces e sons; lógica NPC via Script API.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
