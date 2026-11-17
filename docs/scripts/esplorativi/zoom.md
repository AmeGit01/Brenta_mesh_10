# zoom.py

Script esplorativo (non necessario per produrre i layer). Quattro ingrandimenti (zone di Borgo e vicino a easting 677900) con facce colorate per classe, nomi dei letti e boundary etichettati (`zoom.png`). Si usa dopo `graph.py` (passo 1).

## Requisiti

`python3` di Anaconda con geopandas, shapely, matplotlib (`Agg`); importa `core.py` da `WD/work` (`load_graph`, `cls`, `gpd`, `SP`).

## Input

* `WD/work/graph.pkl` (via `load_graph`).
* `WD/in/boundary.gpkg`.

## Output

`WD/work/zoom.png` (dpi 80), 2×2 finestre. Nessuna stampa.

## Parametri e costanti

* `wins`: quattro finestre `(xmin, xmax, ymin, ymax)`.
* Palette `C`; `figsize=(17,11)`; `dpi=80`.

## Uso

```bash
python3 zoom.py /percorso/WD
```

## Funzionamento

Per ogni finestra disegna le facce che la intersecano colorate per classe (annotando il nome di quelle `bed`) e i boundary in nero con il nome in rosso.

## Verifiche e limiti

Solo ispezione visiva; finestre fisse.
