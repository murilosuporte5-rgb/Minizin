# Minizin Creatures — escopo isolado (experimento, não equivalência ao Java)

Base GitHub `main` em 12/10/2026. O rótulo **v0.2.8** não está publicado como release/tag nesta base, logo não foi validado como ponto de partida. Mudanças limitadas a `bedrock/packs/creatures/`, testes exclusivos e workflow novo.

## Implementado no código, não verificado dentro do Android
- **Ice and Fire:** BP de três dragões (fogo/gelo/raio), idades/estágios 25/50/75/100 dias conforme `EntityDragonBase.getDragonStage`; dono persistente, alimentação, montaria a partir do estágio 3, modo voo acionado, ataque de mordida, cauda, asa e três efeitos elementais distintos. Animador de poses Tabula `BaseMale/Bite/Tail/WingBlast/AttackStream/AttackBlast/Flight` com delta de rotação por osso, **interpolação experimental**, não animação Java exata. Armadura tem estado lógico (sem camada visual); ovo e choco pendentes.
- **Alex's Caves:** Atlatitan com barra de recarga, montaria temporária após Serene Salad, pisão telegráfico, chute e cauda; implementação simplificada do Java (sem destruição da ring de blocos).
- **Mowzie's Mobs:** sistema experimental de Bluff (preparação de 11 ticks, queda, fissura direcionada, recuperação de 34 ticks) aplicado a `minizin:bluff` do BP/RP já existente, sem substituir rig e textura; fissura não usa mesh/partículas do Java.
- **Cataclysm:** Ignis com fases 0/1/2 baseadas em 2/3 e 1/3 de vida, transições (68/120 ticks), escudo, varredura de alma e golpe final de área simplificados; sem todos os golpes, drops, música ou arenas do Java.

**Atenção:** `BP/` contém entidades de pesquisa, mas **não pode ser usado sozinho**, pois novos mobs ficarão sem textura/modelo. O script de build interrompe a montagem se faltar qualquer arquivo original. Nunca declare mobs prontos por existirem definições BP.

## Montar localmente com recursos originais

1. `git submodule update --init --recursive`
2. Obter `generated/conversions` da branch `generated-bedrock`, **sem commit dos assets na feature**: `git fetch origin generated-bedrock && git restore --source origin/generated-bedrock --worktree -- generated/conversions`
3. Com autorização documentada de adaptação/redistribuição de **todos** os recursos usados: `python bedrock/packs/creatures/build_creatures.py --authorized-assets`. O arquivo fica em `build/Minizin_Creatures_Research.mcaddon`.
4. Importar numa cópia do mundo; ativar RP/BP de criaturas e RP/BP de Mowzie; capturar **Content Log**, screenshots, FPS/RAM, versão Bedrock e comparar animações/UV com o Java.
5. `node --test tests/creatures_logic.test.mjs`; `node --check bedrock/packs/creatures/BP/scripts/*.js` (checks sintáticos sem execução Minecraft).

## Comandos de inspeção / teste
`/summon minizin_creatures:fire_dragon`, `/summon minizin_creatures:ice_dragon`, `/summon minizin_creatures:lightning_dragon`, `/summon minizin_creatures:atlatitan`, `/summon minizin_creatures:ignis`, `/summon minizin:bluff`.

O criativo fornece os itens de pesquisa. Interaja com dragão usando `creative_dragon_meal` para domar e `dragon_meal` para crescer; `dragon_armor_iron` muda apenas estado; mão vazia monta estágio >=3. `dragon_flute` em montaria dispara ataque; agachar com flauta alterna voo (controle mobile **não idêntico ao Java**, sujeito à API de itemUse). Serene Salad no Atlatitan libera montaria. Os controles de pisão do Atlatitan e a postura voadora estão em desenvolvimento; não são anunciados como funcionais.

## Proveniência
Ice and Fire: `02b2922003cbce3c67dad55dfea79acf1721e0db` (EntityDragonBase.java); Alex's Caves: `4718f4287c65b810aecb211789b45f54d405a94d` (AtlatitanEntity.java); Cataclysm: `819937203e22b4fa72fdeccc6c56ad415d65eeef` (Ignis_Entity.java); Mowzie: `7aa17309337cbd4102efc418cba12a4983b1540c` (EntityBluff.java). Os recursos permanecem sob as licenças de seus autores. **O build exige permissão explícita**, pois Cataclysm usa CC BY-NC-ND, Mowzie reserva direitos e outras licenças podem separar código/assets.

## Gates pendentes
Ovos, incubação, escala/collision box dinâmica, sela/overlay de armadura, inventário, ataques/partículas 1:1, bosses adicionais, fases completas, drops/loot, IA de grupo, sons OGG, caverns/worldgen, persistência/streaming multiplayer e benchmark real Android. Bedrock Script API não executa Citadel/GeckoLib/LLibrary/Forge; interpolar poses não substitui motores Java.
