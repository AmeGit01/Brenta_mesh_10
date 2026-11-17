# core.py

Modulo di utilità condiviso, **non si lancia direttamente**: gli altri script lo importano con `sys.path.insert(0,sys.argv[1]+'/work'); from core import *`. Contiene gli import comuni, la variabile `SP` (cartella di lavoro), la classificazione dei nomi delle regioni in classi (`cls`), il caricamento di `graph.pkl` (`load_graph`) e le funzioni geometriche per estrarre le linee di piede/ciglio e per interrogare i segmenti con raggi (`Rays`). Nella pipeline (`docs/scripts/README.md`) è trasversale: serve dallo step 4 (`cl.py`) in poi ed è usato anche dagli script `export_sec`, `next_bed`, `finals`, `regions`, `dump`, `check2`, `final` e da alcuni esplorativi.

## Requisiti

* Python di Anaconda (`python3`) con numpy, shapely 2.1 (`STRtree`, `get_coordinates`, `linestrings`), geopandas.
* Non importa altri script. Deve trovarsi in `WD/work/`.

## Input

* `WD/work/graph.pkl` (prodotto da `graph.py`), letto solo tramite `load_graph()`. Chiavi usate: `faces`, `rows`.
* `sys.argv[1]`: cartella di lavoro WD, letta all'import.

## Output

Nessun file. Effetti collaterali all'import: `warnings.filterwarnings('ignore')` e definizione di `SP`.

Con `from core import *` gli script ricevono anche questi nomi: `pickle`, `np`, `shapely`, `gpd`, `warnings`, `collections`, `sys`, `LineString`, `Point`, `Polygon`, `SP`, oltre alle funzioni sotto (per questo `cl.py` usa `Polygon` senza importarlo).

## Parametri e costanti

* `SP = sys.argv[1]` (riga 5): cartella di lavoro. Unica modifica rispetto alla versione originale, che aveva un percorso fisso.
* Nomi riconosciuti in `cls` (riga 7-11), da modificare lì se cambiano i nomi delle regioni.
* Arrotondamento di `key`: 4 decimali (0.1 mm).
* Tolleranze in `Rays.hits`: `|den| > 1e-12` (parallelismo), `u` in `[-1e-9, 1+1e-9]`.

## Uso

Non eseguibile da solo. Negli script che lo usano:

```python
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
```

```bash
python3 cl.py /percorso/WD
```

## Funzionamento: riferimento di funzioni e classi

### `cls(n)`

* Argomento: `n` (str), nome della regione (campo `nome` di `regioni_ponti`).
* Restituisce una stringa:
  * `'bed'` se `n` è `bed`, `bed_borgo`, `Ponte_Bordignon`, `raccordo_sifone_brentavecchio`, oppure finisce con `_bed` o inizia con `source_`;
  * `'sponda'` se inizia con `sponda` o finisce con `sponda_nat`;
  * `'muro'` se è `muro`, `pilone-borgo`, `sottopasso-borgo`;
  * `'inter'` se inizia con `intermedio`;
  * `'flood'` in tutti gli altri casi (golena/piana).
* L'ordine dei test è quello sopra (il primo che corrisponde vince).
* Usata da: `cl.py`, `cl2.py`, `chains.py`, `widen.py`, `place.py`, `finals.py`, `next_bed.py`, `check2.py`, `final.py` (e esplorativi `zoom.py`, `up.py`). Nota: `skel.py` replica la stessa logica con le lambda `isbed`/`isbank` invece di importarla.

### `load_graph()`

* Nessun argomento. Legge `{SP}/work/graph.pkl`.
* Restituisce `(faces, rows)`: `faces` = lista di `shapely.Polygon` (facce del grafo planare); `rows` = lista di dict `{face, fid, nome, mat, area}`, una per faccia che contiene almeno un punto regione (`face` = indice in `faces`).
* Usata da: `cl.py`, `cl2.py`, `chains.py`, `widen.py` (e esplorativi `zoom.py`, `up.py`).

### `ring_segs(poly)`

* Argomento: `poly` (`Polygon`).
* Restituisce un array `(N,4)` di segmenti `[x0,y0,x1,y1]` dell'anello esterno e degli anelli interni (isole), in m, EPSG:25832.
* Usata solo da `boundary_segs`.

### `key(s)`

* Argomento: `s` = `[x0,y0,x1,y1]`.
* Restituisce una tupla `((x0,y0),(x1,y1))` con coordinate arrotondate a 4 decimali e estremi ordinati, quindi uguale per un segmento e per il suo inverso. Serve come chiave di dizionario/insieme.
* Usata da: `boundary_segs`, `place.py`, `finals.py`, `final.py`.

### `boundary_segs(faces, rows, pred)`

* Argomenti: `faces`, `rows` come da `load_graph`; `pred` = funzione `nome -> bool` che sceglie le facce (es. `lambda n: cls(n)=='bed'`).
* Restituisce un array `(M,4)` con i segmenti del contorno dell'unione delle facce scelte: un segmento condiviso da due facce scelte compare due volte e viene scartato, restano quelli contati una volta sola.
* Con `pred` = classe `bed` si ottiene il **piede** (toe), con `bed|sponda|muro` il **ciglio** (top). Se due facce coincidono esattamente (stesso segmento in due facce non selezionabili insieme) il conteggio ne risente: il metodo assume un grafo planare corretto.
* Usata da: `cl2.py`, `widen.py`, `place.py`, `finals.py`, `next_bed.py`, `check2.py`, `final.py`.

### `class Rays(segs)`

Interrogazioni "primo impatto" di rette contro un insieme di segmenti.

* Costruttore: `segs` = array `(N,4)`. Salva `self.s` (segmenti) e `self.t` (`STRtree` dei segmenti come `LineString`).
* `hits(o, d, L)`: `o` = punto (array 2), `d` = direzione **unitaria** (array 2), `L` = semi-lunghezza (m).
  * Considera la retta per `o` con direzione `d`, limitata a `|t| <= L`, e i segmenti candidati trovati con l'`STRtree` sul segmento `o-d*L .. o+d*L`.
  * Risolve `o + t*d = p + u*r` (con `r` vettore del segmento) e tiene le intersezioni con `u` in `[0,1]` (tolleranza 1e-9) e `|t| <= L`.
  * Restituisce un `np.ndarray` ordinato di distanze con segno `t` (m). Array vuoto se nessun colpo. Con `d` = normale sinistra della linea centrale: `t>0` a sinistra, `t<0` a destra; il colpo più vicino per lato è `t[t>0].min()` e `t[t<0].max()`.
* Usata da: `cl2.py`, `widen.py`, `place.py`, `next_bed.py`, `check2.py` (e esplorativo `up.py`).

## Verifiche e limiti

* `SP` viene letto all'import: se lo script è lanciato senza argomento, fallisce con `IndexError`.
* `hits` ignora segmenti paralleli alla retta (anche se sovrapposti).
* `boundary_segs` restituisce un array vuoto 1-D (e non `(0,4)`) se nessuna faccia soddisfa `pred`; gli script a valle non lo gestiscono.
* Le funzioni non fanno controlli sugli argomenti.
