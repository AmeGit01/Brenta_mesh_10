# sections_csv.py

Terzo passo (2026-11-18). Scrive la tabella riassuntiva delle sezioni, `docs/Brenta_sections_50m_mesh10.csv`, leggendo i layer `_50m` dal disco. Va lanciato dopo `write2.py` e `verify2.py`. Sostituisce il comando occasionale usato il 17 novembre e ne riproduce lo stesso formato: è stato verificato riga per riga sui backup del 18 novembre.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely).
* Si lancia dalla cartella del progetto; non usa la cartella di lavoro `WD`.

## Input

* Argomento 1: la cartella dei layer, di norma `layers`, con `boundary_50m.gpkg`, `centerpoints_50m.gpkg` e `bankpoints_50m.gpkg`.
* Argomento 2 (facoltativo): un suffisso da inserire prima di `.gpkg` per leggere dei backup, per esempio `_backup_20261118`. Per i layer correnti si passa `""`.
* Argomento 3 (facoltativo): il file di uscita, `docs/Brenta_sections_50m_mesh10.csv` se assente.

## Output

Un CSV con una riga per sezione, nell'ordine del layer boundary (N, V, B), e le colonne:

* `sezione`, `ramo` (la lettera iniziale) e `s_m` (progressiva nel ramo, dai centerpoint);
* per ciascun lato (`_sx`, `_dx`): `z` (quota DTM), `dist_cp` (distanza dal centerpoint), `tipo`, `regola` e `prom` (prominenza), presi dai bankpoint;
* `lunghezza_m`, la lunghezza della sezione nel layer boundary.

Le cifre decimali sono 2 per `s_m`, `dist_cp` e la lunghezza, e 3 per quote e prominenza. I valori nulli restano vuoti. Lo script stampa il numero di righe.

## Uso

```bash
python3 scripts/sections_csv.py layers "" docs/Brenta_sections_50m_mesh10.csv
```

Per confrontare con uno stato precedente:

```bash
python3 scripts/sections_csv.py layers _backup_20261118 /percorso/prova.csv
```

## Funzionamento

Seleziona le sezioni del boundary (nome con una lettera N, V o B seguita da 5 cifre). Per ognuna legge `s_m` dal centerpoint con lo stesso nome e i due bankpoint `<nome>_sx` e `<nome>_dx`, misura la lunghezza della linea e scrive la riga.

## Verifiche e limiti

* Si ferma con un errore se manca un centerpoint o un bankpoint di una sezione.
* Se una sezione è stata spostata a mano nel boundary senza spostarne i bankpoint, la lunghezza segue la linea mentre quote e distanze restano quelle dei bankpoint.
