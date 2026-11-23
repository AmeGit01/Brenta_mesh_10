# cl.py

Step 4. Computes the raw centerlines of the main channel ("asta", from `BC_caldonazzo` to `BC_brenta_valle`) and of the Brenta vecchio as minimum-cost paths on a fine Voronoi skeleton of the bed; the cost favours the centre of the channel. It follows `net.py`/`graph.py` and precedes `cl2.py`.

## Requirements

* Anaconda Python: geopandas, shapely 2.1, numpy, scipy (`Voronoi`, `cKDTree`), networkx.
* Imports `core.py` (from `WD/work`): `load_graph`, `cls`, `Polygon`, `np`, `shapely`, `gpd`, `pickle`, `SP`.

## Input

* `WD/work/graph.pkl` (`graph.py`), through `load_graph()`: faces with class `bed`.
* `WD/in/boundary.gpkg`, indexed by `nome`; uses the centroids of `BC_caldonazzo`, `BC_brenta_valle`, `divergenza_valle_brenta_vecchio`, `boale_brenta_vecchio_monte`, `boale_brenta_vecchio_valle`, `check_portata_Brenta_vecchio`.

## Output

* `WD/work/rawcl.pkl`: dict `P` (bed polygon used for the skeleton), `main` (Nx2 array of the vertices of the main path), `vecchio` (Mx2 array of the Brenta vecchio). Coordinates EPSG:25832, not yet smoothed or resampled. Read by `cl2.py`.
* `WD/work/altmain.pkl`: Nx2 array of an alternative path of the main reach that goes through the southern meander; for comparison only (read by `esplorativi/up.py`).
* stdout: areas and centroids of the holes (islands), number of seeds, connected components before and after the links, contacts used, length of main/vecchio, attachment distances of the waypoints, head/tail distances of the vecchio from the main.

## Parameters and constants

* `buffer(0.02)` m: union of the bed faces.
* Islands: only holes with area > 1000 m² are kept (line 10).
* Voronoi seeds every **0.6 m** on all rings (line 12; the original comment cites 0.5/1.5 m but the code uses 0.6 everywhere).
* Admitted edges: length < 40 m; cost `c = d / max(min(distance from the boundary of the two vertices), 0.15)` (line 19), weight `w = d`.
* Secondary components to link: >= 80 nodes; contact allowed if distance <= 25 m; two distinct contacts more than 50 m apart; bridge cost `2*distance`.
* "Meander" point `(678150, 5096930)` (line 46), manual waypoints of the Brenta vecchio `(687960, 5102512)` and `(688400, 5102655)` (line 54), confluence point `(689850, 5102944)` (line 63): coordinates chosen by hand, change them if the geometry changes.

## Usage

```bash
python3 cl.py /path/to/WD
```

## How it works

1. Merges the `bed` faces; `P` = outer polygon with only the islands > 1000 m².
2. Voronoi of the points sampled every 0.6 m on the outline; keeps the vertices inside `P` and the edges < 40 m, with a cost that penalizes closeness to the boundary (distance from the nearest seed, minimum 0.15 m).
3. Secondary connected components (>= 80 nodes) are linked to the others with at most two bridges between the nearest points.
4. `A` and `Z` = nodes nearest to the centroids of `BC_caldonazzo` and `BC_brenta_valle`; `mp` = minimum-cost path with cost `c`.
5. Alternative path `A -> M1 -> Z` through the meander, saved in `altmain.pkl` (inside a `try`; if it fails it prints `alt fail`).
6. Brenta vecchio: concatenates the shortest paths (weight `w` = length) between the sorted waypoints, then extends it to the confluence point (689850, 5102944).
7. Prints the lengths and saves `rawcl.pkl`.

## Checks and limits

* Check "comps after": there must be one dominant component; "bridged comp" shows the contacts used (small distances = good attachment).
* A high "wp dist" means a waypoint attached to a distant node.
* The variable `order` (line 26) is computed but never used; `kdm` is only used by the final prints.
* The path with cost `c` follows the centre of the channel: in very wide zones it may "cut" between islands; the smoothing is in `cl2.py`.
* The hard-coded waypoints make the script specific to this dataset.
