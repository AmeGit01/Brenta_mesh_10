# obst.py

Caps the bankpoint search (`maxL` / `maxR` of `sec_in.json`) a margin before the first obstacle beyond the toe. Obstacles are the non-section nodestrings (bridges and similar), the inner breaklines (segments that are neither toe nor top of bank) and the toe of another bed. It runs after `next_bed.py` and before `bank.py`.

Origin: Brenta project, `obst.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* `work/graph.pkl` (`graph.py`): face classes `bed`, `bank`, `wall` through `cfg.face_class`.
* `work/sec_in.json`: `x`, `y`, `nx`, `ny`, `tL`, `tR`, `cL`, `cR`, `stream`, `s` (and existing caps).
* Layer `inputs.boundary` (the ORIGINAL boundary): its features whose name is not a section name (`cfg.is_section`) are the nodestrings. `fields.boundary.name`.
* Config `params.obst`: `ray_range`, `margin_before_edge`, `own_toe_skip`, `top_tolerance` (m).

## Outputs

* `work/sec_in.json` OVERWRITTEN with lowered `maxL` / `maxR`.
* Printed: one line per cap and `obstacle caps N`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/obst.py [-c rcs_config.json]
```

## How it works

1. Toe lines = outline of the `bed` faces; top-of-bank lines = outline of the `bed` + `bank` + `wall` faces.
2. Inner breaklines = unique face segments that are neither of the two.
3. Obstacle lines = inner breaklines + non-section nodestrings. For each section and side, the obstacles in `(toe - margin, top of bank - top_tolerance)` and the toes of other beds beyond the own toe (+ `own_toe_skip`) are merged.
4. The cap is `first obstacle - margin_before_edge`, applied only if it lowers the current cap (idempotent).

## Checks / expected result

* On the 735 Brenta sections (inputs rebuilt from the current layers) output and `sec_in.json` are identical to the original script (251 caps).

## Limits

* Distances are along the section normal from the centerpoint.
* The boundary layer must be the original one: the derived one also holds the sections and edited nodestrings.
