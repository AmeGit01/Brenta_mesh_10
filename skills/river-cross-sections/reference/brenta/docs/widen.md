# widen.py

Step 7. Computes how far each top of bank (top-of-bank) must be moved outward to reach the wanted width, and generates the new geometry of the moved features. Rule: upstream of Borgo (`s <= BORGO_END = 17 335 m` on the main reach) and on the Brenta vecchio, the total top-to-top width must be >= 40.10 m (symmetric shift); downstream of Borgo each bank (toe-to-top) must be >= 16.05 m. The shifts are limited so that at least 5 m remain from the next outer line; the anthropic banks (`sponda_antro`) and the walls do not move. It follows `chains.py` and precedes `apply_widen.py`.

## Requirements

* Anaconda Python: numpy, scipy (`cKDTree`), shapely 2.1, geopandas.
* Imports `core.py`: `load_graph`, `cls`, `boundary_segs`, `Rays`, `collections`, `Point`, `LineString`, etc.

## Input

* `WD/work/graph.pkl` (via `load_graph`): faces and names.
* `WD/work/chains.pkl` (`chains.py`): `feat`, `S`, `meta`, `L`, `R`, `Lc`, `Rc`, `istop`.
* `WD/work/cltab.pkl` (`cl2.py`): only `T0[name]['q']`, the 1 m centerline.
* `WD/in/boundary.gpkg`: geometries of the boundary lines (`fid_as_index=True`) and field `nome` (only for the messages).

## Output

* `WD/work/widen.pkl`: dict with
  * `newf`: `fid -> Nx2 array` of the new geometry of only the "top" features actually moved;
  * `bmove`: `tag -> new position (xy)` of the "forced" vertices: `tag = ('bl', fid, end)` for ends of other breaklines and `('bd', fid_boundary, end)` for ends of boundaries;
  * `endT`: `(x,y) original rounded to the mm -> new xy` for the same points;
  * `bgeo`: `fid boundary -> original vertices`;
  * `ST`: `(nm, D)`: names (`main`/`vecchio`) and matrix with columns `i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR` for every point of the centerline with valid crossings;
  * `sL`, `sR`: left/right shift (m) per row of `D`;
  * `PTS` (points on the top of bank, two per station), `SH` (shift in m), `DN` (unit direction towards the outside).
  Read by `apply_widen.py`.
* stdout: number of points limited by the 5 m constraint, fraction of points widened per side and maximum, statistics downstream of Borgo (fraction, km, maximum), total number of top features, "boundary end coincident w breakline: left as is", "boundary end at chain vertex", number of forced points, "mixed skip <fid>", number of features changed.

## Parameters and constants

* `BORGO_END = 17335.` m (line 10): end of the urban stretch of Borgo on the main reach.
* `40.10` m: minimum top-to-top width upstream and on the vecchio (line 30).
* `16.05` m: minimum toe-to-top width per bank downstream (line 28).
* `5` m: minimum distance from the next outer line (lines 36-37).
* Ray radius ±1500 m.
* `3.0` m: maximum distance of a station from the vertex to apply its shift (`shift_at`, line 54).
* Densification of the tops at 2 m; simplification 0.02 m and removal of the vertices closer than 2 m (lines 100, 117, 120).
* Tolerances: `1e-3` m (contacts), `1e-6` (comparisons), minimum shift applied 1e-3 m; `c>0.5` for the projection along the direction of the incident line (line 111).

## Usage

```bash
python3 widen.py /path/to/WD
```

## How it works

1. Loads the data; `tb` (toe: bed), `tc` (top: bed|sponda|muro), `to` (also `inter`) with `Rays` objects.
2. For each point of the centerline of `main` and `vecchio`: left normal, hits on the toe/top/"outside"; computes `tL,tR` (centerline-toe), `cL,cR` (centerline-top beyond the toe), `W = cL+cR`, `oL,oR` (next outer line beyond the top). Side L = t>0 (left), R = t<0.
3. Shift rule `rule` (see above); then a cap `min(shift, max(gap-5, 0))` with `gap = o - c`.
4. Stations on the top `TL = centre + n·cL`, `TR = centre - n·cR` with shift and direction; `KD-tree` to assign the shift to any point (within 3 m).
5. `topfid`: top segments per feature; `ALL` = features with at least one top segment.
6. "Forced" points: ends of other breaklines (`bl`) and of the boundaries (`bd`) that fall on a top (T-junctions), to keep and move together with it.
7. For each feature in `ALL` (excluded if it touches `sponda_antro`, or if it is mixed: prints `mixed skip`): densifies at 2 m plus the original vertices and the forced points; moves the points; for the forced vertices moves along the direction `u` of the incident line (`P + u·sh/c`) or, if the angle is too oblique, along the normal; splits at the forced vertices, simplifies and thins; recomposes into `newf`.
8. Records the new positions of the forced points in `endT` and `bmove`; saves `widen.pkl`.

## Checks and limits

* Mixed features (top part, non-top part) and those that touch `sponda_antro` remain unchanged.
* `spondaname()` is defined but never used.
* If the normal does not cross the toe/top on one side, the station is excluded (no shift there).
* After running, check "clamped by clearance" (a high number = little room), the widening percentages, and the number of `mixed skip`.
* The new geometry is validated only by `apply_widen.py`.
