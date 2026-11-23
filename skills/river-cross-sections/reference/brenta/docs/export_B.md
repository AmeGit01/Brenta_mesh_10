# export_B.py

Second pass (2026-11-17), updated 2026-11-18. Writes `sec_in.json` for the B reach only, with the same fields as `export_sec.py`, starting from the indices chosen by `dpB.py` or, from 18 November, by `dpB2.py`. Previous: `dpB.py` or `dpB2.py`; next: `next_bed.py`, then `obst.py` and `bank.py`.

## Requirements

* Interpreter: Anaconda `python3`.
* Imported module: `core.py` from `WD/work` (`SP`, `pickle`, `np`); `json`.
* The script must be copied into `WD/work`.

## Input

* `WD/work/cands.pkl` (`place.py`): key `main` with `ss`, `P`, `n`, `tL`, `tR`, `cL`, `cR`.
* Argument 2 (optional): name of the file in `WD/work` to read, `dpB.pkl` if absent. From 18 November `dpB2.pkl` is used.
* `WD/work/dpB.pkl` (`dpB.py`) or `WD/work/dpB2.pkl` (`dpB2.py`): key `B` and, only for `dpB2.pkl`, key `anchor`.

## Output

* `WD/work/sec_in.json` (**overwritten**): list of dicts with `stream='main'`, `tag='B'`, `s`, `x`, `y` (centerpoint), `nx`, `ny` (unit normal, positive towards the left), `tL`, `tR` (toe distances), `cL`, `cR` (top distances), in metres.
* With `dpB2.pkl` the record of the anchored section (B00400) also contains the key `anchor`, with the geometry of `idrometro_Borgo`. The other fields remain those of the nearest candidate, which is only a placeholder: this way `next_bed.py`, `obst.py` and `bank.py` run without changes, and `assemble.py` later replaces the section with the nodestring.
* Prints the number of sections (`B sections N`).

## Parameters and constants

No constants: the tag `'B'` and the stream `'main'` are fixed in the code. `tag='B'` is later used by `assemble.py` to select the B sections.

## Usage

```bash
cp scripts/export_B.py /path/to/WD/work/
```

```bash
python3 /path/to/WD/work/export_B.py /path/to/WD dpB2.pkl
```

Without the second argument it reads `dpB.pkl`, as on 17 November.

(layout of `WD`: see [dpB.md](dpB.md), Usage section.)

## How it works

For each index `j` of `B` it builds the record with the values of the candidates. If the key `anchor` is present, it adds it to the record at position `anchor['k']`. Finally it writes the list to `sec_in.json`.

## Checks and limits

* The file contains **only** the B sections: it overwrites the previous `sec_in.json` (the one of 2026-11-09 remains in the original work).
* The number of sections must match `len(B)` (354 both on 17 and on 18 November, B00000–B17650).
* It does not check that the values are finite (`tL`, `cL`, … `nan` would be written as `NaN`).
