# graph.py

Step 1 della pipeline. Costruisce il grafo planare di breakline e boundary (le linee vengono "nodate" con `unary_union` e poligonizzate), associa a ogni faccia il punto regione (`regioni_ponti`) che vi cade dentro e stampa diagnostiche sull'ampiezza per classe. Il risultato `graph.pkl` è la base di tutti gli step successivi. Precede `skel.py`; non ha predecessori.

## Requisiti

* Python di Anaconda: geopandas, shapely, numpy (+ pickle, sys, collections).
* Non importa `core.py` (usa direttamente `sys.argv[1]`).

## Input

* `WD/in/breaklines.gpkg`: breakline (copia di `layers/breaklines.gpkg`); si usa solo la geometria; geometrie vuote/nulle scartate.
* `WD/in/boundary.gpkg`: linee di contorno/nodestring; solo geometria.
* `WD/in/regioni_ponti.gpkg`: punti regione; campi usati `nome`, `mat_id` e il `fid` (indice del GPKG, `fid_as_index=True`).

## Output

* `WD/work/graph.pkl`: dict con
  * `faces`: lista di `Polygon` (facce del grafo planare, in m, EPSG:25832);
  * `fr`: dict `indice faccia -> lista di posizioni (0..n-1) dei punti regione contenuti`;
  * `rows`: lista di dict, uno per faccia con almeno un punto: `face` (indice in `faces`), `fid` (lista dei fid GPKG dei punti), `nome` e `mat` (`mat_id`) del **primo** punto, `area` (m²).
  Letto da `core.load_graph()` e da `skel.py`.
* stdout: numero di breakline, vuote, distribuzione parti per geometria; numero di facce; facce con area < 1e-3 m² e < 1 m² e area totale in km²; punti regione dentro una faccia; distribuzione facce per numero di punti (atteso: 0 o 1); facce > 1 m² senza punto (15 maggiori); fid dei punti fuori da ogni faccia; tabella finale nome regione / numero facce / ettari.

## Parametri e costanti

* Ciclo `for tol,name in [(0,'exact')]` (riga 13): un solo elemento, la tolleranza non è usata (linee nodate esattamente).
* Soglie di diagnostica: area `1e-3` m² e `1` m² (righe 18, 23): solo stampa.

## Uso

```bash
python3 graph.py /percorso/WD
```

## Funzionamento

1. Legge i tre GPKG e stampa il conteggio delle breakline; scarta le geometrie vuote/nulle.
2. `lines(s)`: scompone ogni (multi)geometria in `LineString` 2D (solo x,y).
3. `unary_union` delle linee (breakline + boundary) le interseca; `polygonize` crea le facce.
4. Calcola le aree e indicizza le facce con `STRtree`; assegna ogni punto regione alla faccia che lo contiene (`predicate='within'`).
5. Costruisce `fr` e `rows` (il nome/materiale della faccia è quello del primo punto).
6. Salva `graph.pkl` e stampa il riepilogo per nome.

## Verifiche e limiti

* Dopo l'esecuzione controllare: "faces per npoints" deve essere solo 0 e 1 (più punti in una faccia: il nome è quello del primo); "pts outside" vuoto; poche facce > 1 m² senza punto.
* Facce senza punto non compaiono in `rows` (quindi non hanno classe e sono ignorate dagli step successivi).
* Linee che non si toccano esattamente (gap < tolleranza) non chiudono la faccia: il metodo non applica snapping.
