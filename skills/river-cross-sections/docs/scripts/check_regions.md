# check_regions.py

Checks that the derived region-point layer can be used directly as the region-marker layer for BASEmesh quality meshing. The planar graph is built differently from `verify3.py`, so the two scripts check each other. It writes nothing.

## Requirements

* Geo interpreter (`~/anaconda3/bin/python3`): geopandas, shapely 2.x, numpy.

## Inputs

* `outputs.regions`, `outputs.breaklines`, `outputs.boundary`; `inputs.regions` (originals, for the hole points).
* `fields.regions` (`name`, `mat_id`, `max_area`, `hole`), `project.crs`.
* `rules.regions`: `clearance` (m), `snap` (T-junction tolerance, m), `sliver_width` (m), `robust_rounding` (list of grid sizes, m).

## Outputs

Print only: a numbered list, `OK` or `**CHECK**` for each check.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/check_regions.py [-c rcs_config.json]
```

## How it works

1. **Layer structure:** `Point`, expected CRS, no Z, no null, empty or invalid geometry.
2. **Coincident points** (within 0.1 mm).
3. **Attributes:** no null name, `mat_id` or `max_area`; `max_area` > 0; one `mat_id` per name. Material ids shared by several names are printed (allowed).
4. **Names with more than one `max_area`:** informative.
5. **Hole points:** same fids and positions as in the original layer.
6. **T-junctions:** counts end points closer than `snap` to another line without touching it; each is connected with `shapely.snap`, which inserts it as a vertex of the line it touches.
7. **Planar graph:** `shapely.node` on all lines, split into segments with coordinates rounded to 1e-7 m, drop duplicates (overlapping lines), `polygonize_full`.
8. **Points** outside every face, or in more than one face.
9. **Faces without a point:** real faces are distinguished from slivers (inscribed circle radius < `sliver_width`) made by nearly coincident lines.
10. **Faces with more than one point:** reports whether the attributes agree.
11. **Robustness:** repeats the graph after rounding line coordinates to each grid in `robust_rounding` (a mesher merges nearby vertices). No point may change face mates and no empty face may exceed 1 m2.
12. **Clearance:** points closer than `clearance` to a line.
13. **Smallest and narrowest faces:** informative.

## Checks / expected result

All numbered checks `OK`; items 4, 14 and 15 of the list are informative. A real face without a point, or a point in two faces, is a `**CHECK**`.

## Limits

* The graph follows the project rule: end points within `snap` are connected, nodestrings count as lines. It does not reproduce the exact BASEmesh code.
* Slivers are recognised only by width, not by origin.
* Output order of dictionaries printed from sets (for example check 4) can change between runs.

Origin: Brenta project, `check_regions.py`, 2026-11-19.
