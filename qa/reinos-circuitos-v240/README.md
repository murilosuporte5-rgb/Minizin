# Fidelidade visual — Reinos & Circuitos 2.4.0

Inspecionado o anexo fornecido: 42 itens, 35 blocos, 9 entidades. A auditoria encontrou 34 recursos com **imagens pixel a pixel idênticas** (23 ícones e 11 texturas de blocos) e **nenhum som** OGG/WAV.

O arquivo [Minizin_Auditoria_e_9_Packs_Independentes_QA.zip] deve ser obtido na conversa que forneceu o anexo, pois os arquivos originais do usuário não foram publicados no repositório GitHub.

Os nove packs de inspeção são **apenas QA**, não mods Java completos nem testes de jogo. Não instalar juntos com o Reinos & Circuitos original: compartilham IDs de entidades/blocos do pacote fonte.

## Próxima correção com material autêntico
O RFTools possui um modelo explícito para `storage_terminal` no commit `030a495c8530183bdfe47475ed41d45386e56f6c`, referenciando 3 imagens distintas: `machinestorageterminal`, `machineside`, `machinebottom`. O script `tools/rc_build_rftools_storage_terminal.py` converte o JSON e os pixels originais em uma geometria/atlas Bedrock e gera **um pack independente experimental**, sem copiar a textura repetida no addon recebido.

- [Workflow e artefatos](https://github.com/murilosuporte5-rgb/Minizin/actions/workflows/rc-authentic-rftools.yml)
- O restante dos ícones genéricos NÃO é marcado como consertado: nomes de inventário internos não provam correspondência com itens originais dos mods.
- Os outros blocos e itens aguardam evidência de fonte autenticada por arquivo e revisão UV.
- As verificações de build são estruturais. Testes no Minecraft Bedrock Android v26.51 continuam pendentes.

**Reprodução:** `python -m pip install Pillow && git submodule update --init mods/54-rftools/upstream && python tools/rc_build_rftools_storage_terminal.py`.
