# AGENTS.md — Codex: reutilização obrigatória

Leia este arquivo antes de alterar o projeto Minizin.

## Regra principal
**Nunca comece modelando tudo do zero.** Inventarie e aproveite os modelos, rigs, UV, texturas, animações, áudio e estruturas já existentes nos 14 mods. Só recrie partes ausentes após justificar a lacuna. Preserve tudo que já funciona no projeto e faça mudanças incrementais.

## Procedimento obrigatório
1. Leia `REVERSE_ENGINEERING_ALL.md` e `mods/<mod>/analysis/ASSET_AUDIT.md`.
2. Execute `git submodule update --init --recursive` e `python tools/reuse_assets.py scan`.
3. Procure `.bbmodel`, `.geo.json`, `.animation.json`, `.obj`, `.blend`, `models/block/*.json`, `client/model/*.java`, PNG, OGG e NBT.
4. Antes de modelar, registre caminho, commit e estratégia `REUSE_DIRECT` / `CONVERT` / `REBUILD_PARTIAL` / `MISSING`.
5. Para Mowzie's, priorize `python tools/reuse_assets.py stage-mowzie-bluff`; executar esse comando produz artefatos locais experimentais (não comprovadamente funcionais).
6. Para Ice and Fire e Alex's Caves, extraia primeiro caixas/pivôs/UV dos modelos Java Citadel; não construa dragões/dinossauros do zero.
7. Para RFTools, priorize arquivos `.blend`/`.obj`; para The Aether, Waystones e Biomes O' Plenty, `models/*.json` + texturas + estruturas.
8. Faça a lógica Bedrock em BP/Script API; código Forge/Fabric/NeoForge não executa no Bedrock Android.
9. Não sobreponha funcionalidades já criadas pelo Codex sem diffs, backups e teste antes/depois.
10. Meça FPS/RAM real e logs no Android; não afirme conclusão sem teste.

## Direitos e publicação
O usuário informa autorização para estudar os mods. Antes de publicar modelos/texturas/código no Minizin, documente também o escopo da permissão **para adaptar e redistribuir** cada recurso. Guarde assets originais/convertidos em `build/` (gitignored) até isso estar confirmado. Fontes públicas não implicam redistribuição livre: Waystones e Mowzie's Mobs reservam direitos; The Aether separa licença do código e dos assets.

## Prioridade de implementação
Waystones/Carry On/Origins (sistemas); Mowzie's Mobs (geometrias já próximas de Bedrock); RFTools (OBJ/Blend); Ice and Fire/Alex's Caves (modelos Java); Aether/Biomes O' Plenty/MCA (mundo e NPCs); Cataclysm (inventário do .jar); Xaero/Immersive Portals/Distant Horizons (avaliar renderizador, sem falsas promessas).

## Pipeline de conversão já disponível — usar ANTES da criação de modelos

- `tools/tabula_to_bedrock.py` e `tools/tabula_batch_to_bedrock.py`: 192/192 poses Tabula do Ice and Fire geradas no GitHub Actions.
- `tools/citadel_java_to_bedrock.py`: modelos Citadel Java, incluindo modelos herdados (`SauropodBaseModel.java` + `AtlatitanModel.java`).
- `tools/block_atlas_to_bedrock.py`: converte blocos e compõe atlases reais de múltiplas texturas; 366 modelos convertidos.
- `tools/java_model_to_bedrock.mjs`: parser de modelos Java JSON com herança, adequado para validar peças.
- `tools/build_bedrock_packs.py`: gera os dois packs experimentais no diretório `build/`.
- `ENGINEERING_STATUS.md`: resultados efetivamente verificados, limites, riscos e links dos artifacts de CI.

**Proibido declarar 14 mods concluídos com base apenas em arquivos .geo.json:** é preciso converter e validar as animações, sistemas, AI, biomas, dimensões, multiplayer e comportamento no dispositivo. Continue completando o backlog em pequenos commits, preservando os upstream submodules.

## Cataclysm, Xaero, Distant Horizons

1. Use o submódulo Cataclysm oficial em mods/43-cataclysm/upstream, não invente modelos: tools/cataclysm_batch_to_bedrock.py já recupera 41 modelos de entidades com Citadel Java.
2. Xaero: importar os waypoints a partir do backup existente usando tools/xaero_waypoint_import.py; sem UI de minimapa nativo ainda.
3. Distant Horizons: auditar o GitLab com tools/distant_horizons_source_audit.py; tools/distant_horizons_lod.py produz apenas dados de altura multirresolução offline.
4. Manter a coluna de limites e o status factual em ENGINEERING_STATUS.md; não declarar port integral com base em geometria estática.
