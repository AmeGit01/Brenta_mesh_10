# cl2.py

Step 5. Smooths the raw centerlines, resamples them to exactly 1 m (so **the array index is the chainage s in m**), and measures, along the perpendicular at each point, the distance from the toe and from the top of bank of the banks. The result `cltab.pkl` is the official centerline used by `widen.py`, `place.py` and `dump.py`. It follows `cl.py` and precedes `chains.py`.

## Requirements

* Anaconda Python: numpy, scipy (`gaussian_filter1d`), shapely, matplotlib (`Agg`).
* Imports `core.py`: `load_graph`, `cls`, `boundary_segs`, `Rays`, `LineString`.

## Input

* `WD/work/graph.pkl` (via `load_graph`).
* `WD/work/rawcl.pkl` (`cl.py`): keys `main` and `vecchio` (Nx2 arrays).

## Output

* `WD/work/cltab.pkl`: dict `{'main': {...}, 'vecchio': {...}}`; each with
  * `q` (Nx2): smoothed centerline, one point every 1 m (index = s);
  * `t` (Nx6): `[tl, tr, cl, cr, 0, 0]` signed distances from the centerline: toe on the side t<0 / t>0, top of bank on the side t<0 / t>0 (m); NaN if the normal does not cross the lines. The last two columns are always 0;
  * `B = tr - tl` bed width (toe-to-toe), `SL = tl - cl` and `SR = cr - tr` bank width (toe-to-top), `W = cr - cl` total top-to-top width (m).
* `WD/work/tab.png`: chart of the bank widths (top, line at 20 m) and of B and W (bottom, line at 40 m).
* stdout for `main` and `vecchio`: length, points without crossings, percentiles of B and of the banks; then, for 3 km blocks of the main, the 1%/50% percentiles of B, SL, SR, W and the fraction where a bank is < 10 m and < 20 m.

## Parameters and constants

* Resampling step 1.0 m (`res`, line 8 and line 34).
* Local tangent: chord between points `i-10` and `i+10` (`step=10`, line 10).
* Search radius ±1500 m.
* Smoothing: Gaussian sigma 6 (narrow) and sigma 60 (wide); weight of the wide one `a = clip((gauss(B,50) - 15)/35, 0, 1)`: 0 with bed <= 15 m, 1 with bed >= 50 m. Missing width replaced by 10 m.
* Report blocks: 3000 m up to 34 000 m (line 43); thresholds 10 and 20 m.

## Usage

```bash
python3 cl2.py /path/to/WD
```

## How it works

1. `tb` = toe segments (outline of the `bed` faces), `tc` = top-of-bank segments (outline of `bed|sponda|muro`); `Rays` objects `Rb`, `Rc`.
2. For each centerline: resamples to 1 m; first width table; smooths with the blend above; resamples to exactly 1 m; second table.
3. In `table(q)` the left normal `n` of each point is intersected with the toe and the top of bank: `tl`/`cl` are the nearest hits with t<0 (maximum), `tr`/`cr` those with t>0 (minimum).
4. Computes `B,SL,SR,W`, prints the statistics, saves `cltab.pkl`, produces the chart.

## Checks and limits

* **Side convention**: here "L" (`tl`, `cl`, `SL`) means the side with t<0, that is geometrically the right side with respect to the direction of the line; in `widen.py` and `place.py` "L" is the side with t>0. In the reports `SL`/`SR` are therefore inverted with respect to `widen.py`; this has no effect on the result because the other scripts use only `q` from `cltab.pkl`.
* The "top of bank" here also includes the walls: in urban stretches small `SL`/`SR` values are normal.
* The number of points of `q` equals the length in m: 33 981.6 m for the main and 3 058.7 m for the vecchio in the final dataset.
* Points with NaN in `t` (normal without crossings) occur at the ends and where the lines have holes.
