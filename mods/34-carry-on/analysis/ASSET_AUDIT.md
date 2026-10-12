# Carry On — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** Tschipp/CarryOn

## Recursos encontrados
Código Java de carregar blocos e render de itens; poucos recursos próprios.

## Exemplos concretos para procurar
- `Common/src/main/java/tschipp/carryon/client/render/CarriedObjectRender.java`
- `Common/src/main/resources/data/carryon/tags`

## Plano reaproveitar antes de modelar
Reusar modelos vanilla e dados de whitelist; preservar NBT/inventário ao pegar.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
