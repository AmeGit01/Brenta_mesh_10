# export_sec.py

Converte le posizioni delle sezioni scelte dalla programmazione dinamica (`dp.py`) in un elenco JSON piatto, un record per sezione a 50 m. È il passo 12 della sequenza (vedi `README.md`): lo script precedente è `dp.py`, il successivo `next_bed.py`. Il file prodotto, `sec_in.json`, è l'ingresso del calcolo dei bankpoint (`bank.py`) e di tutti gli script successivi.

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely, geopandas (importati tramite `core.py`), `json`.
* Modulo importato: `core.py` (da `WD/work`, aggiunto a `sys.path` da `sys.argv[1]`). Da `core` usa solo `pickle`, `SP`.

## Input

* `WD/work/cands.pkl`, prodotto da `place.py`: dict `{'main': {...}, 'vecchio': {...}}`; per ogni stream usa le chiavi `ss` (ascissa progressiva in m), `P` (punti della centerline, N×2), `n` (normali unitarie, N×2), `tL`, `tR` (distanza centerpoint → piede del letto a sinistra/destra), `cL`, `cR` (distanza centerpoint → ciglio a sinistra/destra).
* `WD/work/dp.pkl`, prodotto da `dp.py`: dict `{'main': array, 'vecchio': array}` con gli indici `j` dei candidati scelti, in ordine lungo il corso.

## Output

* `WD/work/sec_in.json`: lista di dict, nell'ordine prima tutte le sezioni `main`, poi tutte le `vecchio`. Chiavi: `stream` (`main`/`vecchio`), `s` (m), `x`, `y` (centerpoint), `nx`, `ny` (normale unitaria, verso sinistra), `tL`, `tR`, `cL`, `cR` (m).
* Stampa il numero di sezioni. Consumato da `next_bed.py` (che lo aggiorna), `bank.py`, `finals.py`, `regions.py`, `dump.py`, `check_bp.py`, `esplorativi/bq.py`.

## Parametri e costanti

Nessuna soglia. Costanti implicite: i nomi degli stream (`'main'`, `'vecchio'`) e il nome dei file di lavoro (`cands.pkl`, `dp.pkl`, `sec_in.json`), modificabili nelle prime righe dello script.

## Uso

Preparare `WD` come in `README.md` (`WD/in`, `WD/work` con gli script e i `.pkl` dei passi precedenti), poi:

```bash
python3 export_sec.py /percorso/WD
```

## Funzionamento

1. Carica `cands.pkl` e `dp.pkl`.
2. Per ciascuno stream (`main`, poi `vecchio`) e ciascun indice `j` scelto compone un record con i valori di `cands.pkl` in posizione `j`, convertiti in `float`.
3. Scrive la lista in `sec_in.json` e stampa la lunghezza.

## Verifiche e limiti

* Il numero stampato deve coincidere con il numero di sezioni attese (asta 33 981.6 m e Brenta vecchio 3 058.7 m, circa una ogni 50 m).
* Non fa alcun controllo: se `dp.pkl` e `cands.pkl` non sono coerenti produce record sbagliati senza avvisi. Sovrascrive `sec_in.json` senza backup (il file viene poi modificato da `next_bed.py`, quindi rieseguire `next_bed.py` dopo ogni riesecuzione di questo).
