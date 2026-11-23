# export_sec.py

Turns the stations chosen by `dp.py` into a flat JSON list, one record per section, in reach order. It is the input of `next_bed.py`, `obst.py` and `bank.py`.

Origin: Brenta project, `export_sec.py` and `export_B.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (the standard library is enough).

## Inputs

* `work/cands.pkl` (`place.py`) and `work/dp.pkl` (`dp.py`).
* Config: `reaches[*].code`. Option `--reach CODE [CODE ...]` exports only those reaches (e.g. only the reach that was placed again).

## Outputs

* `work/sec_in.json`: list of records, each with
  * `stream` and `tag`: reach code; `name`: section name; `s`: chainage along the source centerline;
  * `x`, `y`: centre point; `nx`, `ny`: unit normal towards the LEFT end (a section runs from left to right looking downstream, so the right side is -n);
  * `tL`, `tR`: centre to toe; `cL`, `cR`: centre to top of bank (m);
  * `anchor` (anchored sections only): the nodestring data (`k`, `section`, `nodestring`, `s`, `x`, `y`, `nx`, `ny`, `tL`, `tR`, `coords`). The record keeps the fields of the nearest candidate so that the next scripts run unchanged; `assemble.py` uses the nodestring itself.
* Printed: number of sections, per reach.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/export_sec.py [-c rcs_config.json] [--reach N V B]
```

## How it works

For each reach (config order), takes the candidate of each chosen index and copies its fields. Names are code + number (number = `first_number` + k x spacing).

## Checks / expected result

* One record per chosen station; the count printed per reach equals the length of the reach in `dp.pkl`.

## Limits

* The file is overwritten at every run; `next_bed.py` and `obst.py` update it in place, so run them after it.
