# check_widen.py

Print-only verification of the widening, read back from the derived layers: which boundary lines and breaklines changed, whether a changed line crosses another, whether the widths reach the targets of `widening.zones`, and whether new acute angles appeared. Optional step.

Origin: Brenta project, `check2.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* Derived layers `breaklines` and `boundary` (outputs) and the original ones (inputs); original `regions` layer (its points give the face names; faces with only new points give NaN widths).
* `work/cltab.pkl` (centerline points per name, see `widen.py`).
* Config: `widening.zones` (optional `check_min` per zone = limit used here, default `min`), `widening.bank_class`, `widening.wall_classes`, `face_classes.fixed`, `rules.min_angle_deg`, `params.widen.cltab_alias`, `fields.boundary.name`, `fields.regions.name`, `sections.name_pattern`.

## Outputs

* Nothing on disk. Printed sections:
  * A: boundary lines changed (fid, name, maximum shift);
  * B: breaklines changed;
  * C: changed lines that cross another line; lines that are not simple;
  * D: faces rebuilt from the layers (section nodestrings left out) and faces with a region point;
  * E: widths per zone, every 0.5 m along the centerline. Corridor zones: `W` (top to top) statistics and runs below the limit. Bank zones: bank widths `SL`, `SR` and runs below the limit;
  * G: for the crossings of C, whether they already existed in the original;
  * H: sections that meet exactly 3 breaklines (information);
  * I: new acute angles in the changed lines (inside a line and where lines meet), pre-existing ones counted separately.
* Last line `OK` or `**CHECK**` (new crossings or new acute angles).

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/check_widen.py [-c rcs_config.json]
```

## How it works

1. Compares geometries layer against original.
2. Rebuilds the planar graph, names the faces, and builds ray queries on toe and top outlines.
3. Samples each zone's centerline (normal from the chord s-1..s+1), measures toe and top distances on both sides.
4. Runs the angle comparison on changed lines.

## Checks / expected result

* C should be empty or all pairs pre-existing (G). E: no run below the limit except where the clearance cap or a never-move face prevents the widening.
* Brenta: identical measurements to the original `check2.py`.

## Limits

* The centerline is the 1 m polyline of `cltab.pkl`, not a layer.
* Widths are only measured where the normal crosses a toe and a top edge on both sides.
