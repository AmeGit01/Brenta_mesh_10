# locked_lines.py

Lists the breaklines that bound the "wall" faces, the faces of regions whose material is locked. These breaklines must never be modified by the other scripts, which read the list with `cfg.locked_lines()`.

Origin: Brenta project, `prep_inputs_nvb.py` (part 3, `mat11_lines.json`), 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* The breaklines, boundary and regions layers: the ORIGINAL ones by default (cfg `inputs`), the derived ones with `--derived`.
* Config: `locked.mat_ids` (materials that are locked), `locked.lines_file`, `fields.regions.mat_id`, `fields.boundary.name`, `sections.name_pattern`, `params.locked_lines`: `buffer` (m) and `min_shared` (m).

## Outputs

* `work/<locked.lines_file>`: JSON, sorted list of breakline fids.
* Printed: number of wall faces and of locked breaklines, and the list.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/locked_lines.py [-c rcs_config.json] [--derived]
```

## How it works

1. Builds the planar graph of the breaklines and the non-section boundary lines (sections are not obstacles).
2. The wall faces are the faces that contain a region point with a material in `locked.mat_ids`.
3. A breakline is locked if it shares more than `min_shared` metres with the boundary of the wall faces (buffered by `buffer`).

## Checks / expected result

* Brenta: on the original layers the file is byte-identical to the reference `reference/brenta/mat11_lines.json` (19 wall faces, 32 breaklines). With `--derived` on the current derived layers the result is the same.

## Limits

* Run it once, before the scripts that need the list, and again if the wall regions or lines change.
* A region point that falls outside every face stops the script with an error.
