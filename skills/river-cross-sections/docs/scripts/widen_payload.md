# widen_payload.py

Converts the result of the bank widening into a payload for `write3.py`. The widened breaklines and the extended nodestrings must be in the derived layers before the sections are placed on them and the near-node rule is applied.

## Requirements

* Interpreter: geo (geopandas, numpy).

## Inputs

* `work/widen2.pkl`: key `newf`, the new vertices of every changed breakline.
* `work/bgn.pkl`: the new vertices of every changed nodestring. Optional.
* The derived breaklines and boundary layers, used only to check that every fid exists.
* The locked lines (`cfg.locked_lines()`).

## Output

* `work/widen_payload.json` (or the path given as argument): `{"bl": {fid: [[x, y], ...]}, "bd": {fid: [[x, y], ...]}}`.
* Printed: the number of breaklines and nodestrings changed.

The script stops in two cases:
* a fid does not exist in the derived layers;
* the widening touches a locked line.

## Usage

```bash
cd <working folder>
<geo python> <skill>/scripts/widen_payload.py
<ogr python> <skill>/scripts/write3.py work/widen_payload.json <tag>
```

Then run `graph.py --layers out`, `check_widen.py` and `check_angles.py` on the written layers.

## Limits

It only converts. The widening has already been validated by `apply_widen.py`, which checks the faces, the connections and the region points.

Origin: written for the skill on 2026-11-20. On the Brenta the widened lines were written by the obsolete `write.py`.
