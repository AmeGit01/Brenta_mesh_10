# init_outputs.py

Creates the derived layers (breaklines, boundary, regions) as exact copies of the original ones, and records the SHA-256 of the originals so that later checks can confirm that they never changed. The toolkit never edits the originals.

Origin: new script of the toolkit (no Brenta original).

## Requirements

* Plain python (standard library only; `sqlite3` is used only with `--force-open`).

## Inputs

* Config: `inputs` (breaklines, boundary, regions, dtm), `outputs`, `paths`.
* The original layers in `paths.layers`.

## Outputs

* The derived GeoPackages `<outputs.*>.gpkg` in the layers folder.
* `work/sha_originals.txt`: lines `<sha256>  <path relative to the working folder>` (the format of `sha256sum`).
* Printed: `OK` or `**CHECK**` for each copy.

## Usage

```bash
cd <working folder>
python3 <toolkit>/scripts/init_outputs.py [-c rcs_config.json] [--dtm] [--force-open]
python3 <toolkit>/scripts/init_outputs.py --check      # later: are the originals unchanged?
```

## How it works

1. Refuses if a target (or its `-wal`) exists, or if an original has a `-wal` file (open in the GIS) unless `--force-open`.
2. Writes the SHA-256 of the originals (the DTM too with `--dtm`; it is a large file).
3. Copies each original byte by byte and checks that the SHA-256 is equal. With `--force-open` the copy is made with the SQLite backup API (the `-wal` content is included) and checked by feature counts.
4. `--check` recomputes the hashes and compares them with the file; exit code 1 if something changed.

## Checks / expected result

* Three `OK` lines. A second run stops with `target exists`.

## Limits

* It does not create the centerline, centerpoints and bankpoints layers: `write3.py` builds them from a payload.
