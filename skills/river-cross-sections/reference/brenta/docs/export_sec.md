# export_sec.py

Converts the positions of the sections chosen by the dynamic programme (`dp.py`) into a flat JSON list, one record per section at 50 m. It is step 12 of the sequence (see `README.md`): the previous script is `dp.py`, the next `next_bed.py`. The file produced, `sec_in.json`, is the input of the bankpoint calculation (`bank.py`) and of all the following scripts.

## Requirements

* Interpreter: Anaconda `python3`.
* Packages: numpy, shapely, geopandas (imported through `core.py`), `json`.
* Imported module: `core.py` (from `WD/work`, added to `sys.path` from `sys.argv[1]`). From `core` it uses only `pickle`, `SP`.

## Input

* `WD/work/cands.pkl`, produced by `place.py`: dict `{'main': {...}, 'vecchio': {...}}`; for each stream it uses the keys `ss` (chainage in m), `P` (points of the centerline, N×2), `n` (unit normals, N×2), `tL`, `tR` (distance centerpoint → toe of the bed on the left/right), `cL`, `cR` (distance centerpoint → top of bank on the left/right).
* `WD/work/dp.pkl`, produced by `dp.py`: dict `{'main': array, 'vecchio': array}` with the indices `j` of the chosen candidates, in order along the course.

## Output

* `WD/work/sec_in.json`: list of dicts, in the order first all the `main` sections, then all the `vecchio`. Keys: `stream` (`main`/`vecchio`), `s` (m), `x`, `y` (centerpoint), `nx`, `ny` (unit normal, towards the left), `tL`, `tR`, `cL`, `cR` (m).
* Prints the number of sections. Used by `next_bed.py` (which updates it), `bank.py`, `finals.py`, `regions.py`, `dump.py`, `check_bp.py`, `esplorativi/bq.py`.

## Parameters and constants

No thresholds. Implicit constants: the stream names (`'main'`, `'vecchio'`) and the names of the working files (`cands.pkl`, `dp.pkl`, `sec_in.json`), editable in the first lines of the script.

## Usage

Prepare `WD` as in `README.md` (`WD/in`, `WD/work` with the scripts and the `.pkl` files of the previous steps), then:

```bash
python3 export_sec.py /path/to/WD
```

## How it works

1. Loads `cands.pkl` and `dp.pkl`.
2. For each stream (`main`, then `vecchio`) and each chosen index `j`, builds a record with the values of `cands.pkl` at position `j`, converted to `float`.
3. Writes the list to `sec_in.json` and prints its length.

## Checks and limits

* The printed number must match the expected number of sections (main reach 33 981.6 m and Brenta vecchio 3 058.7 m, about one every 50 m).
* It does no checks: if `dp.pkl` and `cands.pkl` are not consistent it produces wrong records without warnings. It overwrites `sec_in.json` without a backup (the file is then modified by `next_bed.py`, so re-run `next_bed.py` after each re-run of this script).
