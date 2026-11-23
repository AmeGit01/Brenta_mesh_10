# xn_points.py

Lists every point where a nodestring that is not a section meets a breakline. `place.py` penalises candidate sections whose toe crossing lies closer than the near-node radius to one of these points: a section there would create a node next to a node of the boundary.

Origin: Brenta project, `prep_inputs_nvb.py` (first part), 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x).

## Inputs

* Layers `breaklines` and `boundary` of group `in` (default) or `out` (`--layers out`, the derived layers).
* `work/widen2.pkl`, `work/bgn.pkl` (optional, group `in` only): the moved lines of the widening step replace the original ones.
* Config: `fields.boundary.name`, `sections.name_pattern` (features with a matching name are sections and are skipped).

## Outputs

* `work/xn_points.json`: list of `[x, y]` (crossings, or the ends of an overlapping part). Printed: the number of points.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/xn_points.py [-c rcs_config.json] [--layers in|out]
```

## How it works

1. `U` = union of all breaklines (widened where moved).
2. For each nodestring that is not a section, the coordinates of its intersection with `U` are collected.

## Checks / expected result

* Brenta: the original script used the derived layers before the new sections existed (`--layers out` reproduces that choice with today's layers, which hold sections that are skipped). With `--layers in` and the widening files the points follow the widened lines.

## Limits

* Only geometry is used: no check that the meeting points are real nodes of the mesh.
* Run it before `place.py` when `params.placement.weights.xn` is above zero.
