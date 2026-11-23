# chains.py

Step 6. Classifies every segment of every breakline by the class of the face on its left and on its right, to recognize the **tops of bank** (breaklines between a sponda and an `intermedio` or `flood` area) that `widen.py` can move. It follows `cl2.py` and precedes `widen.py`.

## Requirements

* Anaconda Python: geopandas, shapely 2.1, numpy.
* Imports `core.py`: `load_graph`, `cls`, `collections`, `gpd`, `np`, `shapely`, `pickle`, `SP`.

## Input

* `WD/work/graph.pkl` (`load_graph`): `faces`, `rows` (name per face).
* `WD/in/breaklines.gpkg` (with `fid_as_index=True`): geometry only; the **first part** of each geometry is used; empty/null geometries are discarded.

## Output

* `WD/work/chains.pkl`: dict with
  * `feat`: `fid -> Nx2 array` of the vertices;
  * `S`: `(K,4)` array of the non-degenerate segments (> 1e-6 m);
  * `meta`: list of `(fid, index of the segment in the line)` aligned with `S`;
  * `L`, `R`: arrays of region names of the faces on the left/right of the segment (`'outside'` if it is in no face, `'noname'` if the face has no point);
  * `Lc`, `Rc`: the same as `cls` classes;
  * `istop`: bool array, `True` if the segment separates `sponda` from `inter` or from `flood`.
  Read by `widen.py`, `apply_widen.py`, `gaps.py`, `place.py` and the later scripts (`finals`, `regions`...).
* stdout: histogram of the pairs (left class, right class), number of features entirely "top" and mixed, example of mixed features (max 20), number of features touching `sponda_antro`.

## Parameters and constants

* Offset of 0.02 m (2 cm) to sample the sides (`mid ± n*0.02`, line 20).
* Degenerate segment threshold: 1e-6 m (line 12).
* Definition of top of bank: pairs `{sponda, inter}` and `{sponda, flood}` (line 24).

## Usage

```bash
python3 chains.py /path/to/WD
```

## How it works

1. Loads the faces and the breaklines; for each breakline saves the vertices in `feat` and the segments in `S`/`meta`.
2. For each segment computes the unit left normal and the midpoint.
3. `loc()` finds the face that contains the points `mid ± 0.02·n`; this gives `L` and `R` and the classes.
4. Sets `istop` and prints the statistics.
5. Saves `chains.pkl`.

## Checks and limits

* `L` is the left side with respect to the vertex order of the line, not with respect to the centerline.
* "Mixed" features (only some segments are top of bank) are skipped by `widen.py`.
* Segments with an `outside`/`noname` face are not considered top of bank.
* Multipart features are reduced to their first part (the others are ignored).
