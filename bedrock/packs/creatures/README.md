# Minizin Creatures — escopo isolado (experimento, não equivalência ao Java)

Base GitHub `main` em 12/10/2026. O rótulo **v0.2.8** não está publicado como release/tag nesta base, logo não foi validado como ponto de partida. Mudanças limitadas a `bedrock/packs/creatures/`, testes exclusivos e workflow novo.

## Implementado no código, não verificado dentro do Android
- **Ice and Fire:** BP de três dragões (fogo/gelo/raio), idades/estágios 25/50/75/100 dias conforme `EntityDragonBase.getDragonStage`; dono persistente, alimentação, montaria a partir do estágio 3, modo voo acionado, ataque de mordida, cauda, asa e três efeitos elementais distintos. Animador de poses Tabula `BaseMale/Bite/Tail/WingBlast/AttackStream/AttackBlast/Flight` com delta de rotação por osso, **interpolação experimental**, não animação Java exata. Um subconjunto de 8 áudios OGG originais é incluído **apenas no build local** com autorização, sem assets binários no commit. Armadura aplica proteção Bedrock de 2 a 8 pontos pelo número de peças (sem camada visual); ovos de fogo/gelo/raio com modelos reconstruídos a partir dos 4 cubos do Java e PNG originais; incubação por condição de fogo/água/chuva (aproximação de blocos e clima).
- **Alex's Caves:** Atlatitan com barra de recarga, montaria temporária após Serene Salad, pisão telegráfico, chute e cauda; implementação simplificada do Java (sem destruição da ring de blocos).
- **Mowzie's Mobs:** sistema experimental de Bluff (preparação de 11 ticks, queda, fissura direcionada, recuperação de 34 ticks) aplicado a `minizin:bluff` do BP/RP já existente, sem substituir rig e textura; fissura não usa mesh/partículas do Java.
- **Cataclysm:** Ignis com fases 0/1/2 baseadas em 2/3 e 1/3 de vida, transições (68/120 ticks), escudo, varredura de alma e golpe final de área simplificados; sem todos os golpes, drops, música ou arenas do Java.

**Atenção:** `BP/` contém entidades de pesquisa, mas **não pode ser usado sozinho**, pois novos mobs ficarão sem textura/modelo. O script de build interrompe a montagem se faltar qualquer arquivo original. Nunca declare mobs prontos por existirem definições BP.

## Montar localmente com recursos originais

1. `git submodule update --init --recursive`
2. Obter `generated/conversions` da branch `generated-bedrock`, **sem commit dos assets na feature**: `git fetch origin generated-bedrock && git restore --source origin/generated-bedrock --worktree -- generated/conversions`
3. Com autorização documentada de adaptação/redistribuição de **todos** os recursos usados: `python bedrock/packs/creatures/build_creatures.py --authorized-assets`. O arquivo fica em `build/Minizin_Creatures_Research.mcaddon` e contém quatro `.mcpack` internos, dois para criaturas e dois para Mowzie.
4. Importar numa cópia do mundo; ativar RP/BP de criaturas e RP/BP de Mowzie; capturar **Content Log**, screenshots, FPS/RAM, versão Bedrock e comparar animações/UV com o Java.
5. `node --test tests/creatures_logic.test.mjs`; `node --check bedrock/packs/creatures/BP/scripts/*.js` (checks sintáticos sem execução Minecraft).

## Comandos de inspeção / teste
`/summon minizin_creatures:fire_dragon`, `/summon minizin_creatures:ice_dragon`, `/summon minizin_creatures:lightning_dragon`, `/summon minizin_creatures:atlatitan`, `/summon minizin_creatures:ignis`, `/summon minizin:bluff`.

O criativo fornece os itens de pesquisa. Itens de ovo são posicionados pelo toque; ovos de fogo requerem fogo/fogueira, de gelo precisam estar submersos para congelar (probabilidade 1/500 por tick Java (probabilidade ajustada ao polling de 20 ticks)), e de raio requerem chuva e céu visível. Tempo de incubação: 7200 ticks configurados no Java; o rastreio do clima Bedrock depende de getWeather (API preliminar)/weatherChange. Dragões adultos derrubam escama original em quantidade experimental. Interaja com dragão usando `creative_dragon_meal` para domar e `dragon_meal` para crescer; `dragon_armor_iron` muda apenas estado; mão vazia monta estágio >=3. `dragon_flute` em montaria dispara ataque; agachar com flauta alterna voo (controle mobile **não idêntico ao Java**, sujeito à API de itemUse). Serene Salad no Atlatitan libera montaria. Os controles de pisão do Atlatitan e a postura voadora estão em desenvolvimento; não são anunciados como funcionais.

## Proveniência
Ice and Fire: `02b2922003cbce3c67dad55dfea79acf1721e0db` (EntityDragonBase.java); Alex's Caves: `4718f4287c65b810aecb211789b45f54d405a94d` (AtlatitanEntity.java); Cataclysm: `819937203e22b4fa72fdeccc6c56ad415d65eeef` (Ignis_Entity.java); Mowzie: `7aa17309337cbd4102efc418cba12a4983b1540c` (EntityBluff.java). Os recursos permanecem sob as licenças de seus autores. **O build exige permissão explícita**, pois Cataclysm usa CC BY-NC-ND, Mowzie reserva direitos e outras licenças podem separar código/assets.

## Gates pendentes
Correspondência exata do bloco 'egg in ice', renderização e variações dos 12 ovos, escala/collision box dinâmica, sela/overlay de armadura, inventário, ataques/partículas 1:1, bosses adicionais, fases completas, drops/loot, IA de grupo, biblioteca de áudio total e eventos de áudio adicionais, caverns/worldgen, persistência/streaming multiplayer e benchmark real Android. Bedrock Script API não executa Citadel/GeckoLib/LLibrary/Forge; interpolar poses não substitui motores Java.

## Correções de API para controles mobile

Versão mínima da variante de criaturas: **Bedrock 1.21.90**, por requerer `minecraft:input_air_controlled` na montaria em voo. O BP usa `minecraft:input_ground_controlled` em montarias terrestres. Itens de controle são registrados via `system.beforeEvents.startup` + `minizin_creatures:activate` e despachados com deduplicação entre `onUse`, `onUseOn` e `itemUse`; builds anteriores não garantiam callbacks de uso. A escala visual/colisão dos cinco estágios é experimental, configurada por eventos de componente Bedrock, e ainda não equivale precisamente às caixas Java.

## Umvuthi/Umvuthana — expansão em desenvolvimento

Origem: Mowzie `EntityUmvuthi.java` 150 HP, poderes `Sunstrike`, `Solar Flare`, `Solar Beam`, `Supernova` (abaixo de 60% HP) e invocação de Umvuthana; arquivos reais `geo/*.geo.json` (118/70 bones), `animations/*.animation.json` e `textures/entity/*.png` são importados pelo builder. AI escrita em Script API e timers têm adaptações; **não é reprodução 1:1 do Java**.

## Validação estrutural ampliada

`python bedrock/packs/creatures/build_creatures.py --validate-only` monta **temporariamente** os quatro `.mcpack`, verifica que os 10 IDs BP possuem client_entity, modelos e PNG reais, confere referências de animação e manifestos e apaga os arquivos. Não publica pacotes. Teste em Bedrock Android continua necessário.

## Cataclysm — Ender Guardian

Novo boss com geometria original `Ender_Guardian_Model.geo.json`, PNG original, escudo/helmetless em 50% HP e seleção de cinco habilidades diferenciadas do Java: Stomp (48/83 ticks), Black Hole (62), Mass Destruction (75), Uppercut (100/120), Burst (53) e Rocket Punch (58). `ender_guardian.js` implementa ataques e cooldowns. **A modelagem de frames Java de renderização não foi convertida; animações visuais ainda não são equivalentes**. Fonte: `Ender_Guardian_Entity.java` no commit Cataclysm fixado no README.
