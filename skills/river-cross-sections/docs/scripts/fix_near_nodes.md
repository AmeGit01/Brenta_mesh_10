# fix_near_nodes.py

Applies the near-node rule to the breaklines: no breakline vertex at a distance in `(ignore_below, radius)` from a crossing between a section (or a nodestring) and a breakline. Crossings never move. They are inserted as vertices, and the nearby vertices are removed, junctions are moved onto the crossing or slid along their lines. Every operation is validated.

Origin: Brenta project, `fix_near_nodes.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* Layers `outputs.breaklines`, `outputs.boundary`, `outputs.regions` (the CURRENT derived layers).
* `work/secs_new.json` (`assemble.py`): sections with `nome` and `coords`.
* `cfg.locked_lines()` (`locked_lines.py`): wall breaklines, never modified.
* Config `rules.near_node`: `radius`, `slide_margin` (a node slid along its line stops at radius + slide_margin), `max_displacement`, `ignore_below`; `rules.min_angle_deg`; `rules.regions.clearance`; `fields.boundary.name`, `sections.name_pattern`.
* Config `params.fix_near_nodes`: `laid_on_section` (list of `{breakline, section}`), `source_strip` (list of `{upstream, downstream, section}`), `slide_step`, `max_slide`, `max_iterations`, `check_spacing`.

## Outputs

* `work/near_nodes.json`: `F` (fid -> vertices of ALL breaklines), `log` (operations `del`, `move`, `slide`), `unres` (unresolved crossings), `XS` (section crossings as `(section, fid, point)`).
* Printed: T-junction vertices added, special-case ends, crossing counts, removed / moved / slid / unresolved, the unresolved list, changed features.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/fix_near_nodes.py [-c rcs_config.json]
```

## How it works

1. Makes all T-junctions explicit (a line end lying on another line becomes a vertex of it).
2. Special cases from the config. `laid_on_section`: a breakline laid exactly on a section; its ends slide to the crossings of the section with their host toe lines. `source_strip`: the upstream breakline is laid on the section, the downstream one slides along its host lines to `radius + slide_margin` from the crossings.
3. Inserts every section and nodestring crossing as a vertex of the breaklines (locked lines are not touched).
4. For each section crossing, repeatedly takes the nearest vertex within the radius. A plain inner vertex is removed. A junction or end is moved onto the crossing if a path of removable vertices joins them. Vertices on nodestrings, crossings and locked lines are never moved.
5. Second pass: unresolved junctions slide along their lines until they are `radius + slide_margin` from every crossing.
6. `ok_change` validates each operation: network deviation <= `max_displacement`, no new crossing, simple lines, region points not closer than `min(previous, clearance)`, and no new angle sharper than `rules.min_angle_deg` (inside a changed line, or between a changed line and any other line, nodestrings and sections included). An angle that already existed and does not get sharper is accepted. A rejected operation is left unresolved with the reason `new acute angle`; the script prints how many operations were rejected and where. The special cases of step 2 are not validated: run `check_angles.py` afterwards.

## Checks / expected result

* Run `check_near_nodes.py` (violations only where the exceptions are accepted) and `check_geom.py` (no crossing lost or added, no new line-line crossing).
* Brenta: with the angle rule switched off (`min_angle_deg` 0), with the sections of the current layers and the breaklines before the near-node rule, output and `near_nodes.json` are identical to the original script (259 removed, 66 moved, 533 changed lines).

## Limits

* The special cases are Brenta-specific data (breakline fids); leave the lists empty for another case.
* Slow on large sets (about 90 s for 1300 breaklines and 735 sections).
* The special-case host lookup fails if the breakline is already laid on the section (run it on the layers before the near-node rule).
