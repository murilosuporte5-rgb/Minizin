# Engenharia reversa dos 14 mods — modelo antes da modelagem

**Otimização:** reusar os recursos concretos do upstream antes de criar geometria nova. Inventário estático de 11 repositórios Git; 3 dependem de fonte externa/inventário posterior.

## Visão geral

| Mod | Recursos visuais existentes | Próxima estratégia |
|---|---|---|
| [Waystones](mods/15-waystones/analysis/ASSET_AUDIT.md) | Modelos JSON de blocos; 91 texturas de blocos; 3 estruturas NBT | JSON block/item -> geometria/UV Bedrock; teletransporte por Script API |
| [Ice and Fire](mods/16-ice-and-fire/analysis/ASSET_AUDIT.md) | Modelos de dragões em Java Citadel; 1341 PNG; 252 OGG; 28 NBT | AdvancedModelBox e pivôs -> Blockbench/geo; animações precisam interpretação |
| [Biomes O' Plenty](mods/19-biomes-o-plenty/analysis/ASSET_AUDIT.md) | 1348 modelos JSON; 663 texturas; JSON worldgen | Blocos JSON e texturas -> RP; reconstruir regras de worldgen no BP |
| [MCA Reborn](mods/33-mca-reborn/analysis/ASSET_AUDIT.md) | 1317 PNG no repo; 100 OGG; modelos JSON e NPC Java | Reusar skins, objetos, interfaces e sons; lógica NPC via Script API |
| [Carry On](mods/34-carry-on/analysis/ASSET_AUDIT.md) | Código Java de carregar blocos e render de itens; poucos recursos próprios | Reusar modelos vanilla e dados de whitelist; preservar NBT/inventário ao pegar |
| [The Aether](mods/41-the-aether/analysis/ASSET_AUDIT.md) | 1020 modelos JSON; 954 texturas; 73 OGG; 34 NBT | Converter blocos e estruturas; ambiente e dimensões exigem testes Bedrock |
| [Alex's Caves](mods/42-alexs-caves/analysis/ASSET_AUDIT.md) | Modelos Java AdvancedModelBox; 1263 PNG; 1474 OGG; 91 NBT | Extrair cubos, hierarquia, UV e pivôs do Java; adaptar animações/AI |
| [L_Ender's Cataclysm](mods/43-cataclysm/analysis/ASSET_AUDIT.md) | Arquivo .jar autorizado pendente; Lionfish API não é Cataclysm completo | Inventariar .jar do mod real antes de prometer modelos/animações |
| [Mowzie's Mobs](mods/44-mowzies-mobs/analysis/ASSET_AUDIT.md) | 21 BBModels; 24 arquivos geo; 14 animações; 186 PNG em textures; 253 OGG | Bluff: reusar geo+PNG diretamente; converter animação Molang e portar IA depois |
| [Immersive Portals](mods/53-immersive-portals/analysis/ASSET_AUDIT.md) | Java renderer/shaders; poucos recursos de modelos; repositório arquivado | Renderizador Java não portável via .mcaddon comum; sem redesenho 3D |
| [RFTools](mods/54-rftools/analysis/ASSET_AUDIT.md) | 2 BLEND; 2 OBJ/MTL; 292 PNG em textures; modelos JSON | Importar malha existente no Blender/Blockbench e exportar geometria Bedrock |
| [Origins](mods/55-origins/analysis/ASSET_AUDIT.md) | 82 texturas GUI; 1 modelo item; powers em JSON/Java | Reusar UX e ícones, portar poderes para Script API, pouca modelagem nova |
| [Xaero's Minimap](mods/57-xaeros-minimap/analysis/ASSET_AUDIT.md) | Código-fonte público não verificado; .jar autorizado necessário | Mapear texturas/UI do arquivo oficial; minimapa completo depende do renderer |
| [Distant Horizons](mods/58-distant-horizons/analysis/ASSET_AUDIT.md) | Fonte principal hospedada no GitLab; árvore de modelos não inventariada | LOD é lógica de cliente/renderização; não equivale a models reutilizáveis |

## Formatos e adaptação
- `.bbmodel`: abrir no Blockbench, revisar ossos e UV; exportar compatível com Bedrock.
- `.geo.json`: inspecionar `minecraft:geometry`, bones, pivot, UV e escala; testar no Resource Pack.
- `.animation.json`: migrar e testar curvas/expressões Molang; não assumir compatibilidade 1:1 entre GeckoLib e Bedrock.
- Java `AdvancedModelBox` e `addBox`: extrair cubos, pivôs e parent; construir conversor assistido em vez de esculpir novamente.
- Java models block/item JSON: resolver hierarquia `parent`, UV, textura e estados; converter para Resource Pack.
- `.obj`/`.blend`: abrir em Blender, simplificar/rebake e exportar geometria na ferramenta adequada.
- `.nbt` estruturas Java: mapear palettes/IDs de blocos para formato Bedrock.
- Renderizadores/shaders Java: não executar como add-on Bedrock, precisam alternativas ou modificação do cliente.

## Comandos locais
```bash
git clone --recurse-submodules https://github.com/murilosuporte5-rgb/Minizin.git
cd Minizin
python tools/reuse_assets.py scan
python tools/reuse_assets.py stage-mowzie-bluff
```

O último comando monta arquivos RP/BP demonstrativos reutilizando a geometria e textura de Bluff, mas não foi executado/testado nesta sessão. Saída local `build/` — fora do Git, até autorização específica de adaptação e distribuição.

## Evidência do caso Bluff
- `src/main/resources/assets/mowziesmobs/geo/bluff.geo.json` começa com `format_version: 1.12.0`, `minecraft:geometry` e bones.
- `src/main/resources/assets/mowziesmobs/animations/bluff.animation.json` contém movimentos e expressões temporais.
- `src/main/resources/assets/mowziesmobs/textures/entity/bluff.png` e `assets/bluff.bbmodel` também existem.
- O script não liga a animação original nem a IA/ataques; essas etapas continuam no backlog.

**Limites:** Cataclysm precisa do .jar oficial (Lionfish API não é o mod inteiro), Xaero's Minimap possui termos proprietários, Distant Horizons reside no GitLab. Compatibilidade/memória/qualidade não verificadas no Minecraft Android.
