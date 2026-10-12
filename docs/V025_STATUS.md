# Minizin v0.2.5 — estado técnico

Alterações incrementais na branch existente. Ainda não executadas no Minecraft Android.

- Waystones: bloco real criado por upgrade_waystone_block.py, com geometria/textura original já convertidas. Migração conservadora de entidades existentes; blocos obstruídos ou regiões descarregadas não são migrados automaticamente.
- Mochilas: armazenamento vinculado a cada item e transferência parcial; UI de botões, não contêiner nativo. Persistência durante crash ainda sem garantia transacional.
- Aether: dois espaços virtuais para anéis, fora da mão secundária; não são slots do inventário nativo.
- Warp Stone: valida existência de bloco e espaço de chegada.
- Tradução dos ovos: aliases com e sem sufixo .name.

Provas nesta sessão: inspeção do código e testes simulados de JavaScript. Nenhum resultado de importação, Content Log, textura na mão, multiplayer, sobrevivência ou desempenho Android foi inventado.

Construção: executar .github/workflows/verify-minizin-v025.yml na branch e examinar os relatórios. Preservar a versão 0.2.4 anterior e um backup do mundo. O candidato gerado não deve ser chamado de completo.

Restam os sistemas Java ainda não portados integralmente dos doze mods. Distant Horizons permanece sem renderização LOD comprovada; Immersive Portals e Xaero estão excluídos.
