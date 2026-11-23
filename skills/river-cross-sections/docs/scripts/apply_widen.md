# apply_widen.py

Applies the result of `widen.py` to the whole breakline set: moves the ends of the lines that touch a moved end, slides ends onto lines that did not move, extends the boundary-line ends, and validates the new planar graph. Optional step.

Origin: Brenta project, `apply_widen.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy, scipy).

## Inputs

* `work/chains.pkl`, `work/widen.pkl`.
* Original boundary and regions layers; locked lines (`cfg.locked_lines()`, their ends never move).
* Config: `widening.enabled`, `rules.min_angle_deg`, `fields.boundary.name`.

## Outputs

* `work/widen2.pkl`: `newf` (fid -> new vertices of ALL changed breaklines) and `endmap` (old end, rounded to the mm -> new end).
* `work/bgn.pkl`: boundary fid -> new vertices (only changed boundaries). The writer step takes it as the `bd` payload.
* `work/widen_faces.pkl`: faces and areas of the validation graph.
* Printed: moved ends, dependent lines moved, ends slid, boundary ends extended, non-simple lines, faces, region points per face, and the angle report.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/apply_widen.py [-c rcs_config.json]
```

## How it works

1. Builds the map of moved ends from the moved top lines and the forced T points.
2. Lines that are not moved but have an end on a moved end follow it (locked lines do not).
3. A moved end that was on an unmoved line is projected onto that line, so it stays connected.
4. Boundary ends coupled to a moved top line are extended to it.
5. Rebuilds the planar graph (union + polygonize) and counts faces and region points per face.
6. Angle rule: for all changed lines (breaklines and boundaries) it lists the acute angles (< `rules.min_angle_deg`) inside a line and where two lines meet, and separates those that already existed in the original data. New ones print `**CHECK**`.

## Checks / expected result

* "simple?" must be 0; faces with zero or two points should match the original data (Brenta: 173 faces, one pair 57/58 as in the original).
* Brenta: identical to the original script. The angle report flags the end of line 17 slid onto 1002 (16.8 degrees) and three two-vertex breaklines that lay exactly on a nodestring and lose that coincidence (their ends follow the moved top). These are flagged, not reverted: reverting would break the connection. Fix them with the bridge-fix step.

## Limits

* The angle rule is only reported here, not enforced (a global change cannot be rejected line by line). `widen.py` rejects the in-line spikes of the top lines.
