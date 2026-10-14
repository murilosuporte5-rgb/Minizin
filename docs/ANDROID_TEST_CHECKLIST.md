# Minizin — teste no Bedrock Android

## Instalação

1. Copie `Minizin_Todos_Juntos_Experimental.mcaddon` para o Android.
2. Abra o arquivo no Minecraft Bedrock e aguarde a importação dos dois packs.
3. Crie um mundo novo de teste. Ative o pack de comportamento e o pack de recursos do Minizin; habilite as APIs experimentais solicitadas pelo cliente.
4. Não use o mundo principal antes de confirmar salvamento, recarregamento e ausência de perda de inventário.

## Smoke test

Registre a versão exata do Minecraft e anexe o Content Log quando algo falhar.

- Entrar, sair e reabrir o mundo.
- Colocar, ativar, renomear e quebrar um Waystone; viajar entre dois destinos.
- Criar uma mochila, guardar/retirar item encantado, fechar o jogo e confirmar a persistência.
- Interagir com NPC MCA, alterar afinidade, noivar/casar e verificar a família.
- Transportar um bloco/entidade Carry On; relogar e confirmar que não houve duplicação ou perda.
- Ligar gerador, cabo, célula e lâmpada RFTools.
- Escolher uma Origin, usar o poder ativo e relogar.
- Invocar dragão, Atlatitan, Ignis, Ender Guardian, Harbinger e Bluff; verificar textura, colisão, som e comportamento.
- Colocar blocos convertidos de Aether e Biomes O’ Plenty.
- Explorar chunks, salvar, morrer e reconectar.

## Desempenho

Anote FPS aproximado, memória exibida pelo Android, tempo de carregamento do mundo, temperatura e qualquer travamento em 5, 15 e 30 minutos. Teste também com o pacote combinado desativado para separar regressões do cliente.

O pacote foi validado estruturalmente, mas não foi executado em um cliente Android nesta sessão. Resultados desse teste devem ser adicionados ao relatório antes de qualquer alegação de conclusão.
