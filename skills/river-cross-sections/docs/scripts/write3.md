# write3.py

The single writer of the toolkit. It applies a JSON payload prepared by another script to the derived layers, after a tagged backup of every layer it touches. It also covers what the old `write2.py` did: replacing all sections, dropping and adding region points, rebuilding the centerline, centerpoints and bankpoints layers.

Origin: Brenta project, `write3.py` and `write2.py`, 2026-11-18.

## Requirements

* Interpreter: `/usr/bin/python3` (system), because it needs `osgeo` (GDAL/OGR). No shapely.
* The layers must be closed in the GIS (see Safety).

## Inputs

* Argument 1: the payload (JSON). Every key is optional and uses logical field names (mapped with `cfg.f`):
  * `bl`: `{fid: [[x,y],...]}` new geometry of breaklines;
  * `bd`: `{fid: [[x,y],...]}` new geometry of boundary features (name and id unchanged);
  * `rename`: `{fid: name}` gives boundary features a new name, after `secs`. The run stops if two features would share a name;
  * `secs`: `[{"name","coords"}]` replaces ALL section features of the boundary layer. Features whose name matches `sections.name_pattern` and whose fid is at least `sections.first_fid` are deleted (a nodestring with a lower fid keeps its place even if its name matches, e.g. a nodestring renamed as a section); the new ones are inserted in the given order with `fid = sections.first_fid + k` and `id = sections.first_id + k`;
  * `reg_drop`: `[fid,...]` region points to delete;
  * `reg_attr`: `{fid: {field: value}}` new attributes of existing region points (`name`, `mat_id`, `max_area`, `hole`; `null` clears the field). The fid and the position do not change, so an original point stays original;
  * `reg_new`: `[{"x","y","name","mat_id","max_area","hole"}]` new region points (`hole` is written only if not null);
  * `cl`: `[{"name","reach","coords","s0"}]`, `cp`: `[{"name","reach","s","x","y","dist_next"}]`, `bp`: `[{"name","section","s","x","y","z","dist_cp","kind","rule","prom"}]`. They rebuild the centerline, centerpoints and bankpoints layers; all three must be given together. A bankpoint with `z` null gets the value of the DTM cell under it.
* Argument 2: the backup tag (for example `20261118b`).
* Config: `outputs` (layers), `fields`, `sections` (`name_pattern`, `first_fid`, `first_id`), `project.crs`, `inputs.dtm`, `dtm.nodata`, `paths`.

## Outputs

* The modified derived layers.
* For every layer touched, a backup `<layer>_backup_<tag>.gpkg`, verified by SHA-256.
* Printed: `backup ok`, what was written, `written`.

## Usage

```bash
cd <working folder>
/usr/bin/python3 <toolkit>/scripts/write3.py [-c rcs_config.json] [--force-open] payload.json <tag>
```

## How it works

1. Checks, before writing anything: no unknown payload keys; no `-wal` file next to a layer to be written (the layer is probably open in QGIS); no backup with that tag.
2. Copies every touched layer to its backup and checks the SHA-256. With `--force-open` the `-wal` file is copied next to the backup too.
3. Applies, in this order: `bl`, `bd`, `secs`, `rename`, `reg_attr`, `reg_drop` then `reg_new`, then the rebuild of cl/cp/bp. Each file is changed in one transaction.
4. Geometries of lines are written as MultiLineStringZM with z = m = 0. New region fids start after the previous maximum (computed before the drops).
5. The rebuild deletes the three layer files and creates them again with the same schema (centerline: name, reach, length of the geometry, s0).

## Checks / expected result

* Exit with an error, nothing written, when a backup with the tag exists, when a `-wal` file exists (without `--force-open`), when a fid is not found, or when the new section fids collide with a non-section feature.
* Regression on Brenta: the payload of `sync_cp_bp.py` and a mixed payload (breaklines, all sections, region drops and additions, cl/cp/bp) written with the original scripts and with this one give identical layers (fids, attributes, exact coordinates).

## Limits

* No automatic rollback: restore from the backups of the tag.
* It does not check the geometry it writes: run the verification scripts afterwards.
* `secs` assumes the section fids are a contiguous block starting at `sections.first_fid`.
