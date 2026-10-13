# Minizin — relatório de defeitos Android e integração da interface Aether (13/10/2026)

> **ATENÇÃO Work/Codex:** novos registros reais de jogador no **Minecraft Bedrock Android**, capturados nesta conversa e descritos abaixo. **A versão exata do .mcaddon testado ainda não foi identificada**. Logo, não atribuir regressão à branch mais recente nem dizer que foi corrigido sem instalar e testar **o binário de mesmo SHA**.

## Constatações das nove capturas Android (arquivos fornecidos pelo usuário)

| Severidade | Evidência observada / relatada | Como verificar antes de corrigir |
|---|---|---|
| **P0 — Portal/dimensão** | Dois pórticos de **glowstone com água escorrendo e inundando** o chão. Não se vê superfície ativa de portal; jogador relata que a dimensão do Aether não funcionou. | Nova cópia do mundo, BP/RP corretos, experimentos/Beta APIs, log da criação/colisão de portal, `registerCustomDimension`, import do entrypoint, colisão/detecção da superfície, teleporte ida/volta. Água vanilla não comprova ativação do portal. Verificar também que retorno não se multiplica. |
| **P0 — Waystone** | Usuário relata que Waystone não opera e seu **item/bloco na hotbar é visualmente ruim** (ícone cinza com padrão de grade e render na mão). A captura não comprova qual ID foi colocado no mundo. | Testar `minizin:andesite_waystone_block` efetivamente colocado, geometria/material_instances, ícone/item de colocação, custom block components, interação, registro de destino, teleporte entre chunks e retorno; não confundir com entidade legada ou item decorativo. |
| **P0 — Sophisticated Backpacks** | Mochila presente na hotbar, mas usuário relata que **não abre/não funciona**; não há tela funcional de armazenamento mostrada. | Validar ID de mochila, import do runtime item-bound, evento de uso/ação mobile, `@minecraft/server-ui`, associação de ID persistente por item, capacidade 27/54/81, teste retirar/guardar e reconectar. Evitar deduzir funcionamento pelo ícone. |
| **P1 — Criaturas** | Capturas mostram modelos visivelmente anômalos: um **baú sobre pernas compridas**, criatura rosa com duas hastes amarelas, criatura preta semelhante a coluna/martelo e figura verde com torso roxo. Relato: mobs invisíveis e incompletos. | Identificar precisamente cada `typeId` via comandos/script e Content Log; conferir geometria de origem, pivôs, hierarquia de bones, escalas, UV e render_controllers, animações, texturas RGBA. **Não inventar identificação pelo screenshot** ou aplicar modelo genérico. |
| **P1 — Itens invisíveis** | Pelo menos um slot do Criativo é **quadrado lavanda vazio**; outras miniaturas podem estar com atlas incorreto. | Para cada `minecraft:item`, resolver `minecraft:icon` -> `RP/textures/item_texture.json` -> PNG real/alpha; gerar diagnóstico de IDs ausentes e screenshot in-game. |
| **P1 — Localização** | Tooltip mostra texto técnico `item.minizin_aether:gravitite_axe` e `item.spawn_egg.entity.minizin_aether:whirlwind.name`. | Conferir PT-BR/EN-US, `RP/texts/languages.json`, arquivos `.lang` **na raiz `RP/texts`**, caminho de chave/identificador de `minecraft:display_name` e spawn egg; confirmar a versão em que `.lang` foi mesclado (commit v0.3.8). Não marcar fechado só porque as chaves constam no JSON. |
| **P1 — Aether acessórios/inventário** | O jogador quer 8 espaços ao lado do avatar **na tela do inventário**, e uma interface próxima do Java. No Work há backend com 2 anéis, pingente, luvas, capa, escudo e 2 relíquias, mas o menu é `ActionFormData`. | Patch experimental `tools/minizin_inventory_accessories_ui.py` desta branch exibe guia visual discreto nas telas desktop/Pocket, com menu funcional do backend. **Não são slots nativos clicáveis do Bedrock**; testar escala/posição, coexistência com outros RP e fluxo sem novo item na hotbar. |
| **P1 — Qualidade UI** | Interface visual dos mods está distante da apresentação Java, e item Waystone pode ocupar visualmente a hotbar. | Diferenciar HUD/hotbar vanilla de GUI do mod: ajustar ícones/modelos e interfaces onde APIs permitem; **não** esconder informação, quebrar o inventário vanilla ou adicionar botões fictícios como se fossem funcionais. |

### Capturas fornecidas
Nove screenshots Android originais apresentados pelo usuário, nomes locais: `1000387084.jpg`, `1000387076.jpg`, `1000387080.jpg`, `1000387078.jpg`, `1000387092.jpg`, `1000387082.jpg`, `1000387074.jpg`, `1000387070.jpg`, `1000387072.jpg`. **Os binários das imagens permanecem na conversa do usuário, não neste repositório.** O Work deve solicitar acesso aos anexos ou trabalhar com este relatório até recebê-los. Não afirmar revisão pixel-a-pixel em CI.

## Ação concreta nesta branch

- Criado instalador **não destrutivo** de painel visual Aether de 8 espaços, `tools/minizin_inventory_accessories_ui.py`, com verificação de runtime existente de 8 posições.
- O backend do Work (`minizin:aether_accessories_v2`) continua sendo responsável por gravar/trocar/retirar acessórios, efeitos e proteção de dados. **O patch não cria outro armazenamento**.
- **Sem novo item Relicário na hotbar**: abrir menu equipado segurando/usando acessório do Aether, ou agachar e interagir com bloco de mão vazia, como já previsto no runtime.
- O painel JSON UI é **somente visual**. `@minecraft/server` não expõe 8 novos slots nativos no inventário via scripts e JSON UI não fornece binding seguro a funções arbitrárias da Script API. Não prometer arrastar/soltar diretamente sobre os desenhos.
- Não publicar .mcaddon com assets Java de terceiros sem revisão de licença/permissões. Esta branch contém apenas código e texto sem arquivos de arte originais.

## Gates de aceite Android (sem falsos positivos)

1. Registrar versão do Minecraft, versão/hash exato do pacote, quais BP/RP foram ativados, experimentos e Content Log.
2. Criar **mundo novo**; conferir dimensões/portais com entrada e saída; garantir que água não vaze e que portal de retorno não multiplique em ilhas.
3. Colocar Waystone real, interagir, registrar, sair da área e teleportar de volta (com relog).
4. Mochila: abrir em Android, guardar/retirar 3 itens distintos, usar filtro, ordenar, ampliar 27→54→81 se aplicável, fechar/reabrir mundo e confirmar persistência sem duplicação.
5. Criaturas: invocar **cada ID individualmente**, capturar renderização frontal/lateral, animação e Content Log; não apenas contagem de entidade JSON.
6. Exportar lista de itens com atlas faltando e nomes `item.*` não traduzidos; cruzar PT-BR no inventário real.
7. Testar tela de acessórios em Pocket com diferentes escalas e confirmar que ações de equipar/remover continuam preservando encantamentos.

**Estado correto:** defeitos `REPORTADOS/OBSERVADOS`, não `CORRIGIDOS`. O sucesso de GitHub Actions (JSON, sintaxe, empacotamento) **não valida Android**.

### Integração recomendada ao Work

- Revisar primeiro e integrar via cherry-pick/PR, sem sobrescrever branch `work/minizin-final-20261013`.
- Verificar se defeitos já foram corrigidos no candidato v0.3.8 antes de refazer código; screenshots podem corresponder a versão anterior.
- Após revisão, montar novo candidato com SHA e usuário testar. Não publicar arte de terceiros sem licença.
