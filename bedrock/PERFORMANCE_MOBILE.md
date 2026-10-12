# Plano de performance — Android

**Não há benchmarks feitos ainda.** RAM física de 8 GB não significa orçamento de 8 GB para Minecraft. RAM Plus usa armazenamento e não substitui desempenho de RAM física.

## Metodologia
- Fixar versão do jogo, dispositivo, resolução, render distance e configurações.
- Baseline vanilla no mesmo mundo: FPS (p50/p95 de frametime), travamentos, tempo de carga e memória do processo.
- Testar cada módulo isolado (5/15/30 min) antes da composição.
- Cenários: 10/30/60 mobs, 1/3/6 bosses, 10/50/200 waystones, redes 10/100 máquinas, transições de dimensão.
- Medir FPS mínimo, frame time p95/p99, uso de RAM, CPU e thermal throttling. Nenhum número é garantido sem medição.
- Verificar persistência e recovery após crash/force-stop.

## Prioridades
1. Sem tarefas de IA em chunks distantes.
2. Limitar partículas, entidades ativas e ciclos de scripts por tick.
3. Preferir modelos e texturas móveis, com animações simplificadas configuráveis.
4. Particionar saves e sincronização de rede; evitar `getEntities()` globais repetidos.
5. Medir variação no aparelho real, não só em emulador.
