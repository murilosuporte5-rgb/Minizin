# Minizin — checkpoint de integração

O ciclo atual integrou o runtime funcional do Aether, corrigiu a regressão de Waystones em chunks distantes, ampliou os poderes Origins com base nos JSON Java fixados, adicionou profissões persistentes do MCA, fechou os tiers/receitas do RFTools, ampliou a fronteira segura do Carry On, corrigiu os slots de acessórios do Aether, recuperou receitas vanilla/tier de ferramentas do Aether e integrou os Swets, Sentry e Whirlwinds derivados do branch de mundos.

## Pacote gerado

- `Minizin_Todos_Juntos_Correcao_Mobile_v0.2.2.mcaddon` (candidato v40)
- SHA-256: `0e087a835ac83a46ee15bf4a00b862cce12f12c331e39a49ea61e2dae4561210`.
- Estruturalmente: 43 entidades, 375 blocos, 31 scripts, 48 animações e 8 sons.
- ZIP externo e os dois `.mcpack` internos íntegros.
- Aether no pacote: 21 estruturas `.mcstructure`, 21 entidades (16 modelos convertidos, 3 rigs Slime vanilla e 2 atores procedurais de partículas) e scripts de dimensão, biomas, loot, bosses e fauna. Ice and Fire: 3 dragões montáveis e 3 ovos incubáveis. Cataclysm/Mowzie: adapters de ataques específicos para quatro bosses.
- Aether: 59 itens/material com ícones originais, 32 acessórios e 8 posições virtuais correspondentes às categorias Java; 106 receitas vanilla/stonecutter/fornalha convertidas (22 stonecutting, 9 smelting e 9 blasting); ferramentas usam durabilidade/dano/encantabilidade dos tiers Java; mundos do protótipo que usavam a mão secundária são migrados automaticamente. Ice and Fire agora expõe também as 32 peças canônicas de armadura Java (8 materiais × cabeça/pescoço/corpo/cauda), com ícones originais, pilha 1, nomes PT-BR e preservação de slot no runtime; o overlay 3D da armadura ainda não foi validado no cliente Bedrock.
- Dependência de script: `@minecraft/server` `beta`, exigida pelo registro de dimensão customizada atual. O guia oficial do Custom Dimension API também exige Beta APIs para essa superfície.
- Correção v37: o entrypoint combinado ficou idempotente (um único import de `item_actions.js`) e o runtime Waystones é recopiado do código canônico em cada reconstrução; o pacote continua com `beta` porque o Aether usa `registerCustomDimension`.
- Correção v38: adicionados quatro pergaminhos Waystones baseados nas classes Java `BlankScrollItem`, `BoundScrollItem`, `WarpScrollItem` e `ReturnScrollItem`; o vínculo persiste ID/nome no item, usa os ícones Java originais e só consome após teleporte aceito.
- Correção v40: o runtime combinado agora sincroniza o poder Java `shulker_inventory`: nove espaços persistentes, preservação de metadados e round-trip testado; a abertura usa `!origins inventario`/`!origins shulk` porque a API Bedrock não permite adicionar uma aba nativa ao inventário.
- Bundle independente: `Minizin_Independent_Packs_2026-10-12.zip`, com 11 `.mcaddon` e os dois `.mcpack` do Sophisticated Backpacks; SHA-256 `e12f499711237474686cc8b53205d6948acf2e2098b8999d8a851b85a6bac5b5`.
- Pack independente atualizado de criaturas: `Minizin_Creatures_Research.mcaddon`, SHA-256 `c5f7a2c24f47fa8935a3626ee8430576e3ff268ab92b4034d55a229ab9e4b41c`; inclui os 32 itens canônicos de armadura gerados dos ícones Java originais e as chaves PT-BR para itens e ovos geradores.

## Evidência executada

- 33 testes Python do diretório `tests`: PASS.
- 28 testes Python de `bedrock/worlds/tests`: PASS.
- 46 testes JavaScript: PASS.
- `node --check` em todos os scripts do BP final: PASS.
- Validação estrutural final: PASS.
- Origins: ciclo v40 testado com 5 testes direcionados; além dos poderes adaptados anteriores, o inventário Shulk de 9 espaços preserva item real e metadados em round-trip. Phasing, elytra real, restrições de armadura/alcance e os demais poderes ainda continuam explicitamente pendentes.
- MCA: profissões Java `none`, `guard`, `archer`, `outlaw`, `adventurer`, `mercenary` e `cultist` podem ser escolhidas e ficam persistidas no NPC; guarda/arqueiro têm defesa adaptada contra monstros. Comércio, roupas e rotinas Java completas continuam pendentes.
- RFTools: Machine Frame, gerador, Power Cell normal/simple/advanced/creative e seis receitas derivadas dos recursos Java estão no candidato; o runtime migra o estado `v2` e limita transferência pela capacidade de cada tier. A unidade continua sendo Minizin, não Forge FE.
- Carry On: a whitelist efetiva foi ampliada para blocos vanilla comuns, com portas, camas, portais, líquidos, plantas não transportáveis e entidades críticas bloqueados conforme a blacklist Java; estruturas e estados continuam persistentes e a duplicação permanece bloqueada em escrita incerta.

## Limite honesto

O pacote ainda não foi instalado/executado em um aparelho Android nesta sessão. Renderização, carregamento real, FPS, memória, multiplayer e compatibilidade com a versão específica do Bedrock continuam pendentes de teste no dispositivo. A matriz completa está em `docs/FUNCTIONALITY_MATRIX.md`.
As referências visuais `Minizin_Referencias_Visuais_Java_para_Codex.md` não foram encontradas no filesystem nesta execução; portanto, nenhuma comparação imagem-a-imagem foi declarada como concluída.
