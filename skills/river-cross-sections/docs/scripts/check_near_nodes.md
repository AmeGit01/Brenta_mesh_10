# check_near_nodes.py

Independent check of the near-node rule on a breakline set. It counts the breakline vertices within `(ignore_below, radius)` of every section/breakline crossing. Crossings of the same section with other breaklines (narrow beds) and breaklines lying exactly on a section are ignored.

Origin: Brenta project, `check_near_nodes.py`, 2026-11-17.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (shapely 2.x, numpy, scipy).

## Inputs

* `work/secs_new.json` (sections, `nome`, `coords`).
* A JSON with key `F` (fid -> vertices): optional argument, default `work/near_nodes.json`. Lines with at least 2 vertices are used.
* Config `rules.near_node`: `radius`, `ignore_below`.

## Outputs

* Printed only: `crossings <n> violations <k> [(section, minimum distance m), ...]`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/check_near_nodes.py [-c rcs_config.json] [work/near_nodes.json]
```

## How it works

1. For each section, finds the breaklines that cross it (not those with both ends on it).
2. For each crossing, takes the vertices within `radius`, excluding the crossing itself and the other crossings of the same section.
3. Any vertex left (farther than `ignore_below`) is a violation.

## Checks / expected result

* Violations are allowed only for the sections listed in `exceptions.near_node` and `exceptions.locked_line` of the config.
* Brenta: identical output to the original script (1473 crossings, 14 violations on the test input).

## Limits

* It does not know the exceptions: compare the list with the config by hand.
