# Origins — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** apace100/origins-fabric

## Recursos encontrados
82 texturas GUI; 1 modelo item; powers em JSON/Java.

## Exemplos concretos para procurar
- `src/main/resources/assets/origins/textures/gui/choose_origin.png`
- `src/main/resources/assets/origins/models/item/orb_of_origin.json`

## Plano reaproveitar antes de modelar
Reusar UX e ícones, portar poderes para Script API, pouca modelagem nova.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
