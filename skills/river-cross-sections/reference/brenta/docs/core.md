# core.py

Shared utility module. **It is not run directly**: the other scripts import it with `sys.path.insert(0,sys.argv[1]+'/work'); from core import *`. It contains the common imports, the variable `SP` (working folder), the classification of region names into classes (`cls`), the loading of `graph.pkl` (`load_graph`), and the geometry functions that extract the toe and top-of-bank lines and query segments with rays (`Rays`). In the pipeline (`docs/scripts/README.md`) it is used by all steps: it is needed from step 4 (`cl.py`) onward, and it is also used by the `export_sec`, `next_bed`, `finals`, `regions`, `dump`, `check2`, `final` scripts and by some exploratory scripts.

## Requirements

* Anaconda Python (`python3`) with numpy, shapely 2.1 (`STRtree`, `get_coordinates`, `linestrings`), geopandas.
* Does not import other scripts. It must be in `WD/work/`.

## Input

* `WD/work/graph.pkl` (produced by `graph.py`), read only through `load_graph()`. Keys used: `faces`, `rows`.
* `sys.argv[1]`: working folder WD, read at import time.

## Output

No files. Side effects at import: `warnings.filterwarnings('ignore')` and the definition of `SP`.

With `from core import *` the scripts also receive these names: `pickle`, `np`, `shapely`, `gpd`, `warnings`, `collections`, `sys`, `LineString`, `Point`, `Polygon`, `SP`, plus the functions below (this is why `cl.py` uses `Polygon` without importing it).

## Parameters and constants

* `SP = sys.argv[1]` (line 5): working folder. The only change from the original version, which had a fixed path.
* Names recognized in `cls` (lines 7-11). Change them there if the region names change.
* Rounding in `key`: 4 decimals (0.1 mm).
* Tolerances in `Rays.hits`: `|den| > 1e-12` (parallelism), `u` in `[-1e-9, 1+1e-9]`.

## Usage

Not runnable on its own. In the scripts that use it:

```python
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
```

```bash
python3 cl.py /path/to/WD
```

## How it works: reference of functions and classes

### `cls(n)`

* Argument: `n` (str), the region name (field `nome` of `regioni_ponti`).
* Returns a string:
  * `'bed'` if `n` is `bed`, `bed_borgo`, `Ponte_Bordignon`, `raccordo_sifone_brentavecchio`, or ends with `_bed`, or starts with `source_`;
  * `'sponda'` if it starts with `sponda` or ends with `sponda_nat`;
  * `'muro'` if it is `muro`, `pilone-borgo`, `sottopasso-borgo`;
  * `'inter'` if it starts with `intermedio`;
  * `'flood'` in all other cases (floodplain).
* The tests run in the order above (the first match wins).
* Used by: `cl.py`, `cl2.py`, `chains.py`, `widen.py`, `place.py`, `finals.py`, `next_bed.py`, `check2.py`, `final.py` (and the exploratory `zoom.py`, `up.py`). Note: `skel.py` repeats the same logic with the lambdas `isbed`/`isbank` instead of importing it.

### `load_graph()`

* No arguments. Reads `{SP}/work/graph.pkl`.
* Returns `(faces, rows)`: `faces` = list of `shapely.Polygon` (faces of the planar graph); `rows` = list of dicts `{face, fid, nome, mat, area}`, one per face that contains at least one region point (`face` = index in `faces`).
* Used by: `cl.py`, `cl2.py`, `chains.py`, `widen.py` (and the exploratory `zoom.py`, `up.py`).

### `ring_segs(poly)`

* Argument: `poly` (`Polygon`).
* Returns an array `(N,4)` of segments `[x0,y0,x1,y1]` of the outer ring and of the inner rings (islands), in m, EPSG:25832.
* Used only by `boundary_segs`.

### `key(s)`

* Argument: `s` = `[x0,y0,x1,y1]`.
* Returns a tuple `((x0,y0),(x1,y1))` with coordinates rounded to 4 decimals and the endpoints sorted, so it is the same for a segment and for its reverse. It is used as a dictionary/set key.
* Used by: `boundary_segs`, `place.py`, `finals.py`, `final.py`.

### `boundary_segs(faces, rows, pred)`

* Arguments: `faces`, `rows` as from `load_graph`; `pred` = function `nome -> bool` that selects the faces (e.g. `lambda n: cls(n)=='bed'`).
* Returns an array `(M,4)` with the segments of the outline of the union of the selected faces. A segment shared by two selected faces appears twice and is discarded; only those counted once remain.
* With `pred` = class `bed` you get the **toe** (piede), with `bed|sponda|muro` the **top of bank** (ciglio). If two faces coincide exactly (the same segment in two faces that cannot be selected together) the count is affected: the method assumes a correct planar graph.
* Used by: `cl2.py`, `widen.py`, `place.py`, `finals.py`, `next_bed.py`, `check2.py`, `final.py`.

### `class Rays(segs)`

"First hit" queries of lines against a set of segments.

* Constructor: `segs` = array `(N,4)`. Stores `self.s` (segments) and `self.t` (`STRtree` of the segments as `LineString`).
* `hits(o, d, L)`: `o` = point (array 2), `d` = **unit** direction (array 2), `L` = half-length (m).
  * Considers the line through `o` with direction `d`, limited to `|t| <= L`, and the candidate segments found with the `STRtree` on the segment `o-d*L .. o+d*L`.
  * Solves `o + t*d = p + u*r` (with `r` the segment vector) and keeps the intersections with `u` in `[0,1]` (tolerance 1e-9) and `|t| <= L`.
  * Returns a sorted `np.ndarray` of signed distances `t` (m). Empty array if there is no hit. With `d` = left normal of the centerline: `t>0` on the left, `t<0` on the right; the nearest hit per side is `t[t>0].min()` and `t[t<0].max()`.
* Used by: `cl2.py`, `widen.py`, `place.py`, `next_bed.py`, `check2.py` (and the exploratory `up.py`).

## Checks and limits

* `SP` is read at import: if the script is run without an argument it fails with `IndexError`.
* `hits` ignores segments parallel to the line (even if they overlap).
* `boundary_segs` returns an empty 1-D array (and not `(0,4)`) if no face satisfies `pred`; the downstream scripts do not handle this.
* The functions do no argument checks.
