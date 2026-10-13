# Etapas 2 e 3 — recursos originais e gameplay incremental

Data: 12/10/2026. **Entrega parcial experimental; não constitui port integral.**

O trabalho recupera `generated/` da branch `generated-bedrock` e os submódulos
fixados do projeto. Não depende de Reinos & Circuitos. Assets derivados permanecem
em `build/`; somente conversores, runtime próprio, testes e este documento são
publicados na branch de código. O pedido autoriza adaptação e entrega ao usuário;
o escopo de redistribuição externa dos recursos proprietários continua desconhecido.

## Implementação

| Pack | Recursos reaproveitados | Mecânicas nesta entrega | Limites |
|---|---|---|---|
| Ice and Fire | 3 rigs Tabula, skins PNG originais, 3 OGG, poses walk/flight/bite | 3 dragões; perseguição, voo adaptado, mordida, sopro com dano, fogo/gelo, cooldown e fase por vida | 9 clips com tempo adaptado; sem domesticação, crescimento, armadura, ovos, todas as criaturas ou IA integral |
| Cataclysm | Ender Guardian, Ignis e Harbinger: geometrias, skins e 3 sons originais | Vida de boss, HUD, perseguição, ataque em área, knockback e fase abaixo de 50% da vida | Modelos estáticos; golpes são adaptação comum, não reproduzem repertório Java |
| Alex's Caves | Rig/skin de Atlatitan e som original de pisão | Caminhada, vida, retaliação com dano em área após ser atacado | Sem animação esquelética, biomas, todas as criaturas ou tamanho/colisão fiel |
| Mowzie's Mobs | Bluff geo, PNG, OGG e idle original com canais GeckoLib adaptados | Movimento, combate e dano em área | Curvas easing aproximadas por interpolação linear; sem demais criaturas/IA original |
| The Aether | 74 geometrias e atlases convertidos existentes | Blocos obtidos no criativo, colocados, quebrados e com loot próprio | Sem dimensão/geração de mundo; variantes separadas, colisões padrão e dureza adaptada |
| Biomes O' Plenty | 275 geometrias e atlases existentes | Blocos colocáveis/mineráveis com loot | Sem geração de biomas, todas as variantes ou propriedades botânicas |
| MCA | 10 NPCs e ícones existentes preservados | Afinidade persistente por jogador, cooldown social, presente consumido e revalidação após formulário | Modelo humanoide anterior simplificado; sem casamento/família/rotina integral |
| Origins | Catálogo, ícones e quatro passivos anteriores | Elytrian: impulso; Enderian: teleporte com espaço livre/chão em whitelist; cooldown | Sem réplica de Apoli, phasing, todos os poderes ou desvantagens |
| RFTools | Modelos/atlases originais de coalgenerator e powercell | Carvão gera energia; transferência a células adjacentes; ferro bruto vira lingote consumindo energia; estado persistente por máquina/dimensão | Sem rede RF, inventário interno nativo, receitas configuráveis ou automação integral |
| Carry On | Pack anterior preservado | Captura e soltura de animais existentes | Não alterado neste trabalho; sem carregar baús/blocos |

## Reprodução

```bash
git submodule update --init --recursive
git fetch origin generated-bedrock
git checkout origin/generated-bedrock -- generated/
python tools/reuse_assets.py scan
python tools/build_creature_world_packs.py --output build/stages23
python tools/build_gameplay_four.py --output build/four_gameplay
python -m unittest discover -s tests
node --test tests/combat.test.mjs tests/java_model_to_bedrock.test.mjs
python tools/validate_gameplay_packs.py build/stages23/iceandfire build/stages23/cataclysm build/stages23/alexscaves build/stages23/mowzies build/stages23/aether build/stages23/biomesoplenty build/four_gameplay/mca build/four_gameplay/carryon build/four_gameplay/origins build/four_gameplay/rftools
```

Os builders exigem diretórios novos para conservar os resultados anteriores.
`REPORT.json` registra caminhos, SHA-256 e commits upstream. IDs dos seis novos
packs usam namespaces distintos `minizin_<mod>:`. Os quatro anteriores preservam
IDs e UUIDs próprios para manter continuidade; não ativar suas versões anteriores
simultaneamente com as novas.

## Verificação executada

- 25 testes Python e 6 testes Node aprovados.
- Gate independente: 10 packs, 18 entidades (8 novas + 10 NPCs anteriores),
  351 blocos (349 + 2 máquinas), 26 arquivos JS, 10 clips e 8 arquivos de áudio.
- JSON, dependências RP/BP, UUIDs, namespaces, texturas, geometria, loot, sons,
  imports internos e sintaxe JavaScript verificados.
- Declarações oficiais `@minecraft/server@2.0.0` e `server-ui@2.0.0` consultadas;
  API `Block.isSolid` indisponível foi removida; chat não é obrigatório para os
  novos controles. Validação de tipos dos novos runtimes em JS com modo permissivo.
- **Minecraft Android não foi executado.** Sem evidência de renderização, FPS,
  temperatura, importação real, robustez multiplayer ou ausência de Content Log.

## Teste no Android

Minecraft com suporte às dependências declaradas, mínimo alvo 1.21.90. Usar mundo
novo e cópia de segurança; importar o `.mcaddon`, ativar seu BP e RP. Cada pack
funciona isoladamente. Não habilitar versões anteriores do mesmo pack.

- Dragões: `/summon minizin_iceandfire:firedragon`, `icedragon`, `lightningdragon`.
- Bosses: `/summon minizin_cataclysm:ender_guardian`, `ignis`, `harbinger`.
- Criaturas: `/summon minizin_alexscaves:atlatitan`; `/summon minizin_mowzies:bluff`.
- Combate é destinado a jogadores em sobrevivência/aventura; testar paredes,
  alcance, fase de vida, retorno ao solo e cooldown. Atlatitan reage a dano.
- Aether/BOP: buscar blocos no criativo; comparar atlas, orientação, slab/top,
  transparência e loot ao quebrar. Não há worldgen nesta entrega.
- MCA: invocar `minizin:mca_male_0`; agachar e interagir com papel; comparar
  afinidade com segundo jogador; presentear esmeralda, sair/reabrir mundo.
- Origins: agachar, livro na mão e interagir com bloco abre escolha; pena na mão
  ativa Elytrian/Enderian ao interagir. Enderian aceita apenas chão vanilla da
  whitelist; confirmar que o teleporte não atravessa paredes.
- RFTools: colocar `minizin_rftools:coalgenerator` e `minizin_rftools:powercell`
  adjacentes; agachar e interagir; abastecer com carvão, verificar transferência,
  processar ferro bruto, relogar e quebrar/recolocar a máquina.

Pendências obrigatórias para completar as etapas: todos os modelos não suportados,
clips/rigs de bosses e Atlatitan, IA fiel, dimensões/biomas, sistemas sociais,
demais poderes, automação RF e validação visual/funcional no dispositivo.
