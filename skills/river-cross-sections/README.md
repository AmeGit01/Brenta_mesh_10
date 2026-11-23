# river-cross-sections: maintainer notes

This file is for whoever maintains the skill. To use the skill, read [SKILL.md](SKILL.md).

## Layout

| Path | Content |
|---|---|
| `SKILL.md` | Entry point: rules, workflow, index of the references. |
| `references/` | Working folder, kickoff, method, checks, exceptions, BASEmesh, configuration, lessons. |
| `scripts/` | Case-independent scripts. `common.py` (configuration, paths; standard library only) and `geom.py` (geometry helpers, angle rule) are imported by the others. |
| `docs/scripts/` | One sheet per script. |
| `templates/` | `rcs_config.template.json`, `rules.md`, `workflow.md` for a new case. |
| `reference/brenta/` | Brenta configuration (`rcs_config.json`), locked lines (`mat11_lines.json`), the original Brenta implementations of the case-dependent steps (`scripts/`, `docs/`) and `make_test_wd.sh`. |

## Conventions for scripts

* No absolute path and no case value (names, fids, coordinates, thresholds) in the code. Everything comes from `rcs_config.json` through `common.Config`.
* Launch from the working folder. The first output line, printed by `common.load()`, names the case and the folder.
* A missing configuration value stops the script with a message that names the key.
* Header block: name and one line, then Purpose, Inputs, Outputs, Run. Comments in English. Checks print a numbered list with `OK` or `**CHECK**`.
* Line edits go through the acceptance rules of the method: displacement, no new crossings, locked lines, region-point clearance and no new angle under `rules.min_angle_deg`. Use `common.new_acute_angles` or `geom.acute_angles`.
* Every new script gets a sheet in `docs/scripts/` and a row in the SKILL.md workflow.

## Origin of the scripts (Brenta project, November 2026)

| Skill script | Brenta original | Notes |
|---|---|---|
| `common.py`, `geom.py` | `core.py` | Configuration, working folder, face classes, angle helpers. |
| `graph.py` | same | `--layers in/out`. |
| `skel.py`, `cl.py`, `cl2.py` | same | Lines from `centerlines` (from, to, waypoints, join); tables keyed by line name. |
| `chains.py`, `widen.py`, `apply_widen.py`, `gaps.py` | same | Zones from `widening`; angle rule added. |
| `check_widen.py` | `check2.py` | |
| `widen_payload.py` | new | Replaces the writing of the widened lines done by `write.py`. |
| `xn_points.py` | `prep_inputs_nvb.py` (part) | |
| `place.py`, `dp.py` | `place.py`, `dp.py`, `dpB.py`, `dpB2.py` | One dynamic programming for all reaches, anchors, keep-clear zones, angle penalty. |
| `export_sec.py` | `export_sec.py`, `export_B.py` | |
| `next_bed.py`, `obst.py`, `bank.py` | same | |
| `assemble.py` | same | Reaches from the configuration; side overrides. |
| `fix_near_nodes.py`, `check_near_nodes.py` | `fix5.py`, `check5.py` | Renamed (near-node rule); angle acceptance added. |
| `check_geom.py`, `regions2.py`, `prep_write.py` | same | `prep_write` writes the `write3.py` payload. |
| `write3.py` | `write3.py`, `write2.py` | Single writer; refuses open layers. |
| `sync_cp_bp.py`, `fix_manual.py`, `drop_regions.py`, `fix_bridges.py` | same | `fix_bridges` finds the pairs by itself; angle acceptance. |
| `verify3.py`, `verify3_dtm.py`, `check_bp.py`, `check_regions.py`, `sections_csv.py` | same | Expected counts derived from the data. |
| `init_outputs.py`, `locked_lines.py`, `check_angles.py`, `check_mesh.py` | new | `locked_lines` comes from part of `prep_inputs_nvb.py`. |

Brenta scripts left out:
* **Superseded:** `write.py`, `write2.py`, `dump.py`, `regions.py`, `finals.py`, `check.py`, `verify2.py`, `final.py`.
* **Diagnostics only:** `net.py` and the exploratory scripts.

## Tests

Every script was compared with its Brenta original on the same data, in disposable working folders:

```bash
bash reference/brenta/make_test_wd.sh <scratch>/wd reference/brenta/mat11_lines.json
```

The project layers are only read.

| Result | Scripts |
|---|---|
| Identical outputs (stdout, files or layers) | `graph`, `skel`, `cl`, `cl2`, `chains`, `widen`, `apply_widen`, `gaps`, `check_widen`, `verify3`, `verify3_dtm`, `check_regions`, `sections_csv`, `sync_cp_bp`, `fix_manual`, `drop_regions`, `locked_lines`, `write3` (same layers as `write2`/`write3`), `fix_bridges` |
| Identical on inputs rebuilt from the current layers | `next_bed`, `obst`, `bank`, `fix_near_nodes` (with the angle rule off), `check_near_nodes`, `check_geom`, `regions2`, `prep_write`, `assemble` |
| Placement | `place` and `dp` equal the originals with the original weights. B: 340/340 sections not edited by hand match within 1 mm. N: 319/320, the one miss edited by hand. V: 58/58. |
| Smoke test only | `check_bp`, `xn_points`, `export_sec`, `init_outputs`, `widen_payload`, `check_angles`, `check_mesh` |

**Effect of the new rules on the Brenta data.**
* **Angle rule in `fix_near_nodes`:** it rejects 3 operations, at N02150, B00950 and B01750.
* **Default placement weights:** they include the meeting-point and angle penalties, so they give a different placement with fewer near-node violations. Set `params.placement.weights.xn` and `.angle` to 0 to reproduce the November 2026 placement.

Every printed difference from the originals is either a renamed text (near-node rule, configuration names) or a new line (angle rule, face classes).
