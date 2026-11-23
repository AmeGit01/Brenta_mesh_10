# check_bp.py

Independent verification of the bankpoints: it recomputes each one with a different method (profile sampled every 1 cm, instead of exact cell traversal) and compares with the stored layer. It also checks z against the DTM and the near-node rule from the top of bank. Print only.

## Requirements

* OGR interpreter (`/usr/bin/python3`): `osgeo.gdal`, `osgeo.ogr`, numpy. It does not import `geom.py`.

## Inputs

* `work/<params.check_bp.sec_in>`: section data of the bankpoint computation, one record per section: `stream` or `tag`, `s`, `x`, `y`, `nx`, `ny` (centre point and unit normal), `tL`, `tR` (toe distances), `cL`, `cR` (top-of-bank distances), optional `maxL`, `maxR` (caps). An optional key `name` gives the section name; otherwise the name is `stream_prefix[tag or stream]` plus `s` as number with `sections.digits` digits.
* `inputs.dtm`, `outputs.bankpoints`, `outputs.boundary`, `fields.bankpoints`, `fields.boundary.name`, `bankpoint_values` (left, right), `sections.name_pattern`, `rules.near_node.radius`.
* `params.check_bp`: `sec_in`, `stream_prefix`, `kind_wall`, `kind_max`, `kind_fallback`, and the numbers of the limit rule: `step` (0.01 m sampling), `mid_window`, `toe_window`, `wide_bed`, `min_window`, `prom_min`, `extra_search`, `max_search`; tolerances `tol_z`, `tol_kind_z`, `residual_len`.

## Outputs

Print only:

* `sec layer N`: sections read from the boundary layer.
* `12 z_dtm mismatch A of N ; bankpoints closer than the near-node radius to top B`.
* `13 independent 1-cm bankpoint comparison: differences N [...]`: up to 20 items `(section, side, stored kind, recomputed kind, stored z, recomputed z)`.
* `residual ...` lines for differences not explained by the sampling.
* `in-range stretch of winning cell (m) [...] ; at most 1 cm: K of N`.

## Usage

```bash
cd <working folder>
/usr/bin/python3 <toolkit>/scripts/check_bp.py [-c rcs_config.json]
```

## How it works

1. **Check 12a:** reads the DTM cell under each bankpoint and compares it with z (difference > `tol_z` is an error). Expected 0.
2. **Check 12b:** counts non-wall bankpoints with `dist_cp > top-of-bank distance - radius`. Expected 0.
3. **Check 13:** for every non-wall bankpoint it rebuilds the search limit (cap, mid-width + `mid_window`, or toe + `toe_window` if the bed is wider than `wide_bed` or the window is shorter than `min_window`), samples the profile every `step` up to `min(top + extra_search, max_search)`, groups equal values into runs, finds local maxima with prominence >= `prom_min` and height above half of the toe-to-maximum range, and takes the first. Otherwise it takes the highest sample (`fallback`). A difference is a different kind or a height differing by more than `tol_kind_z`.
4. **Explanation of differences:** for each difference it measures the length of the stored point's DTM cell inside the valid window. If <= `residual_len` the 1 cm sampling could not see the cell (sampling artefact); otherwise a `residual` line is printed.

## Checks / expected result

No `residual` line: `at most 1 cm: K of N` with K = N; check 12 gives 0 and 0.

## Limits

* Bankpoints of kind `nobank` or `nodata` have a null z and are not handled.
* Wall bankpoints are checked only for z.
* The script needs the section data file of the bankpoint computation; it is not produced by the checks.
* DTM reading uses `floor`; a point exactly on a cell edge can be ambiguous.

Origin: Brenta project, `check_bp.py`, step 19 of the original pipeline.
