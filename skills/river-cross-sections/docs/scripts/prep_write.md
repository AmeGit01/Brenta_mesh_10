# prep_write.py

Collects into one payload for `write3.py` everything the derived layers need after the near-node rule and the region-point choice: changed breaklines, the new section set, the centerlines of the reaches, centerpoints, bankpoints, and region-point changes. It writes no layer.

Origin: Brenta project, `prep_write.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* A near-nodes JSON: optional argument, default `work/near_nodes.json`.
* Layer `outputs.breaklines` (current breaklines), `work/secs_new.json` (keys `reach`, `nome`, `s`, `s_asta`, `cx`, `cy`, `coords`, `sides` with `tag`, `x`, `y`, `z`, `tipo`, `regola`, `prom`, `moved`), `work/regions2.json`.
* Config `reaches[*].code` and `.centerline` (output centerline names), `bankpoint_values.manual`.
* Config `params.prep_write`: `centerline_sources` (per reach code: `file` relative to the working folder, `line` name, `start` = `zero` or `first_section_s_asta`, `end` = `last_section_s` or `line_end`, `s0_from_start`), `manual_threshold`, `changed_threshold`.

## Outputs

* `work/write_payload.json` (or `-o`), format of `write3.py`, logical keys: `bl` (fid -> vertices of changed breaklines), `secs` (`name`, `coords`), `cl` (`name`, `reach`, `coords`, `s0`), `cp` (`name`, `reach`, `s`, `x`, `y`, `dist_next`), `bp` (`name`, `section`, `s`, `x`, `y`, `z`, `dist_cp`, `kind`, `rule`, `prom`), `reg_drop`, `reg_new` (`x`, `y`, `name`, `mat_id`, `max_area`, `hole`).
* Printed: counts and the lengths of the centerlines.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/prep_write.py [-c rcs_config.json] [work/near_nodes.json] [-o payload.json]
```

## How it works

1. Keeps the breaklines of the fix file whose vertices differ from the layer.
2. Cuts each reach centerline from its source line with `substring`, as configured.
3. Writes one centerpoint per section (`dist_next` = difference of `s` with the next section of the reach, null for the last).
4. Writes the section records and two bankpoints per section, named `<section>_<tag>`; `dist_cp` is recomputed from the coordinates.
5. A bankpoint moved by hand (`moved` > `manual_threshold`) gets kind and rule `bankpoint_values.manual`, and `z` and `prom` null (`write3.py` reads the DTM).
6. New region points get their fid from `write3.py`; section fid and id come from `sections.first_fid` and `first_id`.

## Checks / expected result

* Counts: sections = centerpoints = half the bankpoints; one centerline per reach.
* Brenta: with the test inputs (735 sections, 533 changed lines, 54 region points dropped, 6 new) the payload equals the content of the original `write2.json` (field names mapped).

## Limits

* The source centerlines must exist as lines with the configured names (for Brenta they are in the backup layer of the first version; the current derived layer holds only the cut ones).
* All fids of the fix file must exist in the breakline layer.
