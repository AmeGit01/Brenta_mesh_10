# drop_regions.py

Quinto passo (2026-11-19). Elimina da un GeoPackage di punti regione le feature indicate per fid, dopo averne fatto un backup datato e averlo verificato byte per byte. Tutte le altre feature, i campi, il tipo di geometria, il sistema di riferimento e l'indice spaziale restano invariati.

## Requisiti

* Interprete: `/usr/bin/python3` di sistema, con GDAL/OGR.
* Il layer deve essere chiuso in QGIS.

## Input

* Argomento 1: il GeoPackage da modificare.
* Argomento 2: il percorso del backup. Non deve esistere già, altrimenti lo script si ferma (`exists: …`).
* Argomenti successivi: i fid da eliminare. Se uno non esiste, lo script si ferma senza modificare nulla.

## Output

* Il backup, una copia identica del file di partenza.
* Il file modificato. Le eliminazioni avvengono in un'unica transazione.
* A schermo: per ogni fid eliminato, nome, `mat_id`, `max_area` e geometria.

## Uso

```bash
/usr/bin/python3 scripts/drop_regions.py layers/regioni_ponti_50m.gpkg layers/regioni_ponti_50m_backup_20261119.gpkg 58 65 135
```

## Uso del 2026-11-19

Ha eliminato da `regioni_ponti_50m.gpkg`:

* i fid 65 e 135, `sponda_nat`, senza geometria fin dai dati originali;
* il fid 58, `muro`, che stava nella stessa faccia del 57 con attributi identici.

Le 906 righe rimaste sono tutte con geometria. Al controllo indipendente risultano identiche al backup per geometria e attributi, l'indice R-tree e `gpkg_ogr_contents` contano 906, e `integrity_check` dà ok.

## Limiti

* Non controlla il grafo delle facce: va lanciato dopo `check_regions.py` o `verify3.py`.
