# chains.py

Step 6. Classifica ogni segmento di ogni breakline in base alla classe della faccia a sinistra e a destra, per riconoscere i **cigli** (breakline tra una sponda e un'area `intermedio` o `flood`) che `widen.py` potrà spostare. Segue `cl2.py`, precede `widen.py`.

## Requisiti

* Python di Anaconda: geopandas, shapely 2.1, numpy.
* Importa `core.py`: `load_graph`, `cls`, `collections`, `gpd`, `np`, `shapely`, `pickle`, `SP`.

## Input

* `WD/work/graph.pkl` (`load_graph`): `faces`, `rows` (nome per faccia).
* `WD/in/breaklines.gpkg` (con `fid_as_index=True`): solo la geometria; si usa la **prima parte** di ogni geometria; geometrie vuote/nulle scartate.

## Output

* `WD/work/chains.pkl`: dict con
  * `feat`: `fid -> array Nx2` dei vertici;
  * `S`: array `(K,4)` dei segmenti non degeneri (> 1e-6 m);
  * `meta`: lista di `(fid, indice del segmento nella linea)` allineata a `S`;
  * `L`, `R`: array di nomi regione delle facce a sinistra/destra del segmento (`'outside'` se in nessuna faccia, `'noname'` se la faccia non ha punto);
  * `Lc`, `Rc`: le stesse come classi `cls`;
  * `istop`: array bool, `True` se il segmento separa `sponda` da `inter` o da `flood`.
  Letto da `widen.py`, `apply_widen.py`, `gaps.py`, `place.py` e dagli script successivi (`finals`, `regions`...).
* stdout: istogramma delle coppie (classe sinistra, classe destra), numero di feature interamente "top" e miste, esempio di feature miste (max 20), numero di feature che toccano `sponda_antro`.

## Parametri e costanti

* Offset di 0.02 m (2 cm) per campionare i lati (`mid ± n*0.02`, riga 20).
* Soglia segmento degenere: 1e-6 m (riga 12).
* Definizione di ciglio: coppie `{sponda, inter}` e `{sponda, flood}` (riga 24).

## Uso

```bash
python3 chains.py /percorso/WD
```

## Funzionamento

1. Carica facce e breakline; per ogni breakline salva i vertici in `feat` e i segmenti in `S`/`meta`.
2. Per ogni segmento calcola la normale sinistra unitaria e il punto medio.
3. `loc()` trova la faccia che contiene i punti `mid ± 0.02·n`; si ottengono `L` e `R` e le classi.
4. Segna `istop` e stampa le statistiche.
5. Salva `chains.pkl`.

## Verifiche e limiti

* `L` è il lato sinistro rispetto all'ordine dei vertici della linea, non rispetto alla centerline.
* Le feature "miste" (solo parte dei segmenti sono ciglio) vengono saltate da `widen.py`.
* I segmenti con una faccia `outside`/`noname` non sono considerati ciglio.
* Le feature multiparte sono ridotte alla prima parte (le altre sono ignorate).
