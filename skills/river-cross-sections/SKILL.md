---
name: river-cross-sections
description: Builds cross-sections at a constant spacing (e.g. 50 ± 0.5 m) as nodestrings of a BASEmesh/BASEMENT 2D river mesh, from breaklines, nodestrings, region points and a DTM. Covers centerlines, optional bank widening, centerpoints, bankpoints on the DTM, section drawing (left to right), the near-node rule on breaklines, the 30-degree angle rule, one region point per face, writing GeoPackages with verified backups, full checks, realignment after manual edits in QGIS and the check of the generated mesh. Use when the user asks to create, redo or check river cross-sections, bankpoints, centerpoints or centerlines for a BASEMENT/BASEmesh model, or to realign the layers after editing sections by hand.
---

# River cross-sections for BASEmesh/BASEMENT

The skill builds cross-sections as nodestrings of a 2D river mesh, with their centerlines, centerpoints and bankpoints. Every edit of the case layers is checked and logged.

The scripts are in `scripts/` of this skill and are case-independent. Every case-specific value is in the case configuration `rcs_config.json`. A complete example is in `reference/brenta/` (the Brenta river, November 2026).

## Before anything else

1. **Read** [references/working-folder.md](references/working-folder.md): what each folder is for, and what may and may not be done in it.
2. **First interaction:** survey the material, present a work plan and ask the kickoff questions, following [references/kickoff.md](references/kickoff.md). Do not write any layer before the user has confirmed the configuration.

## Non-negotiable rules

- **Originals.** The original layers, `mesh/`, the BASEMENT model files and the QGIS project are **never written**. Results go into derived layers with a suffix, created once as copies of the originals. The SHA-256 of the originals is recorded at the start and checked at the end.
- **Before every write:** explain the change and wait for the user's confirmation. Check that the layer is closed in QGIS (no `-wal` file). Write only with `write3.py`, which makes a tagged backup checked by SHA-256.
- **After every write:** check the files read back from disk with code that did not produce them ([references/checks.md](references/checks.md)). Report the result as a numbered list.
- **Missing information:** look for it in the available material (configuration, `docs/`, layers, model files, QGIS project, all read-only). If it is not there, ask the user. Never guess: scripts stop and name the missing configuration key.
- **Consent:** deletions and exceptions need explicit consent from the user. Violations, even of a few millimetres, are reported, never rounded away ([references/exceptions.md](references/exceptions.md)).
- **Line edits:**
  - the nodestrings never move to fix a breakline;
  - locked lines (walls) are never touched;
  - fixed-geometry regions (the bed) keep their outline;
  - no edit may create an angle sharper than `rules.min_angle_deg` (30°), inside a line or where two lines meet.
- **DTM:** always the value of the cell under the point, never interpolated.
- **Log:** every action that changes the work goes into `docs/workflow.md`, with date, backup tag and check results.
- **Language:** everything the skill writes (documents, comments, sheets) is in English, unless the user asks otherwise.
- **Git:** never commit unless the user asks.

## Workflow

Run every script from the working folder: `cd <WD>; <python> <skill>/scripts/<name>.py [-c rcs_config.json] [args]`. The sheet of each script, in [docs/scripts/](docs/scripts/), gives the interpreter (geo or ogr), the inputs, the outputs and the expected result. ⛔ marks a stop: show the result and wait for the user.

| # | Step | Scripts | Method |
|---|---|---|---|
| 0 | Survey, plan and kickoff questions; write `rcs_config.json`, `docs/rules.md` and `docs/workflow.md` from `templates/` ⛔ | (read-only) `graph.py --layers in` | [kickoff](references/kickoff.md) |
| 1 | Derived layers; SHA-256 of the originals; locked lines | `init_outputs.py`, `locked_lines.py` | [working folder](references/working-folder.md) |
| 2 | Planar graph and face classes of the original layers | `graph.py --layers in` | [method §1](references/method.md#1-terms) |
| 3 | Centerlines (skeleton, path, smoothing, 1 m table) ⛔ | `skel.py`, `cl.py`, `cl2.py` | [method §2](references/method.md#2-centerlines) |
| 4 | Bank widening, only if requested ⛔ (then written into the derived layers and checked) | `chains.py`, `widen.py`, `apply_widen.py`, `gaps.py`, `widen_payload.py`, `write3.py`, `check_widen.py`, `check_angles.py` | [method §3](references/method.md#3-bank-widening-optional) |
| 5 | Section positions and centerpoints (dynamic programming, anchors); first rebuild the graph of the derived layers | `graph.py --layers out`, `xn_points.py`, `place.py`, `dp.py`, `export_sec.py` | [method §4](references/method.md#4-section-positions-and-centerpoints) |
| 6 | Bankpoints on the DTM | `next_bed.py`, `obst.py`, `bank.py` | [method: bankpoints](references/method.md#bankpoints) |
| 7 | Sections drawn left to right, from bankpoint to bankpoint | `assemble.py` | [method §6](references/method.md#6-drawing-the-sections) |
| 8 | Near-node rule on the breaklines ⛔ violations | `fix_near_nodes.py`, `check_near_nodes.py`, `check_geom.py`, `check_angles.py` | [method §7–8](references/method.md#7-near-node-rule) |
| 9 | One region point per face | `regions2.py` | [method §9](references/method.md#9-region-points) |
| 10 | Payload and writing ⛔ layers closed? | `prep_write.py`, `write3.py` | [working folder](references/working-folder.md#how-a-layer-is-written) |
| 11 | Bridge closures exactly on their nodestrings | `fix_bridges.py`, `write3.py` | [method §8](references/method.md#8-editing-lines-topology-and-angles) |
| 12 | All checks ⛔ results and exceptions | `verify3.py`, `verify3_dtm.py`, `check_bp.py`, `check_regions.py`, `check_angles.py` | [checks](references/checks.md) |
| 13 | Delivery: sections table; `STRINGDEF` block for the model file, given to the user; instructions to regenerate the mesh | `sections_csv.py` | [BASEmesh](references/basemesh.md) |
| 14 | Mesh check after the user regenerates it ⛔ | `check_mesh.py` | [checks](references/checks.md) |

**After manual edits by the user** (repeat as often as needed): ask which sections changed and make sure the layers are closed. Then:
1. Run `fix_manual.py` if repairs are needed, then `write3.py`.
2. Run `sync_cp_bp.py`, then `write3.py`.
3. Run `sync_cp_bp.py` again: it must report 0 changes.
4. Run the step-12 checks.
5. Propose an exception for every remaining violation.
6. Ask the user to regenerate the mesh, and run step 14.

See [method §10](references/method.md#10-manual-edits-by-the-user).

## Reference files

| File | Content |
|---|---|
| [references/working-folder.md](references/working-folder.md) | Folders, roles, allowed and forbidden actions; how a layer is written; how to find missing information |
| [references/kickoff.md](references/kickoff.md) | Survey, work plan and the questions of the first interaction |
| [references/method.md](references/method.md) | Centerlines, widening, positions, centerpoints, **bankpoint definition**, drawing, near-node rule, line editing and angles, region points, attributes |
| [references/checks.md](references/checks.md) | Which check when, what must hold, what to do when a check fails |
| [references/exceptions.md](references/exceptions.md) | How exceptions are proposed, approved, recorded and removed |
| [references/basemesh.md](references/basemesh.md) | How BASEmesh and BASEMENT read nodestrings and region points |
| [references/config.md](references/config.md) | Every key of `rcs_config.json` |
| [references/lessons.md](references/lessons.md) | Problems met on the Brenta and how to recognise them |
| [docs/scripts/](docs/scripts/) | One sheet per script |
| [reference/brenta/](reference/brenta/) | The Brenta configuration, the original implementations and a builder of disposable test folders |
| [templates/](templates/) | Configuration, case rules and work log to start a new case |
