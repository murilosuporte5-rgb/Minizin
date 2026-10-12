# L_Ender's Cataclysm — Inventário para engenharia reversa

**Status:** código/recurso identificado por inspeção estática; conversão, renderização e testes Android pendentes.

**Fonte:** Fonte integral ainda não verificada

## Recursos encontrados
Arquivo .jar autorizado pendente; Lionfish API não é Cataclysm completo.

## Exemplos concretos para procurar
- `https://www.curseforge.com/minecraft/mc-mods/lendercataclysm`
- `https://github.com/lender544/new1.20.1`

## Plano reaproveitar antes de modelar
Inventariar .jar do mod real antes de prometer modelos/animações.

## Checklist do Codex
1. Abrir o arquivo fonte original e verificar o commit/licença.
2. Identificar geometria, UV, hierarquia, pivôs, animação, texturas, efeitos e formatos.
3. Classificar `REUSE_DIRECT`, `CONVERT`, `REBUILD_PARTIAL` ou `MISSING` com evidência.
4. Gerar os resultados em `build/`, não publicar assets sem confirmar autorização específica de redistribuição.
5. Testar em Bedrock Android e registrar prints/FPS; não declarar concluído antes do teste.
