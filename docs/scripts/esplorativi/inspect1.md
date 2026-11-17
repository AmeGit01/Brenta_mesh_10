# inspect1.py

Script esplorativo (non necessario per produrre i layer). Disegna quattro finestre dell'area di Borgo con le facce colorate per classe e i boundary etichettati (`borgo.png`), e stampa statistiche sui capi delle breakline (estremi pendenti). Si usa dopo `graph.py` (passo 1).

## Requisiti

`python3` di Anaconda con numpy, shapely, geopandas, matplotlib (backend `Agg`). Non importa `core.py`: contiene una propria copia di `cls()`.

## Input

* `WD/work/graph.pkl` (`graph.py`): `faces` (poligoni), `rows` (`face`, `nome`).
* `WD/in/boundary.gpkg`, `WD/in/breaklines.gpkg`.

## Output

* `WD/work/borgo.png` (dpi 85), 2×2 finestre: facce colorate per classe (`bed` blu, `sponda` verde, `muro` rosso, `inter` giallo, `flood` grigio), boundary neri con nome.
* Stampa: `total pieces N` (parti di breakline), `end degree {grado: numero}` (quante parti condividono ciascun estremo, arrotondato a 1 mm), `dangling ends N` (estremi con grado 1).

## Parametri e costanti

* `win`: quattro finestre `(xmin, xmax, ymin, ymax)` in EPSG:25832.
* Palette `C`; `figsize=(18,12)`; `dpi=85`.
* Arrotondamento a `3` decimali per confrontare gli estremi.

## Uso

```bash
python3 inspect1.py /percorso/WD
```

## Funzionamento

1. Carica il grafo, i boundary e le breakline (scartando geometrie vuote/nulle).
2. Per ogni finestra disegna le facce che la intersecano e i boundary con etichetta al centroide.
3. Spezza ogni breakline nelle sue parti, conta il grado dei capi e il numero di estremi pendenti.

## Verifiche e limiti

Solo ispezione visiva e statistica; nessun file di dati. La variabile `edges` è inutilizzata. Le finestre sono fisse e specifiche di Borgo.
