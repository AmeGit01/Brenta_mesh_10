# assemble.py

Builds `secs_new.json`: one record per section, from the left bankpoint to the right bankpoint (left and right looking downstream), with the name, the centre point, the chainage, the distance to the next section and both bankpoints. An anchored section becomes the nodestring itself.

Origin: Brenta project, `assemble.py`, 2026-11-17 (updated 2026-11-18 for the anchored section).

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (numpy).

## Inputs

* `work/sec_in.json` (`export_sec.py`, then `next_bed.py`, `obst.py`) and `work/bank_out.json` (`bank.py`): same number of records, same order.
* Config: `reaches[*]` (`code`, `source`, `first_number`, `chainage`), `sections.spacing`, `sections.name_pattern`, `bankpoint_values` (`left`, `right`, `nodestring`).
* Optional `params.assemble.side_overrides`: list of `{section, side ("left" or "right"), sec_in, bank_out, rule}`. The first record of the two files (paths relative to the working folder) is a pseudo-section; its bankpoint (centre + `t` along the direction of that side) replaces the bankpoint of that side of the section. Used to extend a section into a second channel.

## Outputs

* `work/secs_new.json`: list of dicts:
  * `reach`, `old` (null), `nome`, `number`, `source`, `s`, `dist_next` (null for the last section of a reach), `cx`, `cy`;
  * `coords`: two vertices, left then right;
  * `sides`: two dicts (`tag` = `bankpoint_values.left`/`right`) with `x`, `y`, `z`, `dist_cp`, `tipo`, `regola`, `prom`, `moved`; `moved` is 0, or -1 for a side taken from an override;
  * only for reaches with chainage mode `cut_reference`: `s` is relative to the origin section; `s_asta` and `s_src` keep the chainage on the source line.
* Printed: counts per reach, first and last name, anchored sections, overrides.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <skill>/scripts/assemble.py [-c rcs_config.json]
```

## How it works

1. Left vertex = centre + n x `L.t`; right vertex = centre - n x `R.t`; attributes from `bank_out.json`.
2. A record with the key `anchor` takes the two vertices of the nodestring, the intersection with the centerline as centre, kind `bankpoint_values.nodestring`, rule = nodestring name, `z` null (read from the DTM later).
3. Chainage: mode `own` = chainage on the source line; mode `cut_reference` = chainage minus that of the origin section.
4. Side overrides are applied.

## Checks / expected result

* Brenta: with `sec_in.json` and `bank_out.json` rebuilt from the delivered 735 sections the output equals the delivered set within 1e-9 m (N 321, V 60, B 354); the only differences are `moved` on the 4 bankpoints edited by hand and `z` of the anchored section (null here).
* Stops if `sec_in.json` and `bank_out.json` differ in length. `OK` when the names are unique and match `sections.name_pattern`.

## Limits

* Bankpoints edited by hand in an earlier delivery are not read back: edit them again with `fix_manual.py`.
* Sections are produced in the order of `sec_in.json`, so the reach order of the config is kept.
