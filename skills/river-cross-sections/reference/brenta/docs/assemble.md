# assemble.py

Second pass (2026-11-17), updated 2026-11-18 for the anchored section. Builds `secs_new.json`, the new set of sections in three reaches: **N** (main reach up to S16130, renamed), **V** (first 60 of the Brenta vecchio), **B** (Brenta downstream of Borgo, from `dpB.py` and `bank.py`). Previous: the runs of `bank.py`; next: `fix5.py`.

## Requirements

* Interpreter: Anaconda `python3` (geopandas, shapely, numpy).
* **Relative** paths: it must be run with the current working folder = `WD`.
* Does not import `core.py`.

## Input

* `in/boundary_50m.gpkg`, `in/bankpoints_50m.gpkg`, `in/centerpoints_50m.gpkg` (copies of the current layers).
* `work/sec_in.json` (B sections after `export_B.py`, `next_bed.py`, `obst.py`; from 18 November the B00400 record contains the key `anchor`) and `work/bank_out.json` (`bank.py` on the B sections).
* `s16130/work/sec_in.json` and `s16130/work/bank_out.json`: run of `bank.py` to extend S16130; the first record (section) and its right side are used. The `sec_in.json` file of this folder is not produced by any pipeline script (prepared separately).
* `work/cands.pkl` and `work/dpB.pkl` are loaded but **not used**.

## Output

* `WD/secs_new.json`: list of dicts with `reach` (`N`/`V`/`B`), `old` (old name or `None`), `nome`, `s`, (`s_asta` for B), `cx`, `cy`, `coords` (2 vertices: left, right) and `sides` (two dicts `sx`/`dx` with `x`, `y`, `z`, `dist_cp`, `tipo`, `regola`, `prom`, `moved`).
* Prints counts per reach, some names (`secs[0]`, `secs[320]`, `secs[380]`, `secs[381]`, last) and the bankpoints moved by hand.

## Parameters and constants

* Threshold `s_m <= 16130.01` for the N reach; `iloc[:60]` for V.
* Name: `f'{reach}{(k+1)*50:05d}'` for N and V (index+1), `f'B{k*50:05d}'` for B (index from 0).
* `secs[320]` must be `S16130` (assert): it becomes N16050 and is extended to the right with `u = −(nx, ny)`, `t = XO['t']`.
* `moved`: distance between the vertex of the section and the bankpoint of the layer; `> 1e-6` means moved by hand (S00151/S01965); the extension of S16130 has `moved = −1.0` (marker, not "manual").
* Extension rule: `regola='canale_dx'`, `tipo` = `kind` from `bank.py`.
* Anchored section: `tipo='nodestring'`, `regola` = name of the nodestring (`idrometro_Borgo`), `z=None` (the elevation is read by `write2.py` from the DTM), `prom=None`, `moved=0`.

## Usage

```bash
cp scripts/assemble.py /path/to/WD/
```

```bash
cd /path/to/WD
```

```bash
python3 assemble.py
```

(layout of `WD`: see [dpB.md](dpB.md), Usage section.)

## How it works

1. Loads the layers of `in/`, sorts the `main` and `vecchio` centerpoints by `s_m`.
2. For N and V: for each centerpoint reads the two vertices of the section from the boundary layer (old name) and the two bankpoints (`<nome>_sx`, `<nome>_dx`), and computes `moved`.
3. Extends the last N section (S16130) to the right channel with the bankpoint computed by `bank.py` in `s16130/`.
4. For B: for each section of `sec_in.json` with tag `B` computes the two vertices `centre ± n·t` from `bank_out.json`; `s` is relative to the first B section (`s_asta` keeps the chainage of the main reach). If the record has the key `anchor`, the section becomes the nodestring itself: vertices of the nodestring (left first), centre at the intersection with the centerline, chainage of that point. The `bank.py` result for that section is ignored and the script prints `anchor section B00400 = idrometro_Borgo`.
5. Prints the summary and saves `secs_new.json`.

## Checks and limits

* Expected: 735 sections (N 321, V 60, B 354; on 18 November N and V came out identical to those of 17 November); check the printed names (N00050, N16050, V00050, V03000, B17650) and that only S00151/S01965 appear among the bankpoints moved by hand.
* The index `320` is fixed: if the number of N sections changes, the assert breaks.
* `sec_in.json` and `bank_out.json` in the `work/` folder must be those of the B reach (not of 2026-11-09).
* `bp[bp.nome==nm].iloc[0]` fails if a bankpoint of an old section is missing.
