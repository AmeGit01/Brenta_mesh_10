# map.py

Script esplorativo (non necessario per produrre i layer). Mappa in due pannelli delle facce `bed`, `bed_borgo`, `sponda_nat`, `sponda_antro` (`map.png`) e stampa delle componenti connesse di ciascun gruppo, per controllare la continuità di letto e sponde. Si usa dopo `graph.py` (passo 1).

## Requisiti

`python3` di Anaconda con numpy, shapely, geopandas, matplotlib (`Agg`). Non importa `core.py`.

## Input

* `WD/work/graph.pkl` (`graph.py`): `faces`, `rows`.
* `WD/in/boundary.gpkg` (solo per etichettare i boundary `BC_*` e `diverg*`).

## Output

* `WD/work/map.png` (dpi 95), due pannelli (easting 675500-690600 e 690300-705600), con legenda.
* Stampa, per ciascun gruppo, `components N [(area in ha, [xmin, ymin], [xmax, ymax]), ...]` per le 12 componenti più grandi.

## Parametri e costanti

* Colori e nomi dei gruppi in `col`.
* Intervalli di easting dei due pannelli.
* `0.01` m: buffer per unire facce adiacenti prima di contare le componenti.
* `12`: numero di componenti mostrate.

## Uso

```bash
python3 map.py /percorso/WD
```

## Funzionamento

1. Seleziona per ciascun nome le facce con quel `nome` di regione.
2. Disegna i due pannelli e annota i boundary `BC_*`/`diverg*` al centroide.
3. Unisce le facce di ciascun gruppo (con buffer 0.01 m) e conta le componenti disgiunte.

## Verifiche e limiti

Un gruppo con più componenti indica interruzioni; il significato va interpretato a mano. Solo ispezione, nessun file di dati.
