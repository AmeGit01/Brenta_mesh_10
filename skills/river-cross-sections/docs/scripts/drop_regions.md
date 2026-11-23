# drop_regions.py

Deletes region points (by fid) from the derived regions layer, after a tagged backup verified byte by byte. All other features, the fields, the geometry type, the CRS and the spatial index stay as they are.

Origin: Brenta project, `drop_regions.py`, 2026-11-19. (`write3.py` can do the same with the payload key `reg_drop`, together with other changes.)

## Requirements

* Interpreter: `/usr/bin/python3` (system, GDAL/OGR).
* The layer must be closed in the GIS (see Safety).

## Inputs

* Arguments: the backup tag, then the fids to delete.
* Config: `outputs.regions`, `fields.regions` (name, mat_id, max_area), `paths`.

## Outputs

* The edited layer (one transaction) and the backup `<regions layer>_backup_<tag>.gpkg`, identical to the layer before the change.
* Printed: for every deleted fid, name, mat_id, max_area and geometry.

## Usage

```bash
cd <working folder>
/usr/bin/python3 <toolkit>/scripts/drop_regions.py [-c rcs_config.json] [--force-open] <tag> <fid> [<fid> ...]
```

## How it works

1. Stops if the backup exists or if a `-wal` file exists next to the layer (unless `--force-open`).
2. Copies the layer to the backup and compares the two files byte by byte.
3. Stops (leaving the layer unchanged) if a fid does not exist.
4. Deletes the fids in one transaction and prints a record of each.

## Checks / expected result

* Regression on Brenta: same stdout (apart from the header and paths) and identical resulting layer as the original script.

## Limits

* It does not check the planar graph. Run the face checks afterwards.
