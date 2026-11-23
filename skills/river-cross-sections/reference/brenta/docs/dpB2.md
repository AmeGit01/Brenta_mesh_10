# dpB2.py

Third pass (2026-11-18). Moves the whole B reach upstream so that section B00400 coincides exactly with the nodestring `idrometro_Borgo`. This is the point at Borgo where the most reliable flow rates of the model are measured. Previous: `dpB.py`, whose result it uses as reference; next: `export_B.py WD dpB2.pkl`, then `next_bed.py`, `obst.py`, `bank.py` and `assemble.py`.

## Requirements

* Interpreter: Anaconda `python3` (numpy, scipy, shapely, geopandas).
* Imported module: `core.py` from `WD/work` (`SP`, `pickle`, `np`).
* The script must be copied into `WD/work`.

## Input

* Argument 1: the working folder `WD`.
* Argument 2: the boundary file that contains the anchor nodestring, normally `WD/in/boundary_50m.gpkg`.
* `WD/work/cands.pkl` (`place.py`): candidates of the main reach (`main`) every 0.25 m, with penalties and flags.
* `WD/work/dpB.pkl` (`dpB.py`): the arrangement of 17 November (key `B`) and the indices of N and V, copied unchanged.
* `WD/xn_points.json` (`prep_inputs_nvb.py`): meeting points of nodestrings and breaklines.

## Output

* `WD/work/dpB2.pkl`, a dictionary with:
  * `N`, `V`: copied from `dpB.pkl`;
  * `B`: indices of the candidates of the B reach. At the position of the anchored section there is the nearest candidate, which is only a placeholder;
  * `anchor`: `k` (position in the reach, 8 = B00400), `nome`, `s` (chainage on the main reach), `x`, `y` (intersection of the nodestring with the centerline), `nx`, `ny` (unit normal towards the left end), `tL`, `tR` (distances of the two ends from the centre) and `coords` (the two vertices, left first).
* The print reports:
  * shift, chainage of the anchor, number of sections, first and last section;
  * minimum and maximum step and chord, deviation from the targets;
  * sections with straight-line distance outside 49.5–50.5 m and sections more than 0.13 m from the target;
  * sums of the penalties.

## Parameters and constants

* `ANCHOR_K = 8` and `ANCHOR_NAME = 'idrometro_Borgo'`: the anchored section and the nodestring. The nodestring must have 2 vertices and cross the centerline only once.
* `S_BRIDGE = 16327.97` and `MARGIN = 5`: as in `dpB.py`, no section between 5 m upstream of `Ponte_Bordignon_monte` and 20 m downstream.
* `WIN = 5` m: search window around each target.
* `W_DEV = 0.5`: cost per metre of deviation from the target.
* `ADD_END = False`: if true, it would add a section at the end when the last one stays more than 50.5 m from the end of the centerline. It is not used: on the Brenta that section would fall 12 m upstream of `BC_brenta_valle`, rotated by about 30° and with the right bankpoint on the edge of the domain.
* The other penalties are those of `dpB.py`: `pen5`, `hitO` (+1000), `hitB` (+10000), +50 for a toe less than 5 m from a point of `xn_points.json`, invalid candidates excluded.

## Usage

```bash
cp scripts/dpB2.py /path/to/WD/work/
```

```bash
python3 /path/to/WD/work/dpB2.py /path/to/WD /path/to/WD/in/boundary_50m.gpkg
```

Then:

```bash
python3 /path/to/WD/work/export_B.py /path/to/WD dpB2.pkl
```

(layout of `WD`: see [dpB.md](dpB.md), Usage section.)

## How it works

1. Computes the penalties of the candidates as `dpB.py` does.
2. Intersects the nodestring with the polyline of the candidate centres. This gives the chainage `s_a` (16655.68 m) and the centre of the anchored section, and orders the vertices with the left one first.
3. Computes the shift `D = s(B00400 old) − s_a`, equal to 16.57 m. The target of section k is `t_k = s_old_k − D`. The anchor is a fixed node, with no penalty.
4. Runs a layered dynamic programme, one layer per section. In each layer the valid candidates lie within `WIN` of the target. The cost of a candidate is its penalty plus `W_DEV` per metre of deviation from the target. The step between two consecutive sections must lie between 49.5 and 50.5 m along the centerline, and is a hard constraint. A straight-line distance outside 49.5–50.5 m instead costs 500 + 100·|chord − 50|, because the 50 m rule is measured along the centerline and on tight bends the straight line can come out shorter.
5. Rebuilds the best path, puts the placeholder back at the position of the anchor, and saves.

## Checks and limits

* Result of 18 November:
  * 354 sections, B00000 at s = 16253.25 of the main reach and B17650 at 17670.25 m in the B reach;
  * shift between 15.9 and 17.25 m;
  * step between 49.75 and 50.5 m;
  * a single straight-line distance outside tolerance: B11200–B11250, 47.85 m in the tight bend around s ≈ 27 470 m.
* In that bend the rigid shift does not find pairs with straight-line distance within 49.5–50.5 m even when the window is widened to 10 m. For this reason the chord is a soft constraint.
* The result must be read together with the geometric checks (`check_geom.py`, `verify2.py`). In particular it is checked that no section crosses a nodestring, except B00400 which coincides with `idrometro_Borgo`, and that none falls inside a bridge.
* The values of `S_BRIDGE`, `ANCHOR_K` and `ANCHOR_NAME` are fixed in the code.
