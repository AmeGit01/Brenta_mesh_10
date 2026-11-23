# bank.py

Finds the left and right bankpoint of every section on the DTM. Rule: walk along the section from the toe outward and take the first local maximum of the DTM profile with enough prominence, ignoring the lower part of the bank height. The point must be a buffer inside the top-of-bank line and within a window either around the mid-width of the channel (`mid` rule) or beyond the toe (`toe15` rule: wide beds or windows that are too small). Fallback: the highest cell in the window.

Origin: Brenta project, `bank.py`, 2026-11-09.

## Requirements

* Interpreter: `/usr/bin/python3` (GDAL/OGR `osgeo`, numpy). Not the Anaconda one.

## Inputs

* `work/sec_in.json` (after `next_bed.py` and `obst.py`): `x`, `y`, `nx`, `ny`, `tL`, `tR`, `cL`, `cR`, optional `maxL`, `maxR`.
* DTM `cfg.dtm()` (band 1); nodata value `dtm.nodata`.
* Config `params.bank` (metres, DTM units): `min_prominence`, `lower_fraction`, `top_buffer`, `mid_halfwidth`, `wide_bed`, `min_window`, `toe_window`, `profile_extension`, `max_distance`.

## Outputs

* `work/bank_out.json`: list (same order as `sec_in.json`) of `{"L": {...}, "R": {...}}`. Per side: `kind` (`max`, `fallback`, `muro`, `nobank`, `nodata`), `t` (distance from the centerpoint along the normal), `z`, `prom`, `rule` (`mid`, `toe15`, `muro`, `nobank`, `nocell`), `limit`, and `ztoe`, `zrange` for `max`, `fallback`, `muro`.
* Printed: a Counter of `(kind, rule)` for each side.

## Usage

```bash
cd <working folder>
/usr/bin/python3 <toolkit>/scripts/bank.py [-c rcs_config.json]
```

## How it works

1. For each side: `cap = min(top of bank - top_buffer, maxL/maxR)`.
2. Window limit `lim = min(cap, mid + mid_halfwidth)` (`mid` rule). If the bed is wider than `wide_bed` or `lim <= toe + min_window`, `lim = min(cap, toe + toe_window)` (`toe15` rule).
3. If the cap is at or before the toe: wall (`muro`) at the cap. If there is no room: `nobank`. Nodata in the window: `nodata`.
4. The profile is read cell by cell (exact grid traversal) up to `top of bank + profile_extension`.
5. Plateaus of equal value are found; the first one that overlaps the window, has prominence >= `min_prominence` and height >= toe + `lower_fraction` x (max - toe) is the bankpoint (middle of the plateau, clipped to the window). Otherwise `fallback`.

## Checks / expected result

* On the 735 Brenta sections (inputs rebuilt from the current layers) `bank_out.json` is byte-identical to the original script.

## Limits

* The original script read the nodata value from the raster; the toolkit uses `dtm.nodata` (they are equal for the Brenta DTM).
* The side with `nobank` or `nodata` has no `z` and the bankpoint is put midway between toe and top.
