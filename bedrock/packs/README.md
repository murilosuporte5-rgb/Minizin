# Minizin packs — protótipos de reutilização

Este diretório tem códigos e modelos de referência: **ainda não testados dentro do Minecraft Bedrock Android**.

- **Waystones:** geometria de 9 cubos convertida dos modelos Java de `andesite_waystone_bottom`/`top`, PNG do projeto original, entidade interativa e Script API para ativar e teletransportar. Não implementa todos os itens, receitas, custos, permissões e regras do Waystones Java.
- **Mowzie Bluff:** geometria `minecraft:geometry` reaproveitada, PNG original, animação idle normalizada de `Math.` para `math.`, comportamento de caminhada simples; ataques e IA originais NÃO portados.
- **Licenças:** recursos de Waystones e Mowzie's Mobs originalmente *All Rights Reserved*. O usuário informou possuir autorização de adaptação; confirmar e arquivar autorização explícita para divulgação pública antes de distribuir esses arquivos.
- **Teste obrigatório:** importação RP/BP, console de erros, textura correta, escala, UV, animação, uso por toque, persistência, teleportes seguros, multiplayer e FPS.

## Build
```bash
python tools/build_bedrock_packs.py waystones
python tools/build_bedrock_packs.py mowzie
```
Os ZIPs `.mcaddon` são gerados em `build/` (ignorado pelo Git). Importe-os no Minecraft, ative ambos os packs no mundo e use:
```
/summon minizin:andesite_waystone ~ ~ ~
/summon minizin:bluff ~ ~ ~
```
Crie dois marcos Waystone e toque em cada um para ativar. Toque novamente para selecionar o destino. Não use mundos importantes antes de testar em uma cópia.

## Origem / atribuição
- Waystones © BlayTheNinth: https://github.com/TwelveIterations/Waystones
- Mowzie's Mobs © Bob Mowzie / pau101: https://github.com/BobMowzie/MowziesMobs-Public
