# widen.py

Computes how far each top-of-bank line must move outward to reach the wanted width, and builds the new geometry of the moved lines. Optional step; it follows `chains.py` and precedes `apply_widen.py`.

Origin: Brenta project, `widen.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy, scipy).

## Inputs

* `work/graph.pkl`, `work/chains.pkl`.
* `work/cltab.pkl` from the centerline step: dict keyed by centerline name; only `[name]['q']` is used (centerline points every 1 m, index = chainage s in m). If a name is missing the script looks it up in `params.widen.cltab_alias`; otherwise it stops.
* Original boundary layer; locked lines (`cfg.locked_lines()`).
* Config `widening`:
  * `enabled`, `bank_class`, `wall_classes`;
  * `zones`: list of `{centerline, s_from, s_to, mode, min}`. The first zone that contains the chainage wins; `s_to` null = no limit. Mode `corridor`: top-to-top width >= `min`, the shift is split symmetrically. Mode `bank`: each bank, toe to top, >= `min`;
  * `min_gap_outer`: at least this distance stays to the next outer line;
  * `simplify` (m, line simplification), `merge` (m, vertices closer than this are thinned), `densify` (optional, default `merge`);
  * `never_move`: region names or class names; lines touching such a face do not move.
* Config `face_classes.fixed` / `editable`, `rules.min_angle_deg`.
* `params.widen`: `cltab_alias`, `ray_range` (1500 m), `station_radius` (3 m), `min_shift` (1 mm), `oblique_cos` (0.5).

## Outputs

* `work/widen.pkl`: dict with `newf` (fid -> new vertices of the moved top lines), `bmove` and `endT` (new positions of the "forced" T-junction vertices), `bgeo` (original boundary vertices), `ST` (names, matrix `i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR`), `sL`, `sR` (shifts per row), `PTS`, `SH`, `DN` (top stations, shifts, outward directions), `rejected` (lines whose move was rejected by the angle rule).
* Printed: points limited by the clearance, widened fraction and maximum shift per centerline and per zone, number of top lines and of locked ones, forced T points, mixed lines skipped, changed lines, moves rejected by the angle rule.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/widen.py [-c rcs_config.json]
```

## How it works

1. Builds ray queries on three outlines: toe (`fixed` classes), top (fixed + bank + wall classes) and outer (also the other editable classes).
2. At each centerline point, along the left normal: toe distances `tL`, `tR`; top distances `cL`, `cR` beyond the toe; width `W = cL + cR`; distances `oL`, `oR` to the next outer line.
3. The zone of the point gives the shift (modes above). The shift is capped at `gap - min_gap_outer`.
4. Top stations (centre +- normal * top distance) carry the shift. Each vertex of a top line takes the shift of the nearest station within `station_radius`.
5. Ends of other lines or of boundary lines that lie on a top line (T junctions) are "forced" vertices. They move along the incident line, or along the normal if the angle is too oblique.
6. For each top line: densify, move, split at the forced vertices, simplify, thin.
7. Lines touching a never-move face, mixed lines and locked lines stay unchanged.
8. Angle rule: if the new line has more vertices sharper than `rules.min_angle_deg` than the old one (or a sharper one), the move is rejected and the line stays as it was.

## Checks / expected result

* Look at "clamped by clearance" (a high number means little room), the widened fractions, the mixed lines and the rejected moves.
* Brenta: 266 changed lines; identical to the original script.

## Limits

* The new geometry is validated by `apply_widen.py`.
* Points where the normal misses the toe or top on one side get no shift.
* Only the in-line angle is checked here; the angles where lines meet are checked in `apply_widen.py`.
