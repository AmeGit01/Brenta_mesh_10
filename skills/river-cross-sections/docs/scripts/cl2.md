# cl2.py

Smooths the raw centerlines, resamples them at exactly 1 m (the array index is the chainage `s` in metres) and measures, along the perpendicular at every point, the distance from the toe lines and from the top-of-bank lines. The result `cltab.pkl` is the official centerline table used by the widening and placing steps.

Origin: Brenta project, `cl2.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (numpy, scipy, shapely 2.x, matplotlib).

## Inputs

* `work/graph.pkl` and `work/rawcl.pkl` (`cl.py`; keys are the centerline names of the config section `centerlines`).
* Config `params.cl2`:
  * `toe_classes`, `top_classes`: face classes whose union outline is the toe line and the top-of-bank line;
  * `resample_step` (m, keep 1.0 so that index = s), `normal_step` (points each side of the chord that gives the local direction), `ray_range` (m, search distance each side);
  * smoothing: `sigma_narrow`, `sigma_wide` (m); weight of the wide one = clip((gauss(B, `sigma_width`) - `width_narrow`) / (`width_wide` - `width_narrow`), 0, 1); `width_default`: bed width (m) used where it is missing;
  * report: `report_lines` (centerlines printed in blocks), `report_block` (m), `report_thresholds` (two bank widths, m), `plot_line` (line drawn in `tab.png`).

## Outputs

* `work/cltab.pkl`: dict keyed by centerline name; each value is a dict with
  * `q` (Nx2): smoothed centerline, one point every `resample_step` m (index = s);
  * `t` (Nx6): `[tl, tr, cl, cr, 0, 0]`, signed distances from the centerline to the toe on the t<0 side, toe on the t>0 side, top of bank on the t<0 side, top of bank on the t>0 side; NaN if the normal does not cross the lines. The last two columns are always 0;
  * `B = tr - tl` (bed width), `SL = tl - cl` and `SR = cr - tr` (bank widths toe-to-top), `W = cr - cl` (total width).
* `work/tab.png`: bank widths (top) and bed/total width (bottom) of `plot_line`.
* Printed: per line, length, points without crossings, percentiles of B and of the banks; then, per block of each `report_lines` line, the 1% and 50% percentiles of B, SL, SR, W and the fraction of points where a bank is narrower than each threshold.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/cl2.py [-c rcs_config.json]
```

## How it works

1. `tb` = toe segments, `tc` = top-of-bank segments; ray-query objects on them.
2. For each centerline: resample; first width table; smooth with the blend above (narrow reaches follow the channel, wide ones are straightened); resample at exactly `resample_step`; second table.
3. At each point the left normal is intersected with the toe and the top lines: `tl`/`cl` are the nearest hits with t<0, `tr`/`cr` the nearest with t>0.
4. Saves `cltab.pkl`, prints the report and draws the plot.

## Checks / expected result

* The script stops if a config centerline is missing in `rawcl.pkl` (run `cl.py` with the same config).
* Points with NaN in `t` occur at the ends and where the lines have gaps.

## Limits

* Side convention: here "L" (`tl`, `cl`, `SL`) is the t<0 side, geometrically the right side of the line; the widening/placing scripts use L for the t>0 side. They use `q` only from this table.
* The top-of-bank lines include the walls (if `top_classes` lists them), so small bank widths in urban reaches are normal.
