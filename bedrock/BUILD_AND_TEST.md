# Minizin — build e engenharia reversa

## Entrega executável em código
- `tools/java_model_to_bedrock.mjs`: converte modelos de blocos JSON do Java com `parent` e UV explícita; recusa múltiplas texturas por face sem atlas para não gerar resultado incorreto.
- `bedrock/packs/waystones/`: RP/BP do Waystone de andesito de 9 cubos, textura real e script inicial de ativação/teleporte.
- `bedrock/packs/mowzie/`: RP/BP para Bluff, sua geometria `minecraft:geometry`, textura e idle (Molang normalizado).
- `tools/build_bedrock_packs.py`: valida referências RP/BP, manifests, IDs, geometria e textura; empacota .mcaddon.
- `tools/tabula_inspect.py`: abre `.tbl` como ZIP e extrai `model.json`. Inventário confirmado: 192 `.tbl` em Ice and Fire, não desenhar os dragões do zero.

## Construção local ou no Codex
```bash
git clone --recurse-submodules https://github.com/murilosuporte5-rgb/Minizin.git
cd Minizin
node --test tests/java_model_to_bedrock.test.mjs
node tools/java_model_to_bedrock.mjs convert mods/15-waystones/upstream waystones geometry.minizin.andesite_waystone 64 32 build/test-waystone.geo.json block/andesite_waystone_bottom@0 block/andesite_waystone_top@16
python tools/build_bedrock_packs.py waystones
python tools/build_bedrock_packs.py mowzie
python tools/tabula_inspect.py mods/16-ice-and-fire/upstream/src/main/resources/assets/iceandfire/models/tabula/firedragon/firedragon_BaseMale.tbl --extract-to build/fire_dragon_tabula
```

## Teste no Android
Instalar os pacotes gerados em uma cópia de mundo, habilitar RP e BP e usar `/summon minizin:andesite_waystone ~ ~ ~` e `/summon minizin:bluff ~ ~ ~`. Verificar visuais, idle, uso via toque, persistência e teleportes. **Esses testes ainda não foram realizados.**

## Escopo pendente (não prometer entrega completa)
- Converter/validar o rig e as 192 poses Tabula para animações Bedrock.
- Converter modelos `AdvancedModelBox` e suas animações Java do Alex's Caves.
- Expandir 14 mods: modelos/texturas/estruturas, IA, worldgen, compatibilidade, performance.
- Cataclysm/Xaero demandam arquivos originais para inventário completo; Distant Horizons é motor gráfico e código no GitLab.
- A obtenção de autorização para adaptação foi informada pelo usuário. Para redistribuir assets originais em repositório público, registrar escopo dessa permissão.
