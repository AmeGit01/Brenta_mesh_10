# check_geom.py

Geometric check of the fixed breaklines (`near_nodes.json`) against the current ones: (1) the section and nodestring crossing points must not move, (2) the deviation of every changed breakline must be small, (3) there must be no new line-line crossings.

Origin: Brenta project, `check_geom.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* Layers `outputs.breaklines`, `outputs.boundary` (current derived layers); `work/near_nodes.json`; `work/secs_new.json`.
* Config `params.check_geom.special_breaklines`: fids excluded from the crossing comparison (breaklines laid on a section or slid by `fix_near_nodes.py`); `fields.boundary.name`, `sections.name_pattern`.

## Outputs

* Printed only: (1) old crossing points no longer on the new network (expected 0); (2) new crossing points that were not on the old network (expected 0); (3) number of changed breaklines, largest Hausdorff distances, median, how many over 0.5 and 1 m; (4) line-line crossings before / after and the new ones (expected empty list).

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/check_geom.py [-c rcs_config.json]
```

## How it works

1. Lines compared: the new sections and the non-section nodestrings.
2. Crossing points of those lines with the old and with the new breaklines are counted with rounded coordinates.
3. Each point of one set must lie on the union of the other set (tolerance 1e-4 m).
4. A breakline is changed if its vertex count or a coordinate (1e-9 m) differs; the Hausdorff distance to the old one is reported.
5. Pairs of breaklines that properly cross each other are counted before and after.

## Checks / expected result

* Lost = 0, new = 0, new line-line crossings = empty.
* Brenta: identical output to the original script on the test input.

## Limits

* Only the old and new breaklines of the same fid are compared; features added or deleted are not reported.
