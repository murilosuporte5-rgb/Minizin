# Alex's Caves — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** AlexModGuy/AlexsCaves

## Recursos encontrados
Modelos Java AdvancedModelBox; 1263 PNG; 1474 OGG; 91 NBT.

## Exemplos concretos para procurar
- `src/main/java/com/github/alexmodguy/alexscaves/client/model/AtlatitanModel.java`
- `src/main/resources/assets/alexscaves/textures/entity/atlatitan.png`

## Plano reaproveitar antes de modelar
Extrair cubos, hierarquia, UV e pivôs do Java; adaptar animações/AI.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
