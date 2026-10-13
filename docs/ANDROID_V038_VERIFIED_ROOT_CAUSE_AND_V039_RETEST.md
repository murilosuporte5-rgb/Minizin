# Diagnóstico executado sobre o binário v0.3.8 real — Android

**Entrada fornecida pelo usuário:** `Minizin_Integrado_12_MODS_ANDROID_CANDIDATO_v038-1.mcaddon`. SHA-256 confirmado **`77a4b505fd9dd6a09c89e5aa80a1078144b33931dd8d2966ef945f9d8bc92c75`** — corresponde exatamente ao candidato privado v0.3.8 documentado no Work PR #7. Isto comprova o conteúdo da entrada, **mas não a versão que originou cada uma das nove capturas**, se o usuário não confirmar que testou este mesmo arquivo.

## Causas verificadas no pacote v0.3.8

### Aether portal — detecção tardia que permite vazamento
Arquivo: `BP/scripts/aether_full_v3/main.js`.

O código antigo só escutava `world.afterEvents.playerInteractWithBlock` e exigia `event.block.typeId === 'minecraft:glowstone'` **depois** da interação do balde. Se o jogador tocasse o interior ou o líquido fosse colocado antes da detecção, água vanilla poderia escorrer. O frame Java-inspired exige borda 4×5 e interior 2×3.

**Correção implementada no candidato local privado v0.3.9:** `world.beforeEvents.playerInteractWithBlock` com item `minecraft:water_bucket`, `findGlowstoneFrame` no bloco e face adjacente, `event.cancel = true` **somente se a moldura for válida**, `system.run(()=>activateFrame(...))`. A interação normal do balde permanece inalterada longe de um frame válido. Um teste simulado em Node validou 6 substituições por portal e zero derramamentos no cenário. **A dimensão beta e o cliente Android NÃO foram testados.**

### Whirlwinds invisíveis no Overworld
Arquivo: `BP/scripts/aether_full_v3/whirlwinds.js`.

O renderer no v0.3.8 rodava:
```js
const dim = world.getDimension('minizin_aether:sky');
for(const entity of dim.getEntities({type:'minizin_aether:whirlwind'})) { ... }
```

Os dois Whirlwinds são atores **procedurais sem geometria de cliente, por desenho**, e portanto ficam completamente invisíveis quando criados via ovo no Overworld — mesmo que o código do mod esteja funcionando dentro do Aether.

**Correção local:** procurar entidades em Overworld, Nether, End e Aether; animar partículas somente quando houver jogador próximo, preservando comportamento/IA originais adaptados e segurança de exceção por dimensão. Testado **sintaticamente**, não com partículas reais no cliente. Não substituir por cubo/rig falso.

### Mochila — item comum sem caminho independente de uso
Arquivos: `BP/scripts/backpack.js` e `BP/items/backpack.json`.

O código v0.3.8 dependia de `world.afterEvents.itemUse`, além das interações com bloco/entidade. A correção local registra um item custom component `minizin:open_backpack_v039` em `system.beforeEvents.startup`, callbacks `onUse`/`onUseOn` chamando o menu **já existente**, mantendo identificadores e persistência por mochila. A entrega depende de verificação Android do evento no toque, não inferir a partir de CI.

### Waystones — menu com fallback de interação
`BP/scripts/waystones_v2/waystones_block.js`: ao callback de custom block component foi acrescentado fallback de `afterEvents.playerInteractWithBlock`, usando a trava de concorrência original. A entidade legada é preservada para migração, mas seu ovo criativo foi ocultado. Ícone 2D de marcador gerado apenas com pixels da textura original do Waystone; essa mudança visual precisa de reteste.

### Inventário e traduções
- Nomes que faltavam: `item.minizin_aether:gravitite_axe` e `item.spawn_egg.entity.minizin_aether:whirlwind.name` possuem agora aliases `.lang` e `item.namespace:id`; foram adicionadas 986 chaves **por idioma** sem substituir textos originais.
- Interface com guia dos oito espaços Aether é **visual apenas**, sendo equipagem realizada no menu server-ui existente. Foi gerado também um segundo binário **sem patch JSON UI** para fallback se o inventário não abrir.
- Nenhum item do pacote v0.3.8 apresentou **PNG de ícone inexistente, chave de atlas ausente ou textura inteiramente transparente** em auditoria offline (901 itens). Isso não prova que todos são renderizados no Android; Content Log ainda necessário.

## Entregas locais para o usuário
- `Minizin_Integrado_v0.3.9_ANDROID_CORRECOES_TESTE.mcaddon` — SHA-256 `cb5a5c8952eee43ff41193bfea289464f57ced79383c33166ce4e9fe12c2d386`.
- `Minizin_Integrado_v0.3.9_SEM_UI_ANDROID_TESTE.mcaddon` — SHA-256 `214b9007419cfd7b2b3b7baac1c468cb45ea5f0b6b192b41e7b1b1f0aa0fcbc5`.
- Fonte privada: `Minizin_v039_ANDROID_FIXES.py`, processa exclusivamente a entrada cujo hash consta acima. O binário não foi publicado no GitHub por conter arte licenciada de terceiros.

Os dois builds preservam 901 arquivos de itens, 399 blocos, 50 entidades, 50 scripts e os 69 biomas definidos. Ambos passaram sintaxe dos 50 JS, JSON, referências de atlas e integridade ZIP aninhada. **Nenhum dos dois foi executado em Minecraft Android.**

## Trabalho prioritário Work
1. Conferir com o usuário qual versão ele instalou ao tirar as capturas; testar o v0.3.9 ou incorporar correções em nova branch Work sem recomeçar o projeto.
2. **Corrigir e validar no cliente** portal com dimensão, mochila, Waystone, ícones com quadrados vazios, mobs deformados (rig/UV/anim) individualmente.
3. Não chamar modelos de mobs completos sem render real e Content Log; todo item e bloco deve manter atlas/ID antigos; não acrescentar entidades decorativas.
4. Distribuição pública de assets depende de licenças. Os arquivos compilados devem ser enviados privadamente ao usuário.
