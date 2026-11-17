# write.py

Crea in `layers/` i sei GeoPackage `*_50m` a partire da `WD/work/write.json`. È il passo 18, **l'unico script che scrive in `layers/`** (precedente `dump.py`; seguono i controlli `check.py`, `check2.py`, `check_bp.py`, `final.py`).

> **Attenzione.** Scrive in `/home/amedeo/Documents/Brenta_mesh_10/layers/` e non fa alcun backup. Gli originali `breaklines.gpkg`, `boundary.gpkg`, `regioni_ponti.gpkg` vengono solo letti/copiati e **non** sono modificati. Come scritto nel codice, lo script **non sovrascrive**: se anche uno solo dei sei file di output esiste già, termina subito con `SystemExit('exists: <nome>')` senza scrivere nulla. Per rigenerare i file occorre cancellarli a mano prima (operazione distruttiva, senza backup: farne una copia se servono).

## Requisiti

* Interprete: **`/usr/bin/python3`** (sistema) con `osgeo` (GDAL/OGR).
* Pacchetti: `osgeo.ogr`, `osgeo.osr`, `osgeo.gdal`; stdlib `json`, `os`, `shutil`, `sys`.
* Non importa `core.py`.

## Input

* `WD/work/write.json` (`dump.py`): chiavi `secs`, `bp`, `cp`, `cl`, `bgn`, `bl`, `reg`.
* `layers/breaklines.gpkg` (layer `breaklines`), `layers/boundary.gpkg` (layer `boundary`), `layers/regioni_ponti.gpkg` (layer `regioni_ponti`): percorso assoluto fisso (`LAY`).

## Output

In `layers/`:

* `breaklines_50m.gpkg`: copia di `breaklines.gpkg` con geometria sostituita (MultiLineStringZM, Z=M=0) per le feature spostate (`bl`, per fid).
* `boundary_50m.gpkg`: copia di `boundary.gpkg` con i boundary modificati (`bgn`) e le nuove nodestring-sezione (campi `id`, `nome`; fid esplicito; gli altri campi restano NULL).
* `regioni_ponti_50m.gpkg`: copia di `regioni_ponti.gpkg` con i fid in `reg.drop` cancellati e i nuovi punti (`nome`, `mat_id`, `max_area`, `buco` solo se non `None`).
* `centerline_50m.gpkg`: layer `centerline_50m`, LineString, campi `nome` (`asta_principale`, `brenta_vecchio`), `lung_m` (m).
* `centerpoints_50m.gpkg`: layer `centerpoints_50m`, Point, campi `nome`, `stream`, `s_m`, `dist_next`.
* `bankpoints_50m.gpkg`: layer `bankpoints_50m`, Point, campi `nome`, `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo`, `regola`, `prom`.

I tre layer nuovi hanno CRS EPSG:25832. Stampa `written` a fine esecuzione. Letti da `check.py`, `check2.py`, `check_bp.py`, `final.py`.

## Parametri e costanti

* `LAY`: cartella `layers` (percorso assoluto, riga con `LAY=`).
* `OUT`: elenco dei sei nomi di output (usato anche dal controllo di esistenza).
* Mappa stream → nome: `{'main': 'asta_principale', 'vecchio': 'brenta_vecchio'}`.
* EPSG 25832.

## Uso

```bash
/usr/bin/python3 write.py /percorso/WD
```

## Funzionamento

1. Carica `write.json`; se uno dei sei file di output esiste, esce.
2. `breaklines`: copia il GPKG originale e, in una transazione, imposta la nuova geometria alle feature indicate.
3. `boundary`: copia, aggiorna i boundary spostati, aggiunge le sezioni con `CreateFeature`.
4. `regioni`: copia, `DeleteFeature` dei punti scartati, aggiunge i nuovi.
5. Crea da zero `centerline_50m` e, con la funzione `pts`, `centerpoints_50m` e `bankpoints_50m`; i valori `None` restano NULL.

## Verifiche e limiti

* Il controllo di esistenza avviene solo all'inizio: se lo script si interrompe a metà, restano file parziali e una nuova esecuzione fallisce con `exists:` finché non vengono cancellati.
* Non ha rollback né backup; dopo l'esecuzione lanciare `check.py`, `check2.py`, `check_bp.py` e `final.py`.
* Eseguirlo solo con `write.json` aggiornato (`dump.py`).
