# Minizin — checkpoint de integração

O ciclo atual integrou o runtime funcional do Aether, corrigiu a regressão de Waystones em chunks distantes, ampliou os poderes Origins com base nos JSON Java fixados, adicionou profissões persistentes do MCA, fechou os tiers/receitas do RFTools e ampliou a fronteira segura do Carry On.

## Pacote gerado

- `Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon`
- SHA-256: `09692c383e26541d0cf54fb7a61a931c8959a9160762914f8ef33543c121a69f`
- Estruturalmente: 38 entidades, 375 blocos, 29 scripts, 42 animações e 8 sons.
- ZIP externo e os dois `.mcpack` internos íntegros.
- Aether no pacote: 21 estruturas `.mcstructure`, 16 entidades/modelos e scripts de dimensão, biomas, loot, bosses e fauna. Ice and Fire: 3 dragões montáveis e 3 ovos incubáveis. Cataclysm/Mowzie: adapters de ataques específicos para quatro bosses.
- Dependência de script: `@minecraft/server` `beta`, exigida pelo registro de dimensão customizada atual.
- Bundle independente: `Minizin_Independent_Packs_2026-10-12.zip`, com 11 `.mcaddon` e os dois `.mcpack` do Sophisticated Backpacks; SHA-256 `e12f499711237474686cc8b53205d6948acf2e2098b8999d8a851b85a6bac5b5`.

## Evidência executada

- 31 testes Python do diretório `tests`: PASS.
- 26 testes Python de `bedrock/worlds/tests`: PASS.
- 40 testes JavaScript: PASS.
- `node --check` em todos os scripts do BP final: PASS.
- Validação estrutural final: PASS.
- Origins: novo ciclo testado com 3 testes direcionados; imunidade a fogo, vulnerabilidade à água, efeitos aquáticos, queda lenta, salto felino, resistência/pressa, invisibilidade condicional e escalada/teia adaptadas estão no candidato. Phasing, inventário extra e elytra real continuam explicitamente pendentes.
- MCA: profissões Java `none`, `guard`, `archer`, `outlaw`, `adventurer`, `mercenary` e `cultist` podem ser escolhidas e ficam persistidas no NPC; guarda/arqueiro têm defesa adaptada contra monstros. Comércio, roupas e rotinas Java completas continuam pendentes.
- RFTools: Machine Frame, gerador, Power Cell normal/simple/advanced/creative e seis receitas derivadas dos recursos Java estão no candidato; o runtime migra o estado `v2` e limita transferência pela capacidade de cada tier. A unidade continua sendo Minizin, não Forge FE.
- Carry On: a whitelist efetiva foi ampliada para blocos vanilla comuns, com portas, camas, portais, líquidos, plantas não transportáveis e entidades críticas bloqueados conforme a blacklist Java; estruturas e estados continuam persistentes e a duplicação permanece bloqueada em escrita incerta.

## Limite honesto

O pacote ainda não foi instalado/executado em um aparelho Android nesta sessão. Renderização, carregamento real, FPS, memória, multiplayer e compatibilidade com a versão específica do Bedrock continuam pendentes de teste no dispositivo. A matriz completa está em `docs/FUNCTIONALITY_MATRIX.md`.
As referências visuais `Minizin_Referencias_Visuais_Java_para_Codex.md` não foram encontradas no filesystem nesta execução; portanto, nenhuma comparação imagem-a-imagem foi declarada como concluída.
