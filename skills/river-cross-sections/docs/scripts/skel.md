# skel.py

Builds a skeleton (medial axis) of the riverbed from the Voronoi diagram of points sampled along its outline, and saves it as a networkx graph. It is a first, coarse version: `cl.py` recomputes the finer skeleton that the centerlines actually use.

Origin: Brenta project, `skel.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy, scipy, networkx).

## Inputs

* `work/graph.pkl` (`graph.py`): faces and region names.
* Config `params.skel`:
  * `bed_classes`: face classes (see `face_classes` in the config) that form the bed;
  * `corridor_classes`: classes that form the corridor (bed + banks + walls);
  * `buffer`: buffer (m) applied to every face before the union, so that adjacent faces fuse;
  * `seed_spacing`: distance (m) between Voronoi seeds along the outline;
  * `max_edge`: longest skeleton edge kept (m).

## Outputs

* `work/skel.pkl`: dict with `bed` and `cor` (unions of the faces), `g` (`networkx.Graph`, nodes = Voronoi vertex indices, edge attribute `weight` = length in m), `vv` (coordinates of the Voronoi vertices).
* Printed: geometry type, number of parts and hectares of `bed` and `cor`; the 8 largest bed parts; number of seeds; sizes of the largest connected components.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/skel.py [-c rcs_config.json]
```

## How it works

1. Builds `bed` and `cor` as unions of buffered faces of the chosen classes.
2. `P` = the single largest part of the bed, or the whole multipolygon if there are several parts.
3. Samples the outlines (outer ring and holes) at `seed_spacing`.
4. Runs `Voronoi`; keeps the vertices inside `P`.
5. Keeps the Voronoi edges between inner vertices that are shorter than `max_edge` and fully inside `P`.

## Checks / expected result

* The largest component should cross the whole river; the others should be small.

## Limits

* The skeleton has side branches toward indentations of the outline.
* With coarse seeds the axis position is uncertain in narrow reaches; this is why `cl.py` uses a finer spacing.
* No other script of the skill reads `skel.pkl`; it is a diagnostic.
