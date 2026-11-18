# prep_write.py

Secondo passo (2026-11-17). Raccoglie in `write2.json` tutto ciò che `write2.py` deve scrivere: breakline cambiate, nuove sezioni, le tre centerline (N, V, B), centerpoint, bankpoint e modifiche ai punti regione. Precedente: `regions2.py`; successivo: `write2.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely `substring`, numpy).
* Cartella di lavoro corrente = `WD`.

## Input

* Argomento 1: JSON delle breakline corrette (`fix5.json`).
* `in/breaklines_50m.gpkg`, `in/centerline_50m.gpkg`, `in/regioni_ponti_50m.gpkg`, `secs_new.json`, `regions2.json`.

## Output

* `WD/write2.json`: `bl` (fid → vertici delle breakline cambiate), `secs` (`fid`, `id`, `nome`, `coords`), `cl` (3 centerline: `nome`, `ramo`, `coords`, `s0_asta`), `cp`, `bp`, `reg` (`drop`, `new` con `fid`).
* Stampa conteggi (breakline cambiate, sezioni, centerpoint, bankpoint, punti regione eliminati/nuovi, bankpoint manuali) e lunghezze delle centerline.

## Parametri e costanti

* `fid = 64 + k` e `id = 60 + k` per la k-esima sezione di `secs_new.json` (ordine N, V, B).
* Centerline: `N_caldonazzo_borgo` (asta da 0 all'ultima sezione N), `V_brenta_vecchio` (vecchio da 0 all'ultima sezione V), `B_borgo_valle` (asta da `s_asta` di B00000 a fine); i nomi di layer sorgente sono `asta_principale` e `brenta_vecchio`.
* Soglia `1e-12` per dichiarare cambiata una breakline; `1e-6` m su `moved` per un bankpoint manuale.
* Bankpoint manuale: `tipo='manuale'`, `regola='manuale'`, `z_dtm` e `prom` nulli (la quota è letta dal DTM in `write2.py`).
* Nuovi punti regione: fid consecutivi a partire da `max(fid attuale) + 1`.

## Uso

```bash
cp scripts/prep_write.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 prep_write.py fix5.json
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. Confronta le breakline di `fix5.json` con quelle in `in/` e tiene le cambiate.
2. Costruisce le tre centerline ritagliando le centerline attuali con `substring`.
3. Per ogni ramo crea i record centerpoint (`dist_next` = differenza di `s` con la sezione successiva, `None` per l'ultima).
4. Per ogni sezione crea il record sezione e i due bankpoint `<nome>_sx`/`<nome>_dx` (la distanza `dist_cp` è ricalcolata dalle coordinate).
5. Assegna i fid ai nuovi punti regione, scrive il JSON e stampa i conteggi.

## Verifiche e limiti

* Conteggi attesi: 735 sezioni, 735 centerpoint, 1470 bankpoint, 3 centerline; i bankpoint manuali sono quelli di S00151/S01965 (il lato destro esteso di S16130 non è marcato manuale).
* Si assume che `fix5.json` contenga tutte le breakline di `in/` (`O[f]` per ogni `f` di `F`).
* Non scrive nulla in `layers/`.
