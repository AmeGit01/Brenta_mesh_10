# check_angles.py

Read-only check of the angle rule. No angle sharper than `rules.min_angle_deg` may exist inside a line (a spike between two consecutive segments) or where two lines meet (crossing, T-junction, shared end). The lines are the breaklines, the nodestrings and the sections of the derived layers. The script compares them with the original layers and separates NEW angles from PRE-EXISTING ones. It changes nothing.

## Requirements

* Geo interpreter (`~/anaconda3/bin/python3`): geopandas, shapely 2.x, numpy.
* `geom.py` and `common.py` in the same folder.

## Inputs

* Derived layers `outputs.breaklines`, `outputs.boundary`; original layers `inputs.breaklines`, `inputs.boundary`.
* Config: `rules.min_angle_deg`, `fields.boundary.name`, `sections.name_pattern`, `exceptions.angle`.
* `exceptions.angle`: list of `{"where": ..., "reason": ..., "date": ...}`. `where` is `[x, y]` (two floats: it covers angles located within 0.01 m of the point) or a list of line ids (an integer is a breakline fid, a string is a boundary-line name; it covers angles whose lines are all in the list).
* Option `--list-pre`: also list the PRE-EXISTING angles.

## Outputs

Print only: counts, the PRE-EXISTING count, the accepted angles, the NEW angles (kind, lines, position, angle) and a last line `angle rule: ... OK` or `**CHECK**`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/check_angles.py [-c rcs_config.json] [--list-pre]
```

## How it works

1. Reads the lines of the derived and of the original layers. Breaklines are matched by fid, boundary lines by name.
2. Uses `geom.acute_angles` on all derived lines. Two lines that run together (within 1 mm for more than 0.5 m, for example a breakline laid on a section or a nodestring) have no angle and are skipped.
3. An angle is NEW if it involves a section, or a line that is not in the original layer or whose coordinates differ from it. Otherwise it is PRE-EXISTING.
4. A NEW angle covered by `exceptions.angle` is listed as accepted. The check is OK only if no NEW angle is left.

## Checks / expected result

* `OK` when there is no NEW acute angle outside the exceptions.
* `verify3.py` runs the same logic as its last check.
* Brenta (layers of 20 Nov 2026): no PRE-EXISTING angle, 2 NEW angles (a breakline pair at 17.3 deg, a section crossing a breakline at 27.5 deg), so the check prints `**CHECK**`. They are reported, not fixed.

## Limits

* The angle between two lines is the smallest angle between the directions leaving the meeting point. Crossings give 0..90 degrees, junctions of two line ends 0..180.
* Lines are matched with the originals by id only. If ids change between the original and the derived layers, all lines count as new.
* Origin: Brenta project, new script, 2026-11-20.
