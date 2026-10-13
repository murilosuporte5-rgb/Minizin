# Minizin — evidências visuais recebidas e correções

As cinco capturas recebidas no ZIP do WhatsApp foram tratadas como evidência observada no cliente Bedrock, não como teste reproduzido nesta sessão.

| Evidência observada | Causa/limite atual | Ação no ciclo v61 | Estado |
|---|---|---|---|
| Chave crua `item.minizin_creatures:dragon_meal` | Mundo/pack antigo usa namespace de criaturas diferente do ID canônico atual `minizin_iceandfire:dragon_meal` | Adicionados aliases de idioma para o namespace legado, sem duplicar o item | Verificado no RP v61; reteste no Android pendente |
| Chave crua `item.spawn_egg.entity.minizin_creatures:atlatitan.name` | Chave gerada por uma versão anterior do spawn egg | Adicionados aliases `.name` e sem `.name` para Atlatitan | Verificado no RP v61; reteste no Android pendente |
| Aviso vermelho “Falha ao carregar pelo menos um pacote…” | O print não contém o log Bedrock nem identifica se a falha foi manifest, API ou script | v65 isola a falha de registro da dimensão Aether: ausência de Beta APIs agora desativa somente o caminho Aether e não aborta os outros módulos; o diagnóstico definitivo ainda exige log do cliente | Mitigação implementada no código; Android/log ainda pendente |
| Waystone visível em uma captura | A captura não prova o período de invisibilidade relatado em outra execução | O bloco real, modelo, textura e migração continuam no runtime v2; a falha temporal exige reprodução no jogo | Parcial; Android pendente |
| Anel/acessório aparece associado à mão secundária/tela vanilla | Bedrock não oferece API pública para adicionar a aba nativa Java | Runtime usa 8 slots persistentes em menu server-side e só migra a mão secundária de mundos antigos | Implementado como adaptação; não é GUI Java 1:1 |
| Armadura do dragão não tinha camada visual sobre o modelo | O runtime registrava defesa/slot, mas o RP só renderizava o corpo-base | v66 adiciona propriedades client-sync dos quatro slots, render controllers por ordinal e 99 PNGs `armor_*` copiados do Ice and Fire Java; v6 replica o mesmo conjunto no pack independente | Implementado nos dois caminhos; renderização Android pendente |

O v66 não é considerado aprovação Android. Para fechar esses itens no aparelho, importar o addon limpo, abrir um mundo novo e um mundo migrado, capturar o log de conteúdo e repetir os cenários de spawn egg, dragon meal, armadura de dragão nos quatro slots, Waystone e acessórios após reconexão.
