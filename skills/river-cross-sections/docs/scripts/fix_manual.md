# fix_manual.py

Repairs the side effects of sections edited by hand in a GIS, without moving any section or nodestring vertex in plan. It does not write into the layers: it prepares a payload for `write3.py`.

Origin: Brenta project, `fix_manual.py`, 2026-11-18.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).
* `work/<locked.lines_file>` must exist (run `locked_lines.py` first).

## Inputs

* Argument: the output payload file.
* Derived layers: breaklines, boundary, regions. Original layers (cfg `inputs`): breaklines, boundary, regions.
* Config: `sections.name_pattern`, `fields`, `locked`, and `params.fix_manual`: `near` (distance in m under which a crossing is treated as "almost on a vertex"), `polylabel_tol` (tolerance for the new region points), `end_gap_report` (a section end closer than this to a line, but not on it, is reported).

## Outputs

* The payload `{bd, bl, reg_new}`: `bd` sections with z/m set to 0, `bl` breaklines with a moved vertex, `reg_new` new region points (`name, mat_id, max_area, hole, x, y`).
* Printed: every intervention, and the number of vertex moves rejected by the angle rule.

## Angle rule

A vertex move that would create an angle sharper than `rules.min_angle_deg` (inside a breakline, or between a breakline and another line) is not done. It is printed as `NOT moved (new acute angle ...)` and counted. An angle that already existed and does not get sharper is accepted.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/fix_manual.py [-c rcs_config.json] payload.json
/usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>
```

## How it works

1. Sections with z or m different from 0 (vertices snapped onto a 3D line): z = m = 0, x and y unchanged.
2. A section crossing a breakline closer than `near` to a vertex, but not exactly on it: the vertex moves onto the crossing, in every breakline that shares it (rule: move the breakline, never the nodestring). If the vertex belongs to a non-section nodestring or to a locked line, it is only reported.
3. Faces of the planar graph (breaklines + all boundary lines) without a region point get a new point at the pole of inaccessibility (`polylabel`). The attributes come from the ORIGINAL region whose face (in the graph of the original layers) contains that point. If the origin is ambiguous or missing, the case is only reported.
4. Section ends at a distance between 0 and `end_gap_report` from a line are reported.

## Checks / expected result

* Read-only on the layers. After writing, run the region and face checks of the toolkit.
* Regression on Brenta (layers as they were before the repair): identical payload to the original script.

## Limits

* Only for small corrections (`near` is centimetres). It is not a replacement for the near-node rule fix.
* A new region point inherits the attributes of the original region at that place. If the change of the sections altered the nature of the zone, the attribution must be checked.
