# verify3_dtm.py

Quarto passo (2026-11-18). Accompagna `verify3.py`: controlla che il `z_dtm` di ogni bankpoint sia esattamente il valore della cella del DTM sotto il punto, senza interpolazione, e che non ci siano quote nulle o nodata. Non scrive nulla.

## Requisiti

* Interprete: **`/usr/bin/python3`** (di sistema), perché serve `osgeo` (GDAL/OGR).

## Input

`layers/bankpoints_50m.gpkg` e `layers/DTM_finale.tif` (percorso assoluto fisso).

## Output

Una riga di stampa con:

* il numero di bankpoint controllati;
* la differenza massima |`z_dtm` − cella|;
* l'elenco delle differenze oltre 1e-6 m, dei valori nulli e dei nodata;
* l'esito, `OK` o `**CHECK**`.

## Uso

```bash
/usr/bin/python3 scripts/verify3_dtm.py
```

## Funzionamento

Per ogni bankpoint calcola colonna e riga della cella dalla geotrasformazione del DTM, con la stessa formula di `write2.py` e `write3.py`, legge il valore della cella e lo confronta con `z_dtm`.

## Esito del 18 novembre

1470 bankpoint, differenza massima 0, nessuna quota nulla e nessun nodata.
