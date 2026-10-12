# Itens e blocos com PNGs idênticos — fontes originais a recuperar

**Fonte auditada:** `Reinos_e_Circuitos_Ultimate_v2.4.0.mcaddon`, SHA-256 `f0e5139fb1b2b2887e9b5771c4af8099748dce6cefde9b0bb5971d4280bb598e`.

Os nomes na mesma linha abaixo compartilham imagens **pixel a pixel idênticas** apesar de identificadores diferentes:

| Imagem | Arquivos distintos | Estado |
|---|---|---|
| Blocos industriais, grupo 1 | alloy_smelter, battery, cable, conveyor, crusher, electric_furnace, generator, press, shaft | **9 pendentes** |
| Blocos industriais, grupo 2 | monitor, storage_terminal | **2 pendentes** |
| Itens, grupo 1 | atlatitan_sigil, charged_crystal, crystal_beast_sigil, ember_dragon_sigil, frost_dragon_sigil, iron_titan_sigil, origin_talisman, runic_guardian_sigil, storm_dragon_sigil | **9 pendentes** |
| Itens, grupo 2 | beast_fang, copper_dust, copper_plate, gold_dust, inspector, iron_dust, iron_plate, runic_steel, storage_linker | **9 pendentes** |
| Itens, grupo 3 | ember_blade, frost_spear, storm_blade | **3 pendentes** |
| Itens, grupo 4 | runic_hammer, titan_hammer | **2 pendentes** |

**Nota de contagem:** 11 texturas de blocos e 23 de itens representam 34 entradas de textura repetida; o pacote QA separa os recursos afetados e retém os originais no arquivo fonte.

## Reparo autêntico confirmado para um bloco

O repositório original **McJtyMods/RFTools** (commit `030a495c8530183bdfe47475ed41d45386e56f6c`) contém `models/block/storage_terminal.json`. O modelo herda `rftools:block/rftools_logicblock` e referencia texturas `rftools:blocks/machinestorageterminal`, `rftools:blocks/machineside`, `rftools:blocks/machinebottom`. Elas estão presentes como arquivos PNG reais na fonte. O script `tools/rc_build_rftools_storage_terminal.py` usa essas texturas para montar um atlas e geometria Bedrock.

[Pack RFTools de inspeção com os pixels originais](https://github.com/murilosuporte5-rgb/Minizin/tree/qa/reinos-circuitos-v240/qa/reinos-circuitos-v240/verified/rftools/storage_terminal) — **gerado e validado estruturalmente; ainda não testado dentro do Minecraft Android**.

Para os outros 33 recursos, o nome do arquivo local não comprova o modelo original correspondente. A identificação precisa de recurso por recurso e da licença é obrigatória. Não criar quadrados, cores sólidas ou placeholders para cumprir metas.

## Prioridades para Codex

1. Confirmar semelhança da textura real dos três lados do bloco RFTools com screenshot no dispositivo.
2. Corrigir RP/atlas/JSON de cada item com dados autenticados; não trocar o conteúdo de forma global nem atribuir nomes incorretos.
3. Verificar ícone, item na mão, bloco colocado, armadura equipada e animação de entidades separadamente.
4. Preservar `rw:*` da fonte original em backup; não instalar protótipos isolados junto ao pack monolítico.
5. Rodar Content Log no Android v26.51, registrar evidência antes/depois e FPS.
