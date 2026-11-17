# up.py

Script esplorativo (non necessario per produrre i layer). Confronta la larghezza del letto lungo due percorsi alternativi dell'asta nella finestra di easting 677860-678440 m: il percorso di collegamento (`rawcl.pkl['main']`) e quello meandriforme (`altmain.pkl`). Dopo `cl.py` (passo 4).

## Requisiti

`python3` di Anaconda; importa `core.py` da `WD/work` (`load_graph`, `boundary_segs`, `cls`, `Rays`, `np`, `pickle`).

## Input

* `WD/work/graph.pkl` (via `load_graph`, `graph.py`).
* `WD/work/rawcl.pkl` (`cl.py`): `main`.
* `WD/work/altmain.pkl` (`cl.py`): array dei vertici del percorso alternativo.

## Output

Solo stampa: `link route (in window) (percentili 10/50/90 della larghezza in m, numero campioni)` e `meander route ...`. Un commento finale nel file nota che le coordinate alternative non sono conservate altrove.

## Parametri e costanti

* Finestra `677860`-`678440` (easting); `10`: passo dei vertici; `8`: semi-ampiezza per la tangente (vertici `i-8`, `i+8`); `100` m: lunghezza del raggio; `[10, 50, 90]`: percentili.

## Uso

```bash
python3 up.py /percorso/WD
```

## Funzionamento

Per ogni percorso restringe i vertici alla finestra; ogni 10 vertici calcola la normale, lancia raggi contro i bordi del letto e misura la distanza tra il primo bordo a sinistra e il primo a destra; riporta i percentili.

## Verifiche e limiti

Il risultato è `None` se nessun campione ha bordi su entrambi i lati. Solo stampa.
