# dump.py

Raccoglie in un solo JSON tutto ciò che `write.py` deve scrivere nei nuovi GeoPackage (non serve GDAL): sezioni come nodestring `S#####`/`V#####`, bankpoint, centerpoint, centerline, boundary e breakline spostati, modifiche ai punti regione. È il passo 17 (precedente `regions.py`, successivo `write.py`).

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely, geopandas, `json`.
* Modulo importato: `core.py`.

## Input

* `WD/work/sec_in.json`, `bank_out.json`, `secs0.pkl`, `widen2.pkl` (`newf`), `bgn.pkl`, `regions.json` (chiave `new`, `dropped`).
* `WD/work/cltab.pkl` (`cl2.py`): dict per stream con la chiave `q` (vertici della centerline lisciata e ricampionata a 1 m).
* `WD/in/boundary.gpkg`: serve `index.max()` (fid libero successivo) e colonna `id`.
* `WD/in/regioni_ponti.gpkg`: serve l'ultimo fid.

## Output

`WD/work/write.json` con chiavi:

* `secs`: lista di `{fid, id, nome, coords}` (sezioni; `nome` = `S`/`V` + ascissa arrotondata in m su 5 cifre, es. `S00050`; `fid` e `id` consecutivi a partire dal massimo esistente + 1).
* `bp`: due record per sezione: `nome` (`<sezione>_sx` / `_dx`), `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo` (= `kind`), `regola` (= `rule`), `prom`, `x`, `y`.
* `cp`: un record per sezione: `nome`, `s_m`, `x`, `y`, `stream`, e `dist_next` (m tra ascisse di sezioni consecutive dello stesso stream; assente sull'ultima di ogni stream).
* `cl`: `{main: [[x,y],...], vecchio: [...]}`.
* `bgn`: `{fid (stringa): coordinate}` dei soli boundary realmente modificati (> 1e-6 m).
* `bl`: `{fid (stringa): coordinate}` di tutte le breakline spostate (`newf`).
* `reg`: `{drop: [fid], new: [record con in più fid]}`; i nuovi punti hanno fid consecutivi dopo l'ultimo fid di `regioni_ponti`.

Stampa: nomi dei boundary cambiati, `names unique` (True atteso) con primo e ultimo nome, e i conteggi `sezioni bankpoint centerpoint breakline-spostate nuovi-punti`.

## Parametri e costanti

* `1e-6` m: soglia per considerare cambiato un boundary.
* Formato del nome: `{prefisso}{round(s):05d}`, prefisso `S` per `main`, `V` per `vecchio`.

## Uso

```bash
python3 dump.py /percorso/WD
```

## Funzionamento

1. Carica tutti gli ingressi e calcola i primi `fid`/`id` liberi per boundary e regioni.
2. Filtra `bgn` ai boundary con coordinate effettivamente diverse da quelle originali.
3. Per ogni sezione costruisce il record di sezione, i due bankpoint (estremi della sezione) e il centerpoint; imposta `dist_next` sul centerpoint precedente dello stesso stream.
4. Verifica l'unicità dei nomi (solo stampa).
5. Assegna i fid ai nuovi punti regione, estrae le centerline da `cltab.pkl` e scrive `write.json`.

## Verifiche e limiti

* `names unique` deve essere `True`; con ascissa arrotondata al metro due sezioni dello stesso stream non possono avere lo stesso nome finché la distanza è ~50 m.
* I confronti delle coordinate di boundary richiedono lo stesso numero di vertici tra originale e modificato.
* Non scrive in `layers/`; sovrascrive `write.json`.
