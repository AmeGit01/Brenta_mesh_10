# dp.py

Chooses the section stations of every reach by dynamic programming over the candidates of `place.py`. One programme serves all reaches. Along the centerline the sections are `sections.spacing` +- `sections.tol` apart. Priorities, strongest first: no crossing of a nodestring or an inner breakline, no crossing of a section of an earlier reach; then no near-node violation, no toe crossing near a meeting point of nodestring and breakline, no crossing angle sharper than `rules.min_angle_deg`; then spacing close to the target and perpendicularity to the course. An anchor (a section that must coincide with a nodestring) is fixed exactly.

Origin: Brenta project, `dp.py`, `dpB.py`, `dpB2.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (numpy, shapely 2.x, geopandas). Takes seconds.

## Inputs

* `work/cands.pkl` (`place.py`); the original `boundary` layer (and `work/bgn.pkl` if present) for the nodestrings of anchors, keep-clear zones and positions given as nodestring.
* Config:
  * `sections.spacing`, `sections.tol`, `sections.digits`, `sections.name_pattern`;
  * `reaches[*]`: `code`, `source` (centerline name), `first_number`, `start`, `end` (see below);
  * `anchors`: list of `{section, nodestring}`; the section number must be `first_number` plus a multiple of the spacing;
  * `params.placement`: `weights` (`boundary`, `inner`, `obstacle`, `near`, `xn`, `angle`, `perp`, `step`, `chord_base`, `chord`, `invalid`), `extent_beyond_toe`, `extent_inside_top`, `end_gap`, `farthest_back`, `reachable_below`, `keep_clear`.
* Reaches are solved in config order; each treats the approximate sections of the earlier reaches as obstacles (weight `obstacle`).
* Position of a reach on its centerline (`start`, `end`): `{"s": metres}`, `{"nodestring": name}` (crossing of that nodestring with the centerline, must be a single point) or `{"section_of": code}` (the last, or for an end the first, section of another reach already placed).
  * `start`: the first section is at start + `first_number` within `window` (half-width, default `sections.tol`); `prefer_target` (default true) adds the cost `step` x (distance from the target)^2 to the first section.
  * `end`: also `{"count": n}` (exact number of sections) or `{"line_end": true}`; optional `gap` (minimum distance of the last section from the end; default `params.placement.end_gap` for the line end, 0 otherwise) and `rule`: `"window"` (cheapest end in [end - spacing - tol, end - gap]) or `"farthest"` (farthest end whose cost is below `reachable_below`, then the cheapest within `farthest_back` m of it). With `"truncate_full": true` (and `s`, `nodestring` or `count`) the chain is solved to the end of the line with that rule and gap, and only the sections up to `s` (or the first `count`) are kept. The dropped tail still counts as obstacle for reaches on another centerline.
* Optional `reaches[*].reference` = `{"dp": file, "window": 5.0, "weight": 0.5}` (needs an anchor in the reach): re-places the reach keeping an earlier placement. `dp` is an earlier `dp.pkl`; its stations of the reach (same number of sections) are shifted rigidly so that the anchored section matches, and each new station must be within `window` m of its target, at the cost `weight` x distance.
* `params.placement.keep_clear`: list of `{nodestring, source, reach (optional list of reach codes), before, after}`; no section of those reaches lies between `before` m upstream and `after` m downstream of the crossing of the nodestring with the centerline `source`.

## Outputs

* `work/dp.pkl`: dict keyed by reach code: `source`, `idx` (candidate indices in section order; an anchor slot holds the nearest candidate), `anchors` (list of `k`, `section`, `nodestring`, `s`, `x`, `y`, `nx`, `ny`, `tL`, `tR`, `coords`: the section is the nodestring, left vertex first), `names`.
* Printed per reach: number of sections and names, first and last `s`, cost; chord range and violations; counts of crossings (nodestrings, inner breaklines, earlier reaches), near-node violations, meeting-point violations, sections with a crossing angle sharper than the limit, maximum perpendicularity deviation; then `OK` or `**CHECK**`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/dp.py [-c rcs_config.json]
```

## How it works

1. Penalty per candidate = weighted sum of the flags of `place.py`; invalid candidates and keep-clear zones get `invalid` and are never used.
2. A step between two sections is allowed when the distance along the line is spacing +- tol (hard); its cost is `step` x (distance - spacing)^2, plus `chord_base` + `chord` x |chord - spacing| if the straight distance between the centre points is outside spacing +- tol (soft: in a tight bend the chord can be shorter).
3. Without anchor and with a free end: forward pass over all candidates, then the end rule. Else, with `count` or anchors: a layered programme with exactly the needed number of steps (one layer per section).
4. Anchors split the reach. The part before the first anchor is counted back from it (so the start window of `start` is not applied; a message gives the first section and the nominal start). Between anchors and from the last anchor the same programme runs with the anchor as a fixed node (its position is the intersection of the nodestring with the polyline of the candidate centres).
5. The approximate sections of the chosen stations (anchors: the nodestring) become obstacles of the next reaches.

## Checks / expected result

* `OK` when no chord is outside spacing +- tol and no section crosses a nodestring, an inner breakline or a section of an earlier reach. Otherwise `**CHECK**`: the lines list where; a violation can be accepted by the user with an entry of `exceptions.spacing`.
* Near-node, meeting-point and angle counts are penalties, not stops: they are reported. Use `check_near_nodes.py` later for the final geometry.
* Brenta, original lines with only the original constraints (angle penalty and `xn` off, no anchors, no keep-clear zone): the 676 main-channel and 61 Brenta-vecchio stations equal those of the original `dp.py`. The B reach without anchor equals the original `dpB.py`; with the anchor and the `reference` option it equals the original `dpB2.py` (and 340 of the 340 delivered stations that were not edited by hand).
* Brenta N and V with the original constraints: 319 of 320 and 58 of 58 delivered stations that were not edited by hand match (the other one, N00150, was moved by hand). With the new penalties (`xn`, angle) the N chain changes after about s = 8 km; this is intended.

## Limits

* The end rule differs between the original main channel (`window`) and the Brenta vecchio (`farthest`): choose per reach.
* With an anchor the start window is informational only. Without the `reference` option an anchored reach is placed freely: it need not coincide with an earlier placement (same constraints, other choice among equal-cost chains).
* The `reference` option supports one anchor shift per reach: targets use the shift of the first anchor.
* The perpendicularity deviation compares the local normal (chord of +-`tangent_half`) with the normal of the chord of +-`perp_window`; the weight is 0 by default.
