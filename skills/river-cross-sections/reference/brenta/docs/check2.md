# check2.py

Checks that the boundaries and breaklines were changed only where intended, that no changed line crosses another, and that the target widths are reached (upstream of Borgo: top-to-top width ≥ 40 m; downstream: each bank ≥ 16 m; Brenta vecchio: width ≥ 40 m). It belongs to group 19 of the checks (after `write.py`). Print only, with lines labelled A-H.

## Requirements

* Interpreter: Anaconda `python3`.
* Packages: numpy, shapely 2.x, geopandas, scipy (imported), `json`.
* Imported module: `core.py` (`Rays`, `boundary_segs`, `cls`, `SP`, `np`, `shapely`, `gpd`, `LineString`, `Point`).

## Input

From `/home/amedeo/Documents/Brenta_mesh_10/layers/`: `breaklines_50m`, `breaklines` (original), `boundary_50m`, `boundary` (original), `regioni_ponti` (**original**, not `_50m`), `centerline_50m`. `WD` is needed only to import `core.py`.

## Output

Print only (no file). Lines:

* **A**: boundaries whose geometry differs from the original, `(fid, nome, maximum shift in m)`.
* **B**: number of breaklines whose coordinates changed.
* **C**: number and list (first 20) of pairs `(changed line, other)` that cross (`crosses`); non-simple lines.
* **D**: number of faces of the graph, and of faces with at least one region point.
* **E**: main reach upstream of `s = 17335 m`: number of samples, minimum W / 1st percentile / median, samples with W < 40 m and stretches `(s_start, s_end, W_min)`.
* **F**: main reach downstream: minimum and 1st percentile of the banks SL/SR, number of samples with a bank < 16 m, stretches.
* **E2**: Brenta vecchio: W min/p1/median, samples with W < 40 m, stretches.
* **G**: for each pair of C, whether the original also crossed (`True` = pre-existing).
* **H**: sections that intersect exactly 3 breaklines, with the intersection points.

## Parameters and constants

* `17335` m: chainage that separates upstream and downstream (end of Borgo).
* `40` m: minimum top-to-top width (E, E2); `16` m: minimum downstream bank (F).
* `0.5` m: sampling step along the centerline (from 1 m to length − 1 m); `±1 m` for the tangent.
* `1500` m: length of the rays.
* Recognized section names: `S`/`V` + 5 digits.

## Usage

```bash
python3 check2.py /path/to/WD
```

## How it works

1. A-B: compares the `_50m` boundaries and breaklines with the originals.
2. C-G: with an `STRtree` looks for crossings between the changed lines and the others, and checks whether they already existed.
3. D-F: rebuilds the planar graph from the files on disk (breaklines + boundaries, excluding the sections), assigns to each face the name of an original region point it contains, extracts the outlines of the bed `Rb` and of bed+sponda+muro `Rc`; samples the centerline every 0.5 m and fires rays along the normal: `tl`/`tr` = distances of the first bed edges, `cl_`/`cr_` = distances of the first top-of-bank edges beyond the toe; `W = cl_ + cr_`, `SL = cl_ − tl`, `SR = cr_ − tr`.
4. H: lists the sections that intersect exactly 3 breaklines.

## Checks and limits

* Expected criteria (not asserted by the code): A = only the boundaries intended; C empty or with pre-existing pairs (G = `True`); E and E2 with 0 samples below 40 m; F with 0 samples below 16 m. Residues may be legitimate on urban banks/walls that did not move (`sponda_antro`, `muro`): compare the printed stretches with those zones.
* The faces are named with the points of the **original** `regioni_ponti.gpkg`: faces that only have new points do not enter the width measurements (NaN samples).
* If a modified boundary had a different number of vertices than the original, line A would fail (subtraction of arrays of different shape).
* There is one line of dead code (`gl=... if False else None`), harmless.
