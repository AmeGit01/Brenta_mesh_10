# regions2.py

Chooses ONE region point per face of the final planar graph (breaklines + nodestrings + sections). Original points are never replaced. Faces that hold a configured preserved pair are left as they are. Faces without a suitable point get a new point at the pole of inaccessibility, with the attributes of the original region the face comes from.

Origin: Brenta project, `regions2.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* `work/near_nodes.json`, `work/secs_new.json`.
* Layers `outputs.boundary`, `outputs.regions` (current derived layers); `inputs.regions` (original region points).
* `work/graph.pkl` from `graph.py --layers out` run on the derived layers BEFORE this change: its faces are the base faces used to find the original region of a face.
* Config: `originals.region_fid_max` (fids up to it are original points, kept first), `rules.regions.clearance`, `fields.regions.*`, `fields.boundary.name`, `sections.name_pattern`.
* Config `params.regions2`: `preserved_pairs` (lists of fids), `report_points` (fids whose status is printed), `polylabel_tolerance`.

## Outputs

* `work/regions2.json`: `keep`, `drop` (sorted fids), `new` (`face`, `x`, `y`, `name`, `mat_id`, `max_area`, `hole`, `clear`), `nfaces`.
* Printed: number of faces and tiny ones, counts kept / dropped / new / errors, the dropped list, new and kept points closer than the clearance, new points by name, status of the report points.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/regions2.py [-c rcs_config.json]
```

## How it works

1. Polygonizes the new breaklines, nodestrings and sections.
2. For each face, lists the region points inside (originals first, then by fid).
3. A face holding a preserved pair keeps the pair and drops the others.
4. Otherwise the first point at least `clearance` from every line is kept and the others dropped.
5. In a narrow face an original point is kept (the one with most clearance).
6. Otherwise a new point at `polylabel` is created, unless an existing point is at least as clear. Its attributes come from the original region point in the same base face (or, if none, the first current point in the face).

## Checks / expected result

* `errors` must be empty. Points kept with clearance below the limit are expected only in wall and narrow bed faces.
* Brenta: on the test input, stdout and `keep` / `drop` / `new` identical to the original script (new points use logical keys: `name`, `hole`).

## Limits

* Faces with no region source (`errors`) get no point and must be handled by hand.
