# Cataclysm — engenharia reversa de recursos

Fonte **corrigida e confirmada**: https://github.com/lender544/new1.20.1 no commit `819937203e22b4fa72fdeccc6c56ad415d65eeef`. É o código do próprio Cataclysm (pacotes `com/github/L_Ender/cataclysm`), embora também dependa de Lionfish API. Não é correto classificá-lo como *apenas Lionfish API*.

Árvore do commit: **70 modelos de entidades Java**, **236 PNG em `textures/entity`**, **34 arquivos Java de animação**, **188 estruturas NBT**, **232 áudios OGG** e **536 modelos JSON**. Não foram encontrados modelos Blockbench `.bbmodel` nessa árvore.

Conversão publicada: `tools/cataclysm_batch_to_bedrock.py` reutiliza `tools/citadel_java_to_bedrock.py` para os modelos de geometria `AdvancedModelBox`, incluindo os métodos de rotação `setRotateAngle` e `setRotationAngle`. Arquivos Java que usam `ModelPart`/`LayerDefinition` precisam de conversor específico e são marcados `skipped`, não falsamente concluídos.

Execução e arquivo de saída: [Cataclysm Java → Bedrock](https://github.com/murilosuporte5-rgb/Minizin/actions/workflows/cataclysm-convert.yml).

**Limitações:** rig estático recuperado, mas nenhuma IA/efeito/animação original foi portada ainda. A licença declarada no upstream é **CC BY-NC-ND 4.0**, e o site oficial reserva direitos sobre assets: autorização específica para adaptação e distribuição precisa ser preservada antes de liberar mods derivados publicamente. Código e modelos referenciados pelo repo original, não republicados como upstream dentro de Minizin.
