# graph.py

Builds the planar graph of the breaklines and boundary lines. The lines are noded exactly (`unary_union`) and the faces are made with `polygonize`. Each face gets the region point that lies inside it. The result, `work/graph.pkl`, is the base of `next_bed.py`, `obst.py` and `regions2.py`.

Origin: Brenta project, `graph.py`, 2026-11-09.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* Layers of group `inputs` (default, the original layers) or of group `outputs` (`--layers out`, the derived layers): `breaklines`, `boundary`, `regions`.
* Config: `fields.regions.name`, `fields.regions.mat_id`. Geometry of the other layers only; empty or null breaklines are dropped.

## Outputs

* `work/graph.pkl`: dict with
  * `faces`: list of Polygons (faces of the planar graph);
  * `fr`: face index -> positions of the region points inside it;
  * `rows`: one dict per face that has a region point: `face`, `fid` (list), `nome` and `mat` of the FIRST point, `area`.
* Printed: number of breaklines and empty ones, number of faces, tiny faces, points in faces, faces per number of points, faces over 1 m2 without a point, points outside every face, table region name / faces / hectares, and the count of faces per face class (`cfg.face_class`).

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/graph.py [-c rcs_config.json] [--layers in|out]
```

Use `--layers out` to get the faces of the derived layers (what `next_bed.py`, `obst.py` and `regions2.py` need when they work on the current model).

## How it works

1. Reads the three layers and drops empty breaklines.
2. Explodes every geometry into plain 2D lines, nodes them with `unary_union` and polygonizes.
3. Assigns each region point to the face that contains it (STRtree, `within`).
4. Builds `fr` and `rows` (name and material of a face are those of its first point) and saves the pickle.

## Checks / expected result

* "faces per npoints" should show only 0 and 1 points. More points: the face takes the name of the first one.
* "pts outside" should be empty. Few faces over 1 m2 without a point.
* Brenta: on the original layers 173 faces; identical to the original script (faces, `fr`, `rows`).

## Limits

* Faces without a region point are not in `rows`, so later steps ignore them.
* Lines that do not touch exactly do not close a face: there is no snapping.
