# verify3_dtm.py

Checks that the z of every bankpoint equals the value of the DTM cell under the point (no interpolation), and that no value is null or nodata. Read-only. Companion of `verify3.py`.

## Requirements

* OGR interpreter (`/usr/bin/python3`): `osgeo` (GDAL/OGR).

## Inputs

* `outputs.bankpoints` (GeoPackage in `paths.layers`) and `fields.bankpoints` (`name`, `z`).
* `inputs.dtm`: the DTM raster.

## Outputs

One line: number of bankpoints, maximum absolute difference, mismatches (> 1e-6 m), nulls and nodata, then `OK` or `**CHECK**`.

## Usage

```bash
cd <working folder>
/usr/bin/python3 <toolkit>/scripts/verify3_dtm.py [-c rcs_config.json]
```

## How it works

For each bankpoint it computes column and row of the DTM cell from the geotransform (floor of the coordinate difference over the pixel size), reads the cell and compares it with z.

## Checks / expected result

`OK`: maximum difference 0, no null, no nodata.

## Limits

* A point exactly on a cell edge falls in the cell given by the floor rule, the same rule the writers use.

Origin: Brenta project, `verify3_dtm.py`, 2026-11-18.
