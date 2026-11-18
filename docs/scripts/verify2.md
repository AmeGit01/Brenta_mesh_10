# verify2.py

Secondo passo (2026-11-17). Esegue 24 controlli indipendenti sui sei layer riletti dal disco dopo `write2.py` (e sulle copie `_backup_20261117`). Precedente: `write2.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely, numpy, scipy `cKDTree`; stdlib `sqlite3`, `re`, `json`, `hashlib`, `collections`).
* Sola lettura; la cartella corrente è irrilevante.

## Input

* `/home/amedeo/Documents/Brenta_mesh_10/layers/{breaklines,boundary,regioni_ponti,centerline,centerpoints,bankpoints}_50m.gpkg` e le copie `breaklines_50m_backup_20261117.gpkg`, `boundary_50m_backup_20261117.gpkg`, `regioni_ponti_50m_backup_20261117.gpkg` (percorso `L` fisso nel codice).

## Output

Solo stampa: 24 righe numerate; i controlli con esito atteso terminano con `OK` oppure `**CHECK**`, gli altri sono informativi.

## Parametri e costanti

* Valori attesi scritti nel codice: 53 nodestring non-sezione, 735 sezioni, 735 centerpoint, 1470 bankpoint, 3 centerline, stessi record di breakline del backup.
* Nomi: `[NVB]` + 5 cifre, multipli di 50 consecutivi (da 50 per N/V, da 0 per B).
* Spaziatura lungo la centerline 49.5–50.5 m (progressiva e distanza in linea retta).
* `5` m e `1e-3` m (regola dei 5 m), `1e-4` m (incroci conservati), `5` m (B00050 a monte del ponte).
* Punti regione 485, 504, 568 (stampati); originali fid ≤ 176 non spostati; attesa 1 sola faccia con più di un punto (57/58).

## Uso

```bash
cp scripts/verify2.py /percorso/WD/
```

```bash
python3 /percorso/WD/verify2.py
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

Controlli in ordine: (1) conteggi; (2) nomi; (3) le 53 nodestring uguali al backup; (4) ogni sezione ha 2 vertici identici ai bankpoint; (5) spaziatura; (6) B00000 e prime/ultime progressive; (7) B00050 a monte di `Ponte_Bordignon_monte`; (8) nessun incrocio sezione-sezione né sezione-nodestring; (9) regola dei 5 m; (10) breakline attraversate per sezione; (11) incroci delle sezioni su breakline già presenti nel backup; (12) incroci nodestring/breakline del backup ancora sulle nuove; (13) breakline identiche/cambiate; (14) grafo planare: facce senza punto e con più punti; (15–17) punti regione 485, 504, 568; (18) punti regione originali presenti e immutati; (19–24) integrità GeoPackage per ogni layer: `integrity_check`, dimensione dell'rtree = numero di geometrie, SRS 25832 e tipo.

## Verifiche e limiti

* Tutti i controlli con `OK`/`**CHECK**` devono essere `OK`. I controlli 6, 9, 10, 13 e 15–17 sono solo stampati: il 9 (regola dei 5 m) deve dare 0 violazioni, gli altri vanno letti a mano.
* Le soglie (735, 53, …) sono specifiche di questo lavoro: con altri dati vanno aggiornate.
