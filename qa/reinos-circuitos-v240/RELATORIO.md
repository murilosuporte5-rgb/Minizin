# AUDITORIA E SEPARAÇÃO — REINOS & CIRCUITOS ULTIMATE v2.4.0

Fonte: arquivo .mcaddon enviado na conversa. Versão capturada: v2.4.0. Alvo visual capturado no Minecraft: v26.51.

## Problema comprovado
- 42 itens, 35 blocos, 9 entidades definidos nos Behavior Packs.
- Quatro grupos de texturas de itens repetidas: 23 imagens são cópias pixel-a-pixel entre nomes distintos.
- Dois grupos de texturas de blocos repetidas: 11 arquivos são cópias pixel-a-pixel.
- Zero arquivos de áudio OGG/WAV e nenhuma declaração sound_definitions.json no Resource Pack.
- Caminhos de item_texture/terrain_texture existem: a causa principal dos ícones repetidos é o *conteúdo das imagens*, não os JSON de registro.
- 10 blocos usam minecraft:geometry.full_block, uma geometria **embutida** do Bedrock; não é, por si, um arquivo faltante.

## Pacotes isolados de QA gerados

| Arquivo | Itens com textura não duplicada | Blocos com textura não duplicada | Entidades | Estado |
|---|---:|---:|---:|---|
| aether.mcaddon | 0 | 5 | 0 | Somente teste estático, funcionalidade parcial |
| biomesoplenty.mcaddon | 0 | 5 | 0 | Somente teste estático, funcionalidade parcial |
| waystones.mcaddon | 0 | 1 | 1 | Somente teste estático, funcionalidade parcial |
| mowzies.mcaddon | 0 | 0 | 1 | Somente teste estático, funcionalidade parcial |
| alexscaves.mcaddon | 0 | 0 | 1 | Somente teste estático, funcionalidade parcial |
| dragon_prototypes.mcaddon | 3 | 0 | 3 | Somente teste estático, funcionalidade parcial |
| fantasy_prototypes.mcaddon | 3 | 0 | 3 | Somente teste estático, funcionalidade parcial |
| industrial.mcaddon | 2 | 3 | 0 | Somente teste estático, funcionalidade parcial |
| reinos_core.mcaddon | 11 | 10 | 0 | Somente teste estático, funcionalidade parcial |

## O que foi corrigido na geração de QA
- RP/BP foram separados com manifestos e UUIDs distintos para cada grupo, com vínculo interno de dependência.
- Os recursos comprovadamente duplicados não foram declarados concluídos; ficam listados em AUDIT.json.
- Os registros `item_texture.json`, `terrain_texture.json` e `blocks.json` foram filtrados pelos recursos efetivamente incluídos.
- Foram mantidos modelos, controladores de renderização, animações e texturas das entidades existentes.
- Componentes `rw:*` que dependiam do script monolítico foram removidos dos blocos QA e anotados como funcionalidades pendentes.
- O código de teste dos Waystones e do Bluff foi incluído isoladamente com as dependências locais.
- Foram incluídas receitas somente quando suas referências não introduziam dependências externas ao pack.

## O que ainda não está concluído
- As texturas autênticas dos 23 itens e 11 blocos duplicados ainda exigem identificação e recuperação de fontes oficiais; nada foi inventado.
- Modelos completos e configurações de equipamentos, sons e partículas não estão presentes na fonte enviada.
- Os grupos `dragon_prototypes`, `fantasy_prototypes`, `industrial` e `reinos_core` são material próprio/misto do addon; não equivalem a ports fiéis de Ice and Fire, Cataclysm, RFTools ou MCA.
- Não há confirmação de compatibilidade com Minecraft Bedrock v26.51 no Android. Testar em mundo novo com Content Log.
- Para migração de mundo, os identificadores `rw:*` foram conservados nas definições isoladas; **não ative simultaneamente** o addon original, para evitar conflitos.
- Este recorte não inclui 14 mods completos: apenas classifica recursos realmente presentes no `.mcaddon` enviado.

## Arquivos de diagnóstico
- `AUDIT.json`: texturas repetidas, recursos excluídos, componentes sem runtime e referência de origem.
- `split_and_audit.py`: gerador independente, aceita o `.mcaddon` original como argumento.
- `validate_split.py`: verificador estático de UUIDs, referências RP/BP, caminhos e importações JS.

## Prioridade do Codex
1. Recuperar os PNGs originais dos mods correspondentes com proveniência e autorização; comparar UV e ícones, sem substituições genéricas.
2. Reconstruir um pack completo para cada mod usando fontes originais; somente então registrar gameplay e sons.
3. Abrir no jogo isoladamente, verificar Content Log, inventário, item na mão, bloco posicionado, criaturas, animações, FPS e multiplayer.
4. Só marcar um recurso como `APROVADO` se a verificação visual e funcional passar no Bedrock Android.