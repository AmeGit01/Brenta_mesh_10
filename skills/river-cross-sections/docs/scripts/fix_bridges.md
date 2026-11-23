# fix_bridges.py

Removes the sub-micrometre slivers between closure breaklines and the nodestrings they run along. The breakline is moved, never the nodestring. The pairs (breakline, nodestring) are found automatically. It does not write into the layers: it prepares a payload for `write3.py`.

Origin: Brenta project, `fix_bridges.py`, 2026-11-19.

## Why

A closure breakline starts as an exact copy of its nodestring. When it is extended beyond the ends and vertices are inserted on the overlapping stretch, those vertices can lie 1e-11 to 1e-10 m off the nodestring. The two lines no longer coincide and the planar graph gets faces about 1e-8 m wide.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).
* `work/<locked.lines_file>` must exist (run `locked_lines.py` first).

## Inputs

* Argument: the output payload file.
* Derived layers: breaklines, boundary, regions.
* Config `params.fix_bridges`: `tol` (a vertex closer than this to the nodestring is "on" it), `min_overlap` (m), `max_shift` (acceptance limit), `nodestring_regex` (only matching nodestrings are examined; null = all non-section nodestrings), `exclude` (pairs `[fid, nodestring]` that are found but deliberately not fixed).

## Outputs

* The payload `{"bl": {fid: [[x,y],...]}}`; empty if nothing needs to change.
* Printed: the pairs found, every change, the acceptance checks.

## Angle rule

If the fix of a pair would create an angle sharper than `rules.min_angle_deg` (inside the breakline, or between it and another line), the pair is skipped, reported (`NOT fixed, it would create an acute angle`) and counted. The number of rejected pairs is printed. Lines that run together over a stretch (the breakline and its nodestring) have no angle there.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/fix_bridges.py [-c rcs_config.json] payload.json
/usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>
```

## How it works

* A non-locked breakline and a non-section nodestring form a pair if the length of the breakline within `tol` of the nodestring is larger than `min_overlap` ("overlap"), or if the breakline has a vertex within `tol` of an end vertex of the nodestring and no overlap ("touch"). Plain crossings are ignored.
* Overlap: the breakline vertices on the nodestring (they must be consecutive) are replaced by the nodestring vertices, oriented like the breakline. The parts outside the nodestring are kept.
* Touch: the vertex is set exactly onto the nodestring end.
* A pair that is already exact produces no change and nothing in the payload.

## Checks / expected result

1. Maximum displacement (Hausdorff) below `max_shift`.
2. No breakline loses a vertex that coincides with a nodestring vertex.
3. Dropped vertices shared with other breaklines are listed (they become T-junctions).
4. No new crossing between lines.
5. No region point gets closer to the lines.

Regression on Brenta: on the layers before the repair the script gives the same payload as the original (breaklines 1113, 1116, 1118, 1124 and 1421); on the current layers the payload is empty (all exact). The detection on the Brenta layers also finds other candidates. They are listed in `exclude` with a reason: one fix would create a crossing (acceptance 4), the others only touch a nodestring end at 1e-10 m and were not treated in the project.

## Limits

* Which candidate pairs are worth fixing is a judgement. The detection lists them all; use `exclude` for the ones to skip.
* Pairs with a locked line are skipped and reported.
