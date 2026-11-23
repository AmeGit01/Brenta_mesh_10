# gaps.py

Print-only connectivity check after the widening. It lists the breakline ends that touched another breakline in the original data (within 1 mm) but touch nothing in the widened geometry. Boundary lines are not considered. Optional step.

Origin: Brenta project, `gaps.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (shapely 2.x).

## Inputs

* `work/chains.pkl`, `work/widen2.pkl`; config `widening.enabled`.

## Outputs

* Nothing on disk. Printed: the number of broken ends, then up to 60 tuples (fid, end 0 = first / -1 = last, new end xy, original neighbour fids, original end xy), and `OK` or `**CHECK**`.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/gaps.py [-c rcs_config.json]
```

## How it works

For every end of every line, compares the neighbours within 1 mm in the original and in the widened geometry. A broken end is one that had a neighbour and has none now.

## Checks / expected result

* `0` and `OK`: no gaps. Otherwise inspect and fix the listed ends. Brenta: 0.

## Limits

* Print only; does not repair. Neighbours of boundary lines are not checked.
