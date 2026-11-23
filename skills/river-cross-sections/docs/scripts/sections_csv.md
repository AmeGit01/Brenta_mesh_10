# sections_csv.py

Writes the summary table of the sections, one row per section, from the derived layers read back from disk.

## Requirements

* Geo interpreter (`~/anaconda3/bin/python3`): geopandas, shapely.

## Inputs

* `outputs.boundary`, `outputs.centerpoints`, `outputs.bankpoints` in `paths.layers`.
* `fields.boundary`, `fields.centerpoints`, `fields.bankpoints`, `bankpoint_values` (left, right), `sections.name_pattern`, `sections.digits`.
* `outputs.sections_csv`: CSV path relative to the working folder.
* `params.sections_csv.header`: the 14 column titles.
* Options: `--suffix S` inserted before `.gpkg` to read tagged backups (for example `_backup_20261118`); `--out PATH` replaces the CSV path.

## Outputs

The CSV, overwritten, and a line `rows N -> path`. Columns: section, reach, chainage `s` (2 decimals); for the left and the right bankpoint: z (3), `dist_cp` (2), kind, rule, prominence (3); length of the section line (2). Null values are empty fields.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/sections_csv.py [-c rcs_config.json] [--suffix S] [--out PATH]
```

## How it works

It selects the boundary features whose name matches `sections.name_pattern`, in layer order. For each one it reads the chainage from the centerpoint with the same name, and the two bankpoints named `<section>_<left>` and `<section>_<right>`; it measures the line length and writes the row.

## Checks / expected result

The row count equals the number of sections. On the Brenta test folder the output is identical to the CSV written by the original script.

## Limits

* It stops with an error if a section lacks its centerpoint or a bankpoint.
* If a section was moved by hand without moving its bankpoints, the length follows the line while z and distances stay those of the bankpoints.

Origin: Brenta project, `sections_csv.py`, 2026-11-18.
