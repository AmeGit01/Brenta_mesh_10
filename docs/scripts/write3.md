# write3.py

Quarto passo (2026-11-18). È l'unico script di questo passo che **scrive in `layers/`**. Applica un file preparato da `sync_cp_bp.py` o da `fix_manual.py`, dopo aver fatto una copia di sicurezza datata di ogni layer che tocca. Successivo: `verify3.py`.

## Requisiti

* Interprete: **`/usr/bin/python3`** (di sistema), perché serve `osgeo` (OGR/GDAL).
* Pacchetti: `osgeo.ogr/osr/gdal`; stdlib `json`, `os`, `shutil`, `hashlib`, `sys`.
* I layer devono essere chiusi in QGIS.

## Input

* Argomento 1: il file JSON da applicare. Le chiavi sono tutte facoltative:
  * `bl`: `{fid: [[x, y], …]}`, la nuova geometria di alcune breakline;
  * `bd`: `{fid: [[x, y], …]}`, la nuova geometria di alcune feature del boundary, con nome e id invariati;
  * `reg_new`: una lista di nuovi punti regione, ciascuno con `nome`, `mat_id`, `max_area`, `buco`, `x` e `y`;
  * `cl`, `cp`, `bp`: linee d'asse, centerpoint e bankpoint, che vengono **ricostruiti** da zero.
* Argomento 2: l'etichetta dei backup, per esempio `20261118b`.
* La cartella `LAY` (percorso assoluto fisso) con i `*_50m.gpkg` e `DTM_finale.tif`.

## Output

* Il backup `<nome>_backup_<etichetta>.gpkg` di ogni layer toccato, verificato con SHA-256. Se esiste già un backup con quell'etichetta, lo script si ferma prima di scrivere.
* **Linee:** le geometrie di `bl` e `bd` sono sostituite come `MultiLineStringZM` con z = m = 0.
* **Punti regione:** i nuovi punti ricevono i fid successivi al massimo attuale; `buco` si scrive solo se non è nullo.
* **Linee d'asse, centerpoint e bankpoint:** se c'è `cl`, i tre layer sono ricreati con lo schema di `write2.py`. I bankpoint con `z_dtm` nullo prendono il valore della cella del DTM, senza interpolazione.
* La stampa riporta i backup, quante geometrie e quanti punti sono stati scritti, quante quote sono state lette e la parola `written`.

## Uso

```bash
/usr/bin/python3 scripts/write3.py /percorso/WD/write3.json 20261118b
```

## Storia

Il 18 novembre lo script è stato lanciato due volte:

1. con `cl`/`cp`/`bp` da `sync_cp_bp.py`, etichetta `20261118b`. Ha creato i backup di centerline, centerpoints e bankpoints e letto 20 quote dal DTM. In quel momento lo script gestiva solo queste tre chiavi;
2. con `bd`/`bl`/`reg_new` da `fix_manual.py`, etichetta `20261118c`. Ha creato i backup di breaklines, boundary e regioni_ponti, sostituito 2 breakline e 1 sezione e aggiunto 5 punti regione (fid 972–976).

## Verifiche e limiti

* Non c'è un rollback automatico: in caso di errore si ripristina dai backup con l'etichetta usata.
* Lo script non controlla la geometria che scrive: dopo ogni esecuzione vanno lanciati `verify3.py` e `verify3_dtm.py`.
* Il percorso `LAY` è fisso nel codice.
