# apply_widen.py

Step 8. Applies to the whole set of breaklines the shift computed by `widen.py`: it propagates the moved ends to the lines that touch them, slides the ends on lines that were not moved, moves the ends of the boundaries, then validates the new planar graph (simple lines, faces, one region point per face). It follows `widen.py` and precedes `gaps.py` and `place.py`.

## Requirements

* Anaconda Python: numpy, scipy, shapely 2.1, geopandas.
* Imports `core.py` (`pickle`, `gpd`, `np`, `shapely`, `LineString`, `Point`, `SP`, ...).

## Input

* `WD/work/chains.pkl` (`chains.py`): `feat`.
* `WD/work/widen.pkl` (`widen.py`): `newf`, `endT`, `bmove`, `bgeo`, `PTS`, `SH`, `DN` (the last three are loaded but not used).
* `WD/in/boundary.gpkg` (field `nome` for the messages) and `WD/in/regioni_ponti.gpkg` (region points).

## Output

* `WD/work/widen2.pkl`: dict `newf` (`fid -> new vertices` of **all** the modified breaklines: moved tops plus dependent lines) and `endmap` (`(x,y) old end rounded to the mm -> new xy`). Read by `gaps.py`, `place.py`, `finals.py`, `regions.py`, `dump.py`.
* `WD/work/bgn.pkl`: dict `fid boundary -> new vertices` only for the boundaries whose end was moved/extended. Read by `place.py`, `finals.py`, `regions.py`, `dump.py`.
* `WD/work/widen_faces.pkl`: dict `fc` (faces of the validated graph) and `A` (areas, m²). Not read by other scripts.
* stdout: number of moved ends ("moved ends", "ends really moved"), dependent features moved, ends made to slide, boundaries extended (name, end, shift in m), number of new and original non-simple lines, number of faces and faces < 1 m², faces by number of points, points inside a face, faces without a point (area, centroid; max 20), faces with >= 2 points.

## Parameters and constants

* Key of the ends: coordinates rounded to 3 decimals (1 mm).
* "Moved" if > 1e-3 m; contact tolerances `1e-3` m and `1e-6` m.
* No width parameters: they come from `widen.py`.

## Usage

```bash
python3 apply_widen.py /path/to/WD
```

## How it works

1. `endmap`: for each feature in `newf`, old -> new end; adds `endT`.
2. Features that were not moved but have an end coinciding with a moved end are modified (same moved end) and added to `newf`.
3. For each moved feature, if a moved end was attached to a line that was **not** moved, the new end is projected onto that original line (the connection is kept).
4. Saves `widen2.pkl`.
5. Boundaries: for the tags `('bd', k, e)` of `bmove`, the end `e` of boundary `k` is brought to the new top; saves `bgn.pkl`.
6. Validation: union of all the new lines + boundaries, `polygonize`, check for non-simple lines, count of region points per face.

## Checks and limits

* Expected: no new non-simple line (compare with "non-simple orig"), no face without a point of significant area, no face with 2+ points.
* The dependent features moved in this step are not in turn used to propagate further.
* The check of connectivity at the ends is left to `gaps.py`.
