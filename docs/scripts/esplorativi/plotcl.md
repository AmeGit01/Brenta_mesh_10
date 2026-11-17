# plotcl.py

Script esplorativo (non necessario per produrre i layer). Disegna le centerline grezze di asta (rosso) e Brenta vecchio (magenta) sul poligono del letto, in quattro finestre (`cl.png`). Si usa dopo `cl.py` (passo 4).

## Requisiti

`python3` di Anaconda con geopandas, matplotlib (`Agg`). Importa `core.py` da `WD/work` (da cui usa `pickle`, `gpd`, `SP`).

## Input

`WD/work/rawcl.pkl` (`cl.py`): `P` (poligono del letto), `main`, `vecchio` (array di vertici).

## Output

`WD/work/cl.png` (dpi 85), 2×2 finestre. Nessuna stampa.

## Parametri e costanti

* `wins`: quattro finestre `(xmin, xmax, ymin, ymax)` fisse.
* `figsize=(18,10)`, `dpi=85`, spessori di linea.

## Uso

```bash
python3 plotcl.py /percorso/WD
```

## Funzionamento

Carica `rawcl.pkl`, disegna `P` in azzurro e le due polilinee in ogni finestra, salva la figura.

## Verifiche e limiti

Solo ispezione visiva; le finestre sono specifiche delle zone discusse nel registro del lavoro.
