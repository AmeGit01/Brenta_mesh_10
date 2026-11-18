# write2.py

> **Rilancio del 18 novembre.** Per rifare la scrittura in un giorno successivo, partendo dagli stessi input del 17:
> 1. copiare ogni `*_50m.gpkg` corrente in `*_50m_backup_<data>.gpkg` e verificarlo con `cmp`, per conservare lo stato attuale (il 18 novembre: `_backup_20261118`, con le 7 sezioni B modificate a mano in mattinata);
> 2. copiare ogni `*_backup_20261117.gpkg` sul rispettivo `*_50m.gpkg`;
> 3. lanciare lo script, che trova i backup del 17 identici e procede.
>
> **Rilancio nello stesso giorno.** Se il backup del giorno esiste già, lo script lo accetta solo se è identico al layer, cioè se il layer è stato appena ripristinato da quel backup. Altrimenti si ferma. Per rilanciare: prima copiare ogni `*_backup_20261117.gpkg` sul rispettivo `*_50m.gpkg`, poi eseguire lo script.

Secondo passo (2026-11-17), unico script che **scrive in `layers/`**. Crea prima copie di sicurezza datate dei sei layer, poi aggiorna breakline, boundary e punti regione e ricostruisce centerline, centerpoint e bankpoint. Precedente: `prep_write.py`; successivo: `verify2.py`.

## Requisiti

* Interprete: **`/usr/bin/python3`** (di sistema), perché serve `osgeo` (OGR/GDAL).
* Pacchetti: `osgeo.ogr/osr/gdal`; stdlib `json`, `os`, `shutil`, `hashlib`, `sys`.

## Input

* Argomento 1: `write2.json` (`prep_write.py`).
* `/home/amedeo/Documents/Brenta_mesh_10/layers` (`LAY`, percorso assoluto fisso): i sei `breaklines_50m`, `boundary_50m`, `regioni_ponti_50m`, `centerline_50m`, `centerpoints_50m`, `bankpoints_50m` (`.gpkg`) e `DTM_finale.tif`.

## Output

* Sei backup `layers/<nome>_backup_20261117.gpkg`, verificati con SHA-256.
* `layers/*_50m.gpkg` aggiornati: breakline cambiate (geometria `MultiLineStringZM`, z = m = 0); boundary senza le vecchie sezioni (tutti gli oggetti con nome `[SV]` + 5 cifre) e con le nuove (`fid`, `id`, `nome`); punti regione eliminati/aggiunti; `centerline_50m` (campi `nome`, `ramo`, `lung_m`, `s0_asta`), `centerpoints_50m` (`nome`, `stream`, `s_m`, `dist_next`), `bankpoints_50m` (`nome`, `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo`, `regola`, `prom`) ricreati da zero in EPSG:25832.
* Stampa `backup ok <file>` per ognuno, `boundary: removed N added M` e `written`.

## Parametri e costanti

* `LAY`, `TAG = '20261117'`: nel codice, in alto.
* `NAMES`: l'elenco dei sei layer.
* Il valore `z_dtm` dei bankpoint spostati a mano è la quota della cella DTM sotto il punto (`ReadAsArray` 1×1).

## Uso

```bash
cp scripts/write2.py /percorso/WD/
```

```bash
/usr/bin/python3 /percorso/WD/write2.py /percorso/WD/write2.json
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. Per ogni layer copia il file in `<nome>_backup_20261117.gpkg`; se il backup esiste si ferma (`backup exists`); verifica l'uguaglianza degli hash SHA-256.
2. Breakline: apre in aggiornamento e sostituisce la geometria dei fid in `bl`, in una transazione.
3. Boundary: cancella le vecchie sezioni e crea le nuove con `fid`/`id` di `write2.json`.
4. Punti regione: cancella i fid di `reg.drop`, aggiunge `reg.new` (`buco` solo se non nullo).
5. Legge dal DTM la quota dei bankpoint con `z_dtm` nullo.
6. Cancella e ricrea i tre file `centerline_50m`, `centerpoints_50m`, `bankpoints_50m` con lo stesso schema (centerline con i campi `ramo` e `s0_asta` in più).

## Verifiche e limiti

* **Non idempotente**: una seconda esecuzione si ferma sui backup esistenti prima di scrivere (protegge i backup). Per rifare l'operazione i backup vanno rimossi o rinominati a mano.
* Non c'è un rollback automatico: in caso di errore dopo i backup, ripristinare dai file `_backup_20261117`.
* Il tipo geometrico `MultiLineStringZM` delle breakline presuppone quello del layer esistente.
* Dopo l'esecuzione lanciare `verify2.py`.
