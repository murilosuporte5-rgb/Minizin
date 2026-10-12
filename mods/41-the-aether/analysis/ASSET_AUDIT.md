# The Aether — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** The-Aether-Team/The-Aether

## Recursos encontrados
1020 modelos JSON; 954 texturas; 73 OGG; 34 NBT.

## Exemplos concretos para procurar
- `src/generated/resources/assets/aether/models/block/aerogel.json`
- `src/main/resources/assets/aether/textures/block`

## Plano reaproveitar antes de modelar
Converter blocos e estruturas; ambiente e dimensões exigem testes Bedrock.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
