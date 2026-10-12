# Próximos quatro mods: extração baseada nas fontes reais

Este pipeline usa os submódulos Git já vinculados e gera **cópias de recursos originais para análise local** em `build/extracted/<mod>`; não recria modelos do zero e não declara que os quatro mods já rodam no Bedrock.

| Mod | Original verificado | Tipos |
|---|---|---|
| MCA Reborn | Luke100000/minecraft-comes-alive @ 0e9094f | 280 JSON de modelos block/item, skins em `assets/mca/skins`, modelos e renderizadores Java, PNG, sons, diálogos/dados |
| Carry On | Tschipp/CarryOn @ 168f3fb | Tags de blacklist/whitelist, classes de renderização/transporte; sem modelos 3D dedicados nesta árvore |
| RFTools | McJtyMods/RFTools @ 030a495 | 266 modelos JSON, 2 OBJ+MTL, 2 Blender `.blend`, PNGs, GUI, OGG |
| Origins | apace100/origins-fabric @ 80bf805 | 10 origens, 61 poderes JSON, origin layer, ícones e GUI, 1 modelo de item |

**Código do extrator:** `tools/extract_next_four.py`.

```bash
git submodule update --init --depth 1 mods/33-mca-reborn/upstream mods/34-carry-on/upstream mods/54-rftools/upstream mods/55-origins/upstream
python tools/extract_next_four.py --mod mca --output build/extracted/mca
python tools/extract_next_four.py --mod carryon --output build/extracted/carryon
python tools/extract_next_four.py --mod rftools --output build/extracted/rftools
python tools/extract_next_four.py --mod origins --output build/extracted/origins
```

O extrator recusa fontes fora do diretório de recurso de cada mod e exclui fontes tipográficas binárias. Preserva caminho original, tamanho, SHA-256 e tipo. Artefatos do GitHub Actions têm prazo de retenção. Estes arquivos ainda não são modelos Bedrock convertidos nem packs completos.

**Licenças upstream verificadas:** MCA Reborn GPL-3.0; Carry On LGPL-3.0; RFTools MIT; Origins MIT. A permissão relatada pelo usuário permite conduzir o trabalho, mas qualquer distribuição dos materiais deve respeitar os termos aplicáveis e as autorizações específicas sobre recursos visuais.
