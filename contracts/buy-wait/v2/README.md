# Buy/Wait v2

Ce contrat porte une décision temporelle explicite :

- `BUY_NOW` lorsque le prix courant est matériellement bas selon une politique
  historiquement backtestée ;
- `WAIT` lorsque le prix courant est matériellement haut ;
- `ABSTAIN` dès qu'une preuve, une confiance calibrée ou le profil de backtest
  manque.

Une action exige des claims sourcés, un `trace_id`, une confiance de décision
calibrée et la preuve qu'aucune observation future n'a été utilisée. Le contrat
ne contient ni prévision de prix, ni date de baisse, ni économie garantie, ni
contexte brut.
