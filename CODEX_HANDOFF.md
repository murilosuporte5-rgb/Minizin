# Handoff para Codex — integrar os arquivos Bedrock convertidos

**Fonte do trabalho:** branch `main` com scripts/conversores, branch `generated-bedrock` com arquivos RP/BP originais convertidos e `.mcaddon` experimental.

**Importante:** não há uma versão completa e funcional dos 14 mods. Modelos convertidos não incluem IA, animações, interfaces funcionais nem sistemas de dimensões por si sós. A validação de GitHub Actions é estrutural, não um teste dentro do jogo.

## Copiar os recursos para a branch em que o Codex trabalha

```bash
git fetch origin main generated-bedrock
git switch <sua-branch-de-trabalho>
git checkout origin/generated-bedrock -- generated/
```

Não faça `git reset --hard` na branch do Codex. Revise alterações locais antes de copiar pastas e faça commits pequenos por mod.

## Conteúdo que já existe

- `generated/next_four/BP/` e `RP/`: protótipos de MCA, Carry On, RFTools e Origins (Script API).
- `generated/next_four/Minizin_Next_Four_Prototype.mcaddon`: pacote instalável experimental.
- `generated/next_four/BP/items/`: 375 definições Bedrock de itens com 375 texturas PNG correspondentes (95 MCA, 103 RFTools, 1 Origins, mais 176 itens MCA compostos de camadas).
- `generated/next_four/BP/entities/`: 10 NPCs MCA experimentais; modelo humanoide simplificado e 10 skins compostas de camadas originais.
- `generated/next_four/RP/models/entity/`: 69 geometrias convertidas (1 MCA, 68 RFTools). Material/UV devem ser inspecionados.
- `generated/next_four/original_meshes/rftools/`: OBJ, MTL, BLEND originais sem remodelagem.
- `generated/next_four/original_rules/carryon/`: tags do Java; lógica de captura no BP experimental usa apenas entidades existentes e não transporta baús.
- `generated/conversions/`: saídas anteriores de Ice and Fire (192 poses Tabula), Cataclysm (41), Alex's Caves (Atlatitan), Waystones/Biomes O Plenty/Aether (366 modelos com atlas), mais Xaero/Distant Horizons (dados sem renderizador).

## Gates obrigatórios por mod

1. Compare modelo, materiais, UV e animações no Blockbench, e importe RP/BP num mundo de teste Bedrock.
2. Corrija logs de Content Log e warnings de Script API. Registre qual versão do Bedrock foi usada; versões recentes alteram contratos de APIs.
3. MCA: validar NPC humanoide; conectar os arquivos de skins e interações sociais sem perder relacionamentos.
4. Origins: regenerar `catalog.js` das definições upstream e implementar gradualmente poderes não portados, com efeitos e cooldowns testados.
5. Carry On: testar captura/soltura, relog, multiplayer e perda de conexão, sem duplicação de inventário; suporte a blocos com contêineres ainda não implementado.
6. RFTools: integrar modelos 3D existentes e desenvolver automações/energia com isolamento de estado; não fingir que um ícone representa uma máquina.
7. Modelos grandes: converter rig/animação, testar emissões, colisões e otimização mobile (8 GB físicos não são 8 GB disponíveis ao jogo).
8. Não tentar prometer renderização contínua de Immersive Portals, minimapa Xaero completo ou DH LOD via RP/BP sem APIs nativas.
9. Só liberar como produto após verificar direitos de redistribuição de cada recurso e executar testes em Android real.

## Instrução principal

**PARE de criar modelos do zero enquanto houver modelos, PNG, OBJ, Tabula, BBMODEL ou geometry JSON importáveis.** Converter, validar e reutilizar primeiro. Abra `generated/next_four/converted_resources_report.json` e índices em `generated/conversions/` para saber o que foi recuperado e o que foi rejeitado.
