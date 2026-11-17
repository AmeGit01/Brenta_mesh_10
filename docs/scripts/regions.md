# regions.py

Garantisce un punto regione per ogni faccia del grafo planare finale (breakline allargate + boundary + nuove sezioni), a ≥ 1 m dalle linee quando possibile. I vecchi punti troppo vicini alle linee vengono scartati; le facce rimaste senza punto ne ricevono uno nuovo, nel "polo di inaccessibilità" della faccia, con gli attributi del punto della faccia madre. È il passo 16 (precedente `finals.py`, successivo `dump.py`).

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely 2.x (`unary_union`, `polygonize`, `polylabel`), geopandas, `json`.
* Modulo importato: `core.py`.

## Input

* `WD/work/sec_in.json`, `WD/work/bank_out.json`: letti ma non usati nei calcoli (variabili `S`, `O`).
* `WD/work/secs0.pkl` (`finals.py`): sezioni a 2 vertici.
* `WD/work/widen2.pkl` (`newf`), `WD/work/chains.pkl` (`feat`), `WD/work/bgn.pkl`, `WD/work/newfaces.pkl` (`fc`, `rows`): come in `finals.py`.
* `WD/in/regioni_ponti.gpkg`: punti regione, campi `nome`, `mat_id`, `max_area`, `buco`.
* `WD/in/boundary.gpkg`: boundary.

## Output

* `WD/work/regions.json`: `{"new": [...], "dropped": [...], "kept": [...]}`.
  * `new`: dict con `face` (indice in `finalfaces.pkl`), `x`, `y`, `nome`, `mat_id`, `max_area`, `buco` (int o `null`), `clear` (distanza dalle linee, m).
  * `dropped`: fid (indice GPKG) dei punti originali da eliminare.
  * `kept`: fid dei punti originali mantenuti.
* `WD/work/finalfaces.pkl`: `{"fc": lista dei poligoni delle facce finali}`.
* Stampa: numero di facce e di facce piccole (< 0.5 m², < 5 m²), punti con distanza < 1 m, punti nelle facce, `kept/dropped/new/errs`, `new clear min/med`, Counter dei `nome` dei nuovi punti. Consumato da `dump.py`.

## Parametri e costanti

* `1.0` m: distanza minima desiderata punto-linee.
* `1e-6`: tolleranza nel confronto con la distanza dalle linee originali.
* `0.05` m: tolleranza di `polylabel`.
* `0.5`, `5` m²: soglie delle facce "piccole" (solo stampa).
* `[:30]`, `[:10]`: limiti di elenco.

## Uso

```bash
python3 regions.py /percorso/WD
```

## Funzionamento

1. Unisce tutte le linee finali (breakline spostate, boundary spostati, sezioni) con `unary_union` e le poligonizza: `fc`.
2. Assegna a ogni faccia finale i punti regione originali contenuti (`within`).
3. Per ogni faccia finale individua la faccia madre in `newfaces.pkl` (punto rappresentativo) e raccoglie i punti originali della faccia madre (`bfp`).
4. Calcola `d` (distanza di ogni punto dalle nuove linee) e `d_old` (dalle linee originali).
5. Punti fuori da ogni faccia: sempre mantenuti. In una faccia: si tengono i punti con `d ≥ 1 m` oppure non più vicini di prima alle linee (`d ≥ d_old`); se nessuno è accettabile tutti sono scartati (`dropped`).
6. Per le facce senza punti mantenuti, nuovo punto con `polylabel` e attributi del primo punto originale della faccia madre; le facce senza faccia madre o senza punti madre finiscono in `errs`.
7. Scrive `regions.json` e `finalfaces.pkl`.

## Verifiche e limiti

* Controllare `errs` (atteso vuoto), `new clear min` (≥ 1 m auspicabile; i casi < 1 m sono contati) e che il totale dei punti per faccia risulti 1 (verificato poi da `check.py`, punto 9).
* Nelle facce con più punti accettabili li mantiene tutti ("i duplicati preesistenti non vengono toccati", come dice il commento nel codice).
* I `dropped`/`kept` sono fid GPKG; `face` è un indice nella lista `fc` di `finalfaces.pkl`.
