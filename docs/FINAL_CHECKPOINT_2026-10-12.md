# Minizin — checkpoint de integração

O ciclo atual integrou o runtime funcional do Aether, corrigiu a regressão de Waystones em chunks distantes, ampliou os poderes Origins com base nos JSON Java fixados, adicionou profissões persistentes do MCA e fechou os tiers/receitas do RFTools.

## Pacote gerado

- `Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon`
- SHA-256: `48b1f09892916ea9f5ce9a90edce5958107cd348a7ebbc72c4e9de1d1330090a`
- Estruturalmente: 38 entidades, 375 blocos, 29 scripts, 42 animações e 8 sons.
- ZIP externo e os dois `.mcpack` internos íntegros.
- Aether no pacote: 21 estruturas `.mcstructure`, 16 entidades/modelos e scripts de dimensão, biomas, loot, bosses e fauna. Ice and Fire: 3 dragões montáveis e 3 ovos incubáveis. Cataclysm/Mowzie: adapters de ataques específicos para quatro bosses.
- Dependência de script: `@minecraft/server` `beta`, exigida pelo registro de dimensão customizada atual.
- Bundle independente: `Minizin_Independent_Packs_2026-10-12.zip`, com 11 `.mcaddon` e os dois `.mcpack` do Sophisticated Backpacks; SHA-256 `786c7b228607a7554d5eb6508d84f01e19ef280714152ee8807bb4b943c4bdf2`.

## Evidência executada

- 31 testes Python do diretório `tests`: PASS.
- 26 testes Python de `bedrock/worlds/tests`: PASS.
- 39 testes JavaScript: PASS.
- `node --check` em todos os scripts do BP final: PASS.
- Validação estrutural final: PASS.
- Origins: novo ciclo testado com 3 testes direcionados; imunidade a fogo, vulnerabilidade à água, efeitos aquáticos, queda lenta, salto felino, resistência/pressa, invisibilidade condicional e escalada/teia adaptadas estão no candidato. Phasing, inventário extra e elytra real continuam explicitamente pendentes.
- MCA: profissões Java `none`, `guard`, `archer`, `outlaw`, `adventurer`, `mercenary` e `cultist` podem ser escolhidas e ficam persistidas no NPC; guarda/arqueiro têm defesa adaptada contra monstros. Comércio, roupas e rotinas Java completas continuam pendentes.
- RFTools: Machine Frame, gerador, Power Cell normal/simple/advanced/creative e seis receitas derivadas dos recursos Java estão no candidato; o runtime migra o estado `v2` e limita transferência pela capacidade de cada tier. A unidade continua sendo Minizin, não Forge FE.

## Limite honesto

O pacote ainda não foi instalado/executado em um aparelho Android nesta sessão. Renderização, carregamento real, FPS, memória, multiplayer e compatibilidade com a versão específica do Bedrock continuam pendentes de teste no dispositivo. A matriz completa está em `docs/FUNCTIONALITY_MATRIX.md`.
As referências visuais `Minizin_Referencias_Visuais_Java_para_Codex.md` não foram encontradas no filesystem nesta execução; portanto, nenhuma comparação imagem-a-imagem foi declarada como concluída.
