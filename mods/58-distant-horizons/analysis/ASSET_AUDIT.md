# Distant Horizons — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** GitLab oficial

## Recursos encontrados
Fonte principal hospedada no GitLab; árvore de modelos não inventariada.

## Exemplos concretos para procurar
- `https://gitlab.com/distant-horizons-team/distant-horizons`
- `https://gitlab.com/distant-horizons-team/distant-horizons`

## Plano reaproveitar antes de modelar
LOD é lógica de cliente/renderização; não equivale a models reutilizáveis.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
