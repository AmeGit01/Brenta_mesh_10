# cl.py

Computes the raw centerlines of the river, and of its branches, as minimum-cost paths on a fine Voronoi skeleton of the bed. The cost favours the centre of the channel. Every line is described in the config section `centerlines`. The raw lines are smoothed and resampled by `cl2.py`.

Origin: Brenta project, `cl.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy, scipy, networkx).

## Inputs

* `work/graph.pkl` (`graph.py`).
* Boundary layer of group `inputs` (nodestrings are read by name; field `fields.boundary.name`).
* Config section `centerlines`: list of lines, each
  * `name` (required): key of the line in all outputs;
  * `from` (required): nodestring name (its centroid is used) or `[x, y]`;
  * `to` (required): nodestring name, `[x, y]`, or `join:<other centerline name>` for a branch that ends on another line;
  * `waypoints` (optional): ordered list of nodestring names or `[x, y]` points the path must pass through. Use them to force the path into a given branch;
  * `cost` (optional): `centre` (default; cost = length / distance from the bed boundary) or `length` (plain shortest path);
  * `join_point` (optional, with `join:`): nodestring name or `[x, y]` where the branch ends. Default: the node of the other line that is closest, along the skeleton, to the last waypoint.
* Config `params.cl`:
  * `bed_classes`: face classes of the bed; `buffer`: buffer of the faces (m);
  * `min_island_area`: islands (holes of the bed) smaller than this (m2) are filled;
  * `seed_spacing`: Voronoi seed distance on the outline (m); `max_edge`: longest edge kept (m);
  * `min_boundary_dist`: floor of the boundary distance in the cost (m);
  * `bridge_min_nodes`, `bridge_max_gap`, `bridge_min_sep`, `bridge_cost_factor`: a secondary skeleton component with at least `bridge_min_nodes` nodes is linked to the others with up to two bridges, each shorter than `bridge_max_gap` (m) and at least `bridge_min_sep` (m) apart; a bridge costs `bridge_cost_factor` times its length.

If `centerlines` is missing, or a line has no `name`, `from` or `to`, the script stops and names the key. It also stops if a nodestring name is not found in the boundary layer, if a `join:` target is unknown, or if joins are circular.

## Outputs

* `work/rawcl.pkl`: dict with `P` (the bed polygon used) and one Nx2 array of path vertices per centerline, keyed by the config `name`. Coordinates are not yet smoothed or resampled.
* Printed: islands, seeds, components before and after the bridges, snapping distance of every waypoint, node count and length of every line, distance of a branch from the line it joins.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/cl.py [-c rcs_config.json]
```

## How it works

1. Reads and checks the `centerlines` section.
2. Merges the bed faces; `P` = outer polygon with only the islands larger than `min_island_area`.
3. Voronoi of points sampled on all rings of `P`; keeps vertices inside `P` and edges shorter than `max_edge`. Each edge gets a length `w` and a cost `c`.
4. Links the secondary components to the main one.
5. For each line (a branch after the line it joins): snaps `from`, waypoints and `to` to the nearest skeleton nodes and concatenates the shortest paths between consecutive points (weight `c` or `w` according to `cost`). For `join:`, the path then continues to the join point.
6. Saves `rawcl.pkl`.

## Checks / expected result

* After the bridges there should be one dominant component.
* A large waypoint snapping distance means the point is far from the bed skeleton: move it.
* The head/tail distances of a branch show how well it attaches to the line it joins.

## Limits

* The centre-preferring cost may cut between islands in very wide zones; the smoothing is done in `cl2.py`.
* At a split of the river the cost decides which branch the line takes; force another choice with `waypoints`.
