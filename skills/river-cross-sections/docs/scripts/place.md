# place.py

Generates a candidate section every `candidate_step` metres along each centerline used by a reach and evaluates every candidate: distances from the centerline to the toe and to the top of bank on both sides, near-node violations on the toe crossings, crossings with nodestrings and inner breaklines, and crossings at an angle sharper than `rules.min_angle_deg`. It also saves the faces of the widened planar graph. The stations are chosen later by `dp.py`.

Origin: Brenta project, `place.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (numpy, scipy, shapely 2.x, geopandas).
* Slow: about 5 to 10 minutes for 34 km of main channel (one ray query pair per candidate).

## Inputs

* `work/cltab.pkl` (`cl2.py`): `q` of every centerline named by a reach `source`.
* Original layers `breaklines`, `boundary`, `regions` (cfg `inputs`).
* `work/widen2.pkl`, `work/bgn.pkl` (`apply_widen.py`): optional. Without them the original lines are used (widening disabled). If `widening.enabled` is true and they are missing, the script stops.
* `work/xn_points.json` (`xn_points.py`): needed only when `params.placement.weights.xn` > 0.
* Config: `reaches[*].source`; `rules.near_node.radius` and `.ignore_below`; `rules.min_angle_deg`; `params.placement`: `toe_classes`, `top_classes`, `candidate_step`, `ray_range`, `tangent_half`, `perp_window`, `extent_beyond_toe`, `extent_inside_top`, `wide_section`, `min_beyond_toe`, `angle_penalty`, `weights.xn`.

## Outputs

* `work/cands.pkl`: dict keyed by centerline name; each value holds arrays aligned per candidate:
  * `ss` (s, m), `P` (x, y on the centerline), `n` (left unit normal, from the chord between s-`tangent_half` and s+`tangent_half`);
  * `tL`, `tR`: centerline to toe on the + and - side; `cL`, `cR`: centerline to the first top-of-bank line beyond the toe (NaN if absent);
  * `eL`, `eR`: half-extent of the approximate section on each side;
  * `pen_near` (0..2): toe crossings closer than the near-node radius to a toe vertex (a vertex that coincides within `ignore_below` is skipped and the next one is used);
  * `pen_xn` (0..2): toe crossings closer than that radius to a meeting point of a nodestring and a breakline;
  * `pen_angle`: number of crossings of the approximate section with any line (toe, top, inner line, nodestring) at an angle below `rules.min_angle_deg`;
  * `perp_dev`: angle in degrees between the section normal and the normal of the longer chord (`perp_window`);
  * `hitB` / `hitO`: 1 if the approximate section crosses a nodestring / an inner breaklines segment (a line that is neither toe nor top);
  * `ok`: toe and top found on both sides.
* `work/newfaces.pkl`: `fc` (faces) and `rows` (`{face, nome}`, one per face with a region point; the first point gives the name).
* Printed: faces, toe vertices, obstacles; per centerline the number of candidates, valid ones, and how many hit a nodestring, hit an inner line, violate the near-node rule, are close to a meeting point, have a sharp crossing angle.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/place.py [-c rcs_config.json]
```

## How it works

1. Builds the planar graph of the (widened) breaklines and the nodestrings; each face takes the name of its first region point.
2. Toe segments = outline of the `toe_classes` faces; top segments = outline of the `top_classes` faces.
3. For each centerline, candidates every `candidate_step` m; the normal at each is perpendicular to the chord between s-1 and s+1 m. Rays of +-`ray_range` m give the nearest toe hits on both sides and the first top hit beyond each toe.
4. Near-node rule: each toe crossing is compared with the two nearest toe vertices.
5. Approximate section: toe + `extent_beyond_toe` on each side, but not beyond `extent_inside_top` inside the top line; for narrow sections at least toe + `min_beyond_toe`. It is tested against the nodestrings, the inner segments (all that are neither toe nor top), and all line segments for the crossing angle.

## Checks / expected result

* Brenta, original lines of the November work: 135 924 candidates on the main channel and 12 232 on the Brenta vecchio, all valid. With the angle penalty off the arrays equal those of the original `place.py` (see the regression in the test report).

## Limits

* The extent test is asymmetric as in the original: the left side compares `tL+cR` with `wide_section`, the right side `tL+tR`. It only affects the choice of candidates, not the bankpoints.
* The approximate extent is not the final section: `bank.py` finds the bankpoints.
* A crossing exactly at a line vertex counts once per segment for the angle rule.
