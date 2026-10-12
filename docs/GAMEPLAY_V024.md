# Minizin v0.2.4 — ampliação incremental de gameplay

12/10/2026. Base: v0.2.3 que o usuário executou no Android. As imagens mostram
modelos visíveis e ícones de blocos; não demonstram todas as mecânicas aprovadas.

## Recursos adicionados

- Waystones: modelo/textura existentes; ativação de marcos, destinos conhecidos por
  jogador, teleporte no marco e Warp Stone com menu portátil/cooldown adaptado de 10s.
- Aether: 15 ferramentas (pickaxe/axe/shovel de Skyroot, Holystone, Zanite,
  Gravitite e Valkyrie), 5 espadas, Vampire Blade e 4 anéis. Texturas do upstream.
- Dano, durabilidade, encantabilidade e velocidade base extraídos de
  `AetherItemTiers.java`; espadas com fogo e cura baseados nas classes originais.
- Flaming Sword: 30 segundos de fogo + 4 segundos por nível de Fire Aspect.
  Vampire Blade: cura 1 ponto, limitada à vida máxima. Cooldown de habilidade
  adaptado de 12 ticks; não reproduz o sistema completo de ataque carregado Java.
- Anéis do Aether: interação com bloco troca com a mão secundária. Ice Ring
  congela água de superfície em gelo temporário e consome durabilidade em survival.
  Iron/Golden são acessórios ornamentais na fonte. Zanite está equipável, mas seu
  bônus dinâmico de mineração continua pendente; não é um anel de casamento.

## Identificação do anel

O pacote anterior continha os PNGs `engagement_ring`, `engagement_ring_rg`,
`wedding_ring`, `wedding_ring_rg`, `matchmakers_ring` do MCA. Os dois primeiros
servem para noivado e os dois seguintes para casamento segundo o código Java.
Matchmakers Ring continua pendente. Imagens de anéis parecidos não identificam um
item sem o nome/ID. Nesta versão os anéis do Aether usam `minizin_aether:*_ring`.

Os quadrados rosa/preto identificados correspondem aos PNGs originais
`null_block`, `null_end_stone_alt`, `null_plant` do BOP; não são substituições
genéricas geradas neste trabalho e são preservados.

## Como testar

1. Importar `.mcaddon`, desativar a versão anterior, ativar o único BP e RP.
2. Ferramentas/armas estão no criativo; receitas e aquisição survival ainda pendem.
3. Waystone: `/summon minizin:andesite_waystone`. Interagir para ativar dois marcos;
   interagir novamente para escolher um destino. Warp Stone abre o menu ao tocar
   num bloco, e só lista marcos já ativados.
4. Testar Flaming Sword e Vampire Blade contra mobs. Equipar Ice Ring ao tocar em
   bloco com o anel na mão; andar perto de água sem voar para testar congelamento.
5. Confirmar dano, mineração, desgaste e encantamentos no Android; testar destinos
   bloqueados e descarregados antes de usar Waystones em mundo importante.

## Estado real e pendências

26 itens adicionados. Gate estrutural: 19 entidades, 351 blocos, 24 arquivos JS,
10 clips e 8 sons. 26 testes Python e 16 Node aprovados. Verificação permissiva de
tipos com as declarações oficiais server/server-ui 2.0.0. **Build novo não executado
no Minecraft Android pelo agente.**

Continuam pendentes: receitas, tiers completos de coleta, drops especiais de
Skyroot/Holystone, bônus dinâmico Zanite, elevação Gravitite, alcance Valkyrie,
IA/animações completas de bosses, NPCs/famílias, todos os poderes, worldgen e
dimensão Aether. Cada item novo não representa a conclusão do mod original.

Immersive Portals (render contínuo entre portais), Xaero's Minimap (renderizador
de minimapa) e Distant Horizons (LOD distante) não foram portados. Não anexamos
packs vazios nem declaramos importadores/dados como esses renderizadores.

Fonte e SHA-256 dos PNGs em `EXPANSION_REPORT.json` no diretório do build.
Recursos derivados continuam em `build/`, sem publicação pública de assets.
