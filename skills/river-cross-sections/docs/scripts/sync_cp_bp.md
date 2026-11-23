# sync_cp_bp.py

Realigns the centerline, centerpoints and bankpoints to the sections as they are now in the boundary layer, after sections were moved or reshaped by hand. It does not write into the layers: it prepares the payload that `write3.py` writes.

Origin: Brenta project, `sync_cp_bp.py`, 2026-11-18.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* Argument: the output payload file.
* Derived layers: boundary, centerline, centerpoints, bankpoints (cfg `outputs`).
* Config: `reaches[*].chainage` (`{"mode": "own"}` or `{"mode": "cut_reference", "reference_file", "reference_line", "origin_section"}`), `sections`, `fields`, `bankpoint_values` (`left`, `right`, `manual`, `nodestring`).
* For a `cut_reference` reach: the reference file (path relative to the working folder) with the reference line.

## Outputs

* The payload `{cl, cp, bp}` with logical keys (see `write3.md`).
* Printed: the shift of the origin section along the reference line, the centre points moved or with changed chainage (more than 1 mm), the bankpoints that changed status, the written counts.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/sync_cp_bp.py [-c rcs_config.json] payload.json
/usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>
```

## How it works

* Centre point: intersection of the section with the centre line of its reach. `s` is the chainage of that point in the reach.
* Reach with mode `own`: the line and `s0` stay as they are in the layer.
* Reach with mode `cut_reference`: the line is cut again from the reference line, starting at the intersection with the origin section; `s0` is the chainage of that intersection on the reference line. Its sections are intersected with the whole reference line (the cut line starts exactly on the origin section and would give a degenerate intersection) and `s` is the chainage on the reference line minus `s0`.
* `dist_next` = `s` of the next section of the same reach minus `s`; null for the last one.
* Bankpoints are the two section vertices (left first). A vertex that coincides (<= 1e-6 m) with the stored bankpoint keeps kind, rule, prom and z. A vertex that moved gets kind and rule `manual`, prom and z null (write3 reads z from the DTM). If the section has the same geometry as a non-section nodestring, the moved vertex gets kind `nodestring` and rule = the nodestring name. `dist_cp` is recomputed for all.

## Checks / expected result

* Every section must cross the line of its reach in exactly one point, otherwise the script stops.
* Run on layers that are already aligned it reports 0 centre points and 0 bankpoints changed. This is a good check after every write.
* Regression on Brenta: same payload as the original script, on the current layers and on layers with sections deliberately moved.

## Limits

* The sections must be in reach order in the boundary layer (`dist_next` uses the layer order).
* Bankpoint names are `<section>_<left|right>` with the values of `bankpoint_values`.
