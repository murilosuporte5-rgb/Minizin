# Xaero's Minimap — engenharia reversa de waypoints

**Código-fonte:** o mod original é proprietário; não há repositório oficial de código que tenha sido identificado e usado nesta entrega. Há um formato de dados local documentado por análise externa: [Conflux-Union/Conflux Map - waypoint storage formats](https://github.com/Conflux-Union/conflux-map/blob/master/docs/reference-specs/waypoint-storage-formats.md).

**Implementado:** `tools/xaero_waypoint_import.py` é um importador **somente leitura**, que reconhece os locais antigos `XaeroWaypoints/` e novos `xaero/minimap/`, pastas de dimensão `dim%...`, arquivos `waypoints.txt`, linhas `waypoint:`, cores, nomes, conjuntos, Y desconhecido (`~`), mundo, e metadados de teletransporte. Exporta JSON portátil com `world` e `dimension`; **não teleporta o usuário nem desenha minimapa**.

**Teste:** [CI Xaero Waypoints](https://github.com/murilosuporte5-rgb/Minizin/actions/workflows/xaero-waypoints.yml).

```bash
python tools/xaero_waypoint_import.py /caminho/da/pasta/do/Minecraft --output build/xaero_waypoints.json
```

**Limites:** formato validado por testes com linhas de referência, não testado contra `.jar` oficial específico do usuário. Para recursos visuais originais ou análise das classes Java é necessário o binário autorizado; isso não foi baixado nem alterado nesta etapa. Limitações da API Bedrock impedem um minimapa nativo equivalente por um BP/RP comum.

**Licença:** sem replicar ou publicar a implementação proprietária original; importação de dados segue a gramática observada e documentação citada.
