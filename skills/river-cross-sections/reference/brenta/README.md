# Brenta reference folder

> **Names used here are the original ones.** The "5 m rule" is the **near-node rule** of the skill, with the distance chosen by the user. `fix5.py` and `check5.py` became `fix_near_nodes.py` and `check_near_nodes.py`. The generic versions of the scripts in this folder are in `../../scripts/` (see the origin table in `../../README.md`). Keep this folder as a record: it is not part of the workflow.


This folder keeps the original Brenta implementations of the case-dependent steps of the 50 m section workflow: centerline (`cl.py`, `cl2.py`), bank widening (`chains.py`, `widen.py`, `apply_widen.py`), section placement by dynamic programming (`place.py`, `dp.py`, `dpB.py`, `dpB2.py`), and assembly of the reaches (`export_sec.py`, `export_B.py`, `assemble.py`, `prep_inputs_nvb.py`).

It is a **reference**, not a ready-to-run toolkit. The scripts still use the old working-folder layout (`WD/in`, `WD/work`) and hard-coded Brenta values (chainages, line numbers, waypoints, coordinates). Each script has a sheet in `docs/<name>.md` with requirements, input, output, parameters, usage, how it works, and limits.

## Scripts

Run order from the original pipeline (`docs/scripts/README.md`, translated). Only the steps whose scripts are in this folder are listed.

| script | step | what it does | produces | sheet |
|---|---|---|---|---|
| `core.py` | shared | common functions: region classes, face graph loading, ray queries | – | [core.md](docs/core.md) |
| `skel.py` | 2 | Voronoi skeleton of the bed (first version) | `skel.pkl` | [skel.md](docs/skel.md) |
| `cl.py` | 4 | raw centerlines of the main reach and of the Brenta vecchio | `rawcl.pkl`, `altmain.pkl` | [cl.md](docs/cl.md) |
| `cl2.py` | 5 | smoothed centerlines at 1 m, toe and top distances | `cltab.pkl` | [cl2.md](docs/cl2.md) |
| `chains.py` | 6 | classifies breakline segments; finds the tops of bank | `chains.pkl` | [chains.md](docs/chains.md) |
| `widen.py` | 7 | computes the outward shift of each top of bank | `widen.pkl` | [widen.md](docs/widen.md) |
| `apply_widen.py` | 8 | applies the shifts to the breaklines and boundaries, validates the graph | `widen2.pkl`, `bgn.pkl`, `widen_faces.pkl` | [apply_widen.md](docs/apply_widen.md) |
| `gaps.py` | 9 | prints the line ends that lost their connection (print only) | – | [gaps.md](docs/gaps.md) |
| `place.py` | 10 | candidate section positions every 0.25 m and their checks | `cands.pkl`, `newfaces.pkl` | [place.md](docs/place.md) |
| `dp.py` | 11 | dynamic programming: sections at 50 ± 0.5 m | `dp.pkl` | [dp.md](docs/dp.md) |
| `export_sec.py` | 12 | section data for the bankpoint calculation | `sec_in.json` | [export_sec.md](docs/export_sec.md) |
| `prep_inputs_nvb.py` | 0 (second pass) | prepares `xn_points.json`, the dummy section of S16130 and the locked wall lines | `xn_points.json`, `s16130/work/sec_in.json`, `mat11_lines.json` | [prep_inputs_nvb.md](docs/prep_inputs_nvb.md) |
| `dpB.py` | 1 (second pass) | re-places the B reach on the main-reach candidates (dynamic programming) | `work/dpB.pkl` | [dpB.md](docs/dpB.md) |
| `export_B.py` | 2 (second pass) | section data of the B reach | `work/sec_in.json` | [export_B.md](docs/export_B.md) |
| `dpB2.py` | 1 (third pass) | moves the B reach with B00400 anchored to `idrometro_Borgo` | `work/dpB2.pkl` | [dpB2.md](docs/dpB2.md) |
| `assemble.py` | 7 (second pass), 6 (third pass) | assembles sections N, V, B | `secs_new.json` | [assemble.md](docs/assemble.md) |
| `check2.py` | group 19 of the checks | checks changed boundaries and breaklines, crossings and target widths (print only) | – | [check2.md](docs/check2.md) |

Scripts that are not in this folder (`graph.py`, `net.py`, `finals.py`, `regions.py`, `dump.py`, `write*.py`, `bank.py`, `next_bed.py`, `obst.py`, `fix5.py`, `verify*.py` and others) are described in the original `docs/scripts/` sheets; their links inside the sheets here point to files that are not copied.

## Configuration and helper files

These files in this folder are not scripts. They belong to the Brenta case:

* `rcs_config.json`: the Brenta configuration.
* `mat11_lines.json`: the locked breakline fids, the lines that bound the wall strips (regions with `mat_id` 11). `fix5.py` must leave them unchanged. It is produced by `prep_inputs_nvb.py`.
* `make_test_wd.sh`: builds disposable test working folders (`WD`) from the layers, so the scripts can be tried without touching the project data.

## Anomalies noted in the code (not corrected)

They were left as they are because fixing them would change the reproduction of files already delivered and verified.

* `place.py`: for the left side, the provisional extension of the segment used in the head-crossing checks is `tL+cR>30` instead of `tL+tR>30`. This affects only the choice of candidates, not the bankpoints, whose 30 m rule is in `bank.py`. The final sections passed the crossing check.
* `cl2.py`: calls "L" the side opposite to `widen.py`/`place.py` in the fields `SL`/`SR` of `cltab.pkl`. These fields are not used downstream.
* `check2.py`: reads the face names from the original `regioni_ponti`, so faces with only new points give NaN width.
* Unused code in `place.py`, `widen.py`, `cl.py`, `chains.py` and `dp.py`, indicated in their sheets.
