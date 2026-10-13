# Minizin v0.3.0 — binário EXATO testado no Android (reprodução de defeitos)

**LEIA ANTES DE CORRIGIR:** a versão testada pelo usuário NÃO é o build mais novo de `integration/kuroko-minizin-20261012`. O arquivo **exato** testado precisa ser analisado, sem supor que seu conteúdo é idêntico ao último commit. O usuário possui esse arquivo e pode anexá-lo diretamente à sessão Codex.

## Identificação inequívoca do arquivo real

- Nome: `Minizin_Integrado_v0.3.0_68_Biomas_TESTE.mcaddon`.
- **SHA-256 do binário exato:** `3d54880c63cafa980abb697ff296e0fb623949dd3443d60bd1149fe1282f3360`.
- Tamanho aproximado: 2,59 MB.
- Archive externo ZIP: íntegro; contém **somente** `Minizin_v030_BehaviorPack.mcpack` e `Minizin_v030_ResourcePack.mcpack`.
- Manifestos de ambos os packs: versão `[0,3,0]`; `min_engine_version: [1,26,50]`.
- Behavior Pack: 760 arquivos de `items/`, 372 `blocks/`, 25 `entities/`, 69 `biomes/` (68 BOP mais Aether), 47 arquivos `scripts/`, 15 `recipes/`.
- Resource Pack: 1.213 recursos de `textures/`, 435 modelos em `models/`, 68 `biomes_client/`, 25 definições `entity/`, 29 `animations/`.
- Fontes da integração: v0.2.9 experimental e os 68 biomas adicionais do PR #4. NÃO presumir que toda a evolução posterior do PR #6 já está presente nele.
- Variante de diagnóstico: `Minizin_Integrado_v0.3.0_COMPAT_SEM_68_BIOMAS.mcaddon`, SHA-256 `1117aee09d43f06534dcb92e67775d8ef0cc2a1e12109b7a448d4c4ce8bd5fde`; não instalar simultaneamente.

## Defeitos observados pelo usuário EM JOGO (sete capturas Android no chat)

1. **Ícones de itens invisíveis**: células aparentemente vazias, embora haja IDs; pelo menos `item.minizin_creatures:dragon_armor_iron` aparece como nome técnico.
2. **Localização incorreta**: `item.minizin_aether:holystone_shovel` também aparece como chave técnica em vez de nome.
3. **Waystone invisível como bloco**: o visual do bloco não aparece adequadamente; conferir aliases, geometria do JSON de bloco x `.geo.json`, atlas, texturas, item no inventário e entidade cliente.
4. **Waystone aparece como entidade/ovo**: o marcador legado do protótipo está exposto visualmente na experiência Criativo; a solução principal deve ser um bloco, preservando migração e destinos.
5. **Aether duplica portal de saída em várias ilhas**, em vez de controlar spawn dos retornos vinculados a entradas válidas; os screenshots mostram diversas ilhas pequenas e portais repetidos.
6. **Portal Aether com visual errado**: interior escuro semelhante a painéis negros/obsidian, sem a superfície azul fiel ao Java.
7. **Mochilas não localizadas** pelo usuário; verificar presença no creative menu e por comando, nome, ícone, componente e interface, sem pressupor que ausência de descoberta prova ausência de definição.
8. **Poucos itens funcionam na prática**, apesar de presentes no catálogo; a causa exata ainda depende de logs.
9. **Novos biomas BOP não identificados** durante exploração limitada; NÃO declarar que os 68 geram corretamente apenas por existirem definições JSON.

A dimensão Aether, seus terrenos/ilhas e alguma interação de teleporte **funcionaram parcialmente** no dispositivo — preservar essas capacidades.

## Protocolo do Codex

1. Obter o **próprio arquivo `.mcaddon` anexado pelo usuário à sessão**, verificar SHA-256 acima. **Não há URL pública do binário neste GitHub.**
2. Extrair os dois `.mcpack` e reproduzir referências BP → RP, por ID. Examinar conteúdo PNG, UV, geometria, animação e `texts/pt_BR.lang`.
3. Relacionar cada defeito às evidências das sete capturas do usuário; conferir `docs/visual-references/README.md` para comparação com o mod Java original.
4. Aplicar correções no código-fonte do projeto, não só no pacote gerado; reconstruir, comparar inventário de recursos do binário anterior e do novo e proteger contra regressões.
5. Testar JS, JSON, manifests, referências e modelos. **Teste Android real continua pendente** até o usuário executar uma nova versão e registrar Content Log/capturas.
6. Não divulgar o binário contendo eventuais assets de terceiros num release GitHub público sem auditoria dos direitos de redistribuição.

**Critério de aprovação:** verificar no Android os modelos e ícones corretos, nomes localizados, Waystone bloco 3D (sem spawn egg legado visível), mochila utilizável, portal visualmente semelhante ao Java e sem duplicação em ilhas não vinculadas; encontrar biomas legítimos de forma reproduzível; documentar as diferenças técnicas remanescentes.
