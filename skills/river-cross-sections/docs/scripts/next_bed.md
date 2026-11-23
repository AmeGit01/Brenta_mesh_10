# next_bed.py

If the bed of a different channel lies just beyond the bank of a section, this script caps the bankpoint search distance on that side, so that the search stops a margin before the other bed. It runs before `obst.py` and `bank.py`.

Origin: Brenta project, `next_bed.py`, 2026-11-09.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (shapely 2.x, numpy).

## Inputs

* `work/graph.pkl` (`graph.py`): faces and region names. Faces of class `bed` (`cfg.face_class(name) == 'bed'`) give the toe lines.
* `work/sec_in.json`: per section `x`, `y`, `nx`, `ny` (unit normal, + = left), `tL`, `tR` (toe distances), `stream`, `s`.
* Config `params.next_bed` (metres along the normal): `ray_range`, `margin_before_edge`, `own_toe_skip`, `search_past_toe`, `window_margin`.

## Outputs

* `work/sec_in.json`, OVERWRITTEN in place, with `maxL` / `maxR` (distance from the centerpoint) where a cap applies.
* Printed: one line per cap and `caps N`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/next_bed.py [-c rcs_config.json]
```

## How it works

1. Takes the outline of the union of the `bed` faces and builds a ray caster.
2. For each section, casts a ray along the normal in both directions and collects the signed distances of the bed edges.
3. On each side, keeps the hits beyond the own toe (+ `own_toe_skip`).
4. If the first one lies within `search_past_toe + window_margin` of the toe, the cap is `hit - margin_before_edge`. A cap is only lowered, never raised, so the script is idempotent.

## Checks / expected result

* On the 735 Brenta sections (inputs rebuilt from the current layers) output and `sec_in.json` are identical to the original script (20 caps).

## Limits

* `graph.pkl` must come from the layers the sections were designed on (use `graph.py --layers out` on the derived layers).
* `search_past_toe` should match the toe window of `bank.py` (`params.bank.toe_window`).
