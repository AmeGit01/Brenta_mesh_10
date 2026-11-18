# sync_cp_bp.py

Quarto passo (2026-11-18). Riallinea linee d'asse, centerpoint e bankpoint alle sezioni così come sono in `boundary_50m.gpkg`, dopo che l'utente le ha modificate a mano in QGIS. Non scrive nei layer: prepara il file che poi scrive `write3.py`. Successivi: `write3.py` e `verify3.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy).
* Si lancia dalla cartella del progetto o con percorsi assoluti.

## Input

* Argomento 1: la cartella dei layer, con i `*_50m.gpkg` correnti (`boundary`, `centerline`, `centerpoints`, `bankpoints`).
* Argomento 2: un file di linee d'asse che contiene `asta_principale` e `brenta_vecchio`. Si usa `layers/centerline_50m_backup_20261117.gpkg`, l'ultimo che contiene l'asta intera, da cui si ritaglia la linea del ramo B.
* Argomento 3: il file JSON di uscita, per esempio `WD/write3.json`.

## Output

Il file JSON contiene `cl` (le tre linee d'asse), `cp` (735 centerpoint) e `bp` (1470 bankpoint), nello stesso formato di `write2.json`.

La stampa riporta:

* lo spostamento della B00000 lungo l'asta;
* i centerpoint spostati o con `s_m` cambiata di più di 1 mm;
* i bankpoint che cambiano posizione, con il vecchio e il nuovo `tipo`.

## Regole applicate

* **Centerpoint:** è l'intersezione della sezione con la linea d'asse del suo ramo. Le sezioni B si intersecano con l'asta intera, perché la linea B comincia esattamente sulla B00000 e darebbe un'intersezione degenere. `s_m` è la progressiva di quel punto nel ramo; per B è la progressiva sull'asta meno quella della B00000.
* **Linea B:** si ritaglia di nuovo dall'asta a partire dalla B00000. `s0_asta` è la progressiva della B00000 sull'asta.
* **`dist_next`:** è la differenza di `s_m` con la sezione successiva dello stesso ramo; è nulla per l'ultima sezione del ramo.
* **Bankpoint:** sono i due vertici della sezione, con il sinistro per primo.
  * Un vertice che coincide (entro 1e-6 m) con il bankpoint salvato ne conserva `tipo`, `regola`, `prom` e `z_dtm`.
  * Un vertice spostato prende `tipo` e `regola` `manuale`, `prom` nullo e `z_dtm` nullo, che poi `write3.py` legge dal DTM.
  * Se la sezione ha la stessa geometria di una nodestring (B00400 = `idrometro_Borgo`), il vertice spostato prende `tipo` `nodestring` e come `regola` il nome della nodestring.
  * `dist_cp` si ricalcola per tutti.

## Uso

```bash
python3 scripts/sync_cp_bp.py layers layers/centerline_50m_backup_20261117.gpkg /percorso/WD/write3.json
```

Poi:

```bash
/usr/bin/python3 scripts/write3.py /percorso/WD/write3.json <tag>
```

## Verifiche e limiti

* Ogni sezione deve incrociare la linea d'asse del suo ramo in un solo punto, altrimenti lo script si ferma con un errore.
* Lanciato subito dopo una scrittura, deve dire "0" centerpoint e "0" bankpoint cambiati. È un buon controllo che i layer siano già allineati: il 18 novembre è stato rilanciato dopo `write3.py` e ha dato zero cambiamenti.
* Il 18 novembre ha spostato di 2.5 cm il centerpoint di N00150 e di 5 mm quello di N01950. Sono le due sezioni modificate a mano prima del 17 novembre, che non passavano più esattamente per il loro vecchio centerpoint.
