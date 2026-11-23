# place.py

Step 10. Generates candidate section positions every 0.25 m along the two centerlines and evaluates them: distances from the toe and the top of bank, the 5 m rule from the toe vertices, crossings with the boundaries and with the internal breaklines. It also builds the new planar graph (widened breaklines + new boundaries) with the faces and their names. The choice of the stations at 50 m is made by `dp.py`. It follows `gaps.py`/`apply_widen.py`.

## Requirements

* Anaconda Python: numpy, scipy (`cKDTree`), shapely 2.1, geopandas.
* Imports `core.py`: `cls`, `key`, `boundary_segs`, `Rays`, `gpd`, `pickle`, `shapely`, `LineString`.

## Input

* `WD/work/cltab.pkl` (`cl2.py`): `q` of `main` and `vecchio`.
* `WD/work/widen2.pkl` (`apply_widen.py`): `newf`.
* `WD/work/chains.pkl` (`chains.py`): `feat`.
* `WD/work/bgn.pkl` (`apply_widen.py`): modified boundaries.
* `WD/in/boundary.gpkg`, `WD/in/regioni_ponti.gpkg` (field `nome`).

## Output

* `WD/work/newfaces.pkl`: dict `fc` (faces of the new planar graph) and `rows` (list of `{face, nome}`, one per face with at least one region point; the first point counts). Read by `finals.py`, `regions.py`, `next_bed.py`, `final.py`.
* `WD/work/cands.pkl`: dict `{'main': ..., 'vecchio': ...}`, each with arrays aligned per candidate:
  * `ss`: chainage (m, step 0.25); `P`: xy on the centerline; `n`: unit left normal;
  * `tL`, `tR`: centerline-toe distance on the side t>0 and t<0 (m); `cL`, `cR`: centerline-top;
  * `pen5`: 0..2, number of sides where the crossing with the toe falls less than 5 m from a toe vertex;
  * `hitB`: 1 if the approximate section intersects a boundary; `hitO`: 1 if it intersects an internal breakline;
  * `ok`: True if toe and top were found on both sides.
  Read by `dp.py` and `export_sec.py`.
* stdout: number of faces and of faces with a name; number of toe vertices; number of obstacles (boundaries, internal segments); for each centerline the number of candidates, valid ones, how many touch a boundary / internal lines / violate the 5 m rule.

## Parameters and constants

* `GR = 0.25` m (line 43): candidate step.
* Tangent for the normal: chord between `s-1` and `s+1` m.
* Ray radius ±1500 m.
* 5 m rule (line 68): the crossing with the toe must not fall less than 5 m from a toe vertex (if a vertex coincides, <= 1 mm, the next one is used).
* Approximate extent of the section (lines 70-72): `min(t+15, c-5)` (15 m beyond the toe but 5 m inside the top); if the width is <= 30 m it is limited to `max(t+0.5, c-5)`. Note: for the left side the test is `tL+cR > 30`, for the right side `tL+tR > 30` (asymmetry as written).
* Tolerance `1e-3` m, `1e-6`.

## Usage

```bash
python3 place.py /path/to/WD
```

## How it works

1. Loads the data and builds the new planar graph (lines `newf` or originals + boundaries `bgn` or originals); `polygonize`; assigns the names to the region points per face; saves `newfaces.pkl`.
2. `tb` (toe) and `tc` (top) from the new graph; `Rays` objects.
3. `vtx`: vertices of the breaklines that contain at least one toe segment; `KD-tree` `vk`.
4. Obstacles: `OT` = boundaries; `OTB` = single segments of breaklines that are neither toe nor top (internal lines: cross-lines, buildings).
5. For `main` and `vecchio`: `cand()` creates the candidates, `eval_cand()` evaluates the toe/top distances; computes `pen5`, the approximate extent, `hitB`, `hitO`.
6. Saves `cands.pkl`.

## Checks and limits

* The variables `toev` (line 20, `None`) and `obs` (lines 28-32) are dead code.
* The extent of the section is approximate: the final sections are built by the following scripts (`export_sec.py`, `finals.py`).
* A candidate with `ok=False` or touched by a boundary is practically excluded by `dp.py` (penalty).
* Faces without a region point have no name and do not enter the toe/top lines.
