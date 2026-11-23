# skel.py

Step 2. Builds a skeleton (medial axis) of the bed ("bed") from the Voronoi diagram of points sampled along the outline, and saves it as a networkx graph. It follows `graph.py` and precedes `net.py`. The finer skeleton actually used for the centerlines is recomputed by `cl.py`; this step is the first version, used by `net.py`.

## Requirements

* Anaconda Python: geopandas, shapely, numpy, scipy (`Voronoi`), networkx.
* Does not import `core.py` (it repeats the logic of `cls` with the lambdas `isbed`/`isbank`).

## Input

* `WD/work/graph.pkl` (`graph.py`): `faces`, `rows` (fields `face`, `nome`).

## Output

* `WD/work/skel.pkl`: dict with `bed` (geometry of the union of the bed faces), `cor` (union of bed + sponda/muro, the "corridor"), `g` (`networkx.Graph`, nodes = indices of the Voronoi vertices, attribute `weight` = edge length in m), `vv` (array of the coordinates of the Voronoi vertices). Read by `net.py`.
* stdout: geometry type, number of parts and hectares of `bed` and `cor`; the 8 largest parts of the bed (area, bounds, number of holes); number of seeds; sizes of the 6 largest connected components of the skeleton.

## Parameters and constants

* `buffer(0.02)` (lines 11-12): 2 cm, to join the adjacent faces.
* Seed spacing `1.5` m (line 20).
* Maximum edge length `d<30` m (line 29).
* `isbed`/`isbank` (lines 9-10): lists of the bed class names and of the sponda/muro class names. Keep them aligned with `core.cls`.

## Usage

```bash
python3 skel.py /path/to/WD
```

## How it works

1. Loads `graph.pkl`; builds `bed` and `cor` as the union of the faces with a 2 cm buffer.
2. `P` = the single part of the bed, or the whole multipolygon.
3. Samples the outlines (outer and holes) every ~1.5 m.
4. `Voronoi` of the seeds; keeps the vertices inside `P`.
5. Builds the graph with the Voronoi edges between interior vertices, shorter than 30 m and fully contained in `P`.
6. Prints the connected components and saves.

## Checks and limits

* The skeleton includes side branches ("whiskers") toward indentations of the outline; they are handled downstream (`net.py` uses shortest paths).
* The largest component should cross the whole river; check that the others are small.
* With seeds every 1.5 m the axis position is uncertain by about this order in narrow reaches: for this reason `cl.py` rebuilds the skeleton with seeds every 0.6 m.
