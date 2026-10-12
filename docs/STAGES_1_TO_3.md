# Minizin — etapas 1 a 3, sem refazer conversoes

Revisao: 2026-10-12. Base do inventario: ENGINEERING_STATUS.md e
CODEX_HANDOFF.md. Nao declarar portabilidade completa por gerar geometria.

## 1. Inventario e aproveitamento

| Familia | Ja recuperado | Sistema que ainda falta |
|---|---|---|
| Waystones | 17 modelos de blocos; BP/RP experimental | Teleporte integral |
| Ice and Fire | 192 Tabula; geometria de dragao | IA, montaria e animacoes |
| Biomes O' Plenty | 275 modelos com atlas | Geracao de mundo |
| MCA Reborn | 1.145 skins extraidas; 10 NPCs Bedrock de teste | Relacionamentos e profissoes |
| Carry On | 39 fontes/regras; demo de transportar 4 animais | Transporte de blocos com NBT |
| The Aether | 74 modelos de blocos | Dimensao e portais |
| Alex's Caves | Atlatitan | Animacoes, IA e biomas |
| Cataclysm | 41 de 70 modelos analisados | Combates e IA |
| Mowzie's Mobs | Bluff em prototipo | Ataques e IA |
| Immersive Portals | Estudo da renderizacao Java | Sem replica via packs comuns |
| RFTools | 864 recursos originais, 68 geometrias | Redes energeticas e maquinas |
| Origins | 10 origens e 61 powers | Runtime dos powers, 4 passivos de teste |
| Xaero's Minimap | Importador de waypoints | Minimap nativo |
| Distant Horizons | Dados LOD offline | Render LOD nativo |

As geometrias e os recursos anteriormente publicados estao na branch
generated-bedrock, pasta generated. Nao criar novas skins genericas.

## 2. Recursos originais

A nova ferramenta tools/split_next_four_packs.py separa a saida do pipeline
existente build/next_four, sem redesenhar PNGs, criar geometrias ficticias ou
misturar assets de mods diferentes. A origem de cada recurso e registrada em
PROVENANCE.json; licencas existentes acompanham a entrega fora do arquivo
instalavel. Carry On reutiliza visuais vanilla. Os OBJ/Blend originais do
RFTools permanecem preservados no pipeline para adaptacao posterior.

## 3. Logica adaptada, independente

MCA: interacao com papel ao agachar em aldeoes ou nos 10 NPCs MCA de teste.
Carry On: agachar e interagir com porco, galinha, ovelha ou vaca segurando
graveto; !carryon soltar interrompe o transporte.
Origins: !origins escolher; !origins atual. Quatro passivos experimentais.
RFTools: olhar uma magnetita e digitar !rftools maquina para uma demo
experimental de armazenamento de energia.

Cada um recebe seus proprios manifests, UUIDs, dependencias RP/BP, arquivos
Script API e recursos originais que pertencem a ele.

## Geracao

1. Inicializar os submodulos MCA, Carry On, RFTools e Origins.
2. Instalar Pillow.
3. Executar tools/build_next_four_pack.py --output build/next_four
4. Executar tools/convert_four_visual_assets.py --staged build/next_four
5. Executar tools/split_next_four_packs.py --staged build/next_four --output build/independent
6. Testar com python -m unittest discover -s tests -p test_split_next_four_packs.py -v

O GitHub Actions independent-four-mods.yml executa esta sequencia e publica
um artefato temporario Minizin-Four-Standalone-Bedrock-Addons.

Arquivos resultantes:
- build/independent/mca/Minizin_mca_Standalone_Prototype.mcaddon
- build/independent/carryon/Minizin_carryon_Standalone_Prototype.mcaddon
- build/independent/rftools/Minizin_rftools_Standalone_Prototype.mcaddon
- build/independent/origins/Minizin_origins_Standalone_Prototype.mcaddon

Nao instalar o antigo pacote combinado ao mesmo tempo que os separados,
pois as definicoes de entidades e itens teriam identificadores duplicados.
Um workflow aprovado indica compilacao estatica, nao validacao de modelos,
animacoes, content log, multiplayer, FPS ou jogabilidade no Android.
O uso/distribuicao de assets depende das licencas aplicaveis.
