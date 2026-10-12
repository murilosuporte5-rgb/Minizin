# Ice and Fire — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** AlexModGuy/Ice_and_Fire

## Recursos encontrados
Modelos de dragões em Java Citadel; 1341 PNG; 252 OGG; 28 NBT.

## Exemplos concretos para procurar
- `src/main/java/com/github/alexthe666/iceandfire/client/model/ModelDragonBase.java`
- `src/main/resources/assets/iceandfire/textures`

## Plano reaproveitar antes de modelar
AdvancedModelBox e pivôs -> Blockbench/geo; animações precisam interpretação.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
