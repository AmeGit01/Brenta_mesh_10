# chains.py

Classifies every segment of every breakline by the face classes on its left and right side. A segment that separates the bank class from one of its neighbour classes is a top-of-bank segment. `widen.py` moves only these lines. Optional step: it does nothing when `widening.enabled` is false.

Origin: Brenta project, `chains.py`, 2026-11.

## Requirements

* Interpreter: `~/anaconda3/bin/python3` (geopandas, shapely 2.x, numpy).

## Inputs

* `work/graph.pkl` (from `graph.py`, run on the original layers).
* Original breaklines layer (`inputs.breaklines`); empty geometries are dropped.
* Config: `face_classes` (`order`, `classes`, `default`, `fixed`, `editable`), `widening.enabled`, `widening.bank_class`, `widening.never_move`.
* The neighbour classes of the bank are the other `editable` classes plus the `default` class (Brenta: `inter` and `flood`).

## Outputs

* `work/chains.pkl`: dict with `feat` (fid -> vertex array), `S` (segments), `meta` ((fid, segment index) per segment), `L` / `R` (region name left / right of each segment), `Lc` / `Rc` (class names, as in the config), `istop` (top flag per segment).
* Printed: histogram of class pairs, number of lines made only of top segments and of mixed lines, number of lines touching a never-move face.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/chains.py [-c rcs_config.json]
```

## How it works

1. Reads the faces and the breaklines; each segment gets its left and right face 2 cm from its middle point.
2. The face name gives the class (`cfg.face_class`).
3. A segment is a top segment when its two classes are the bank class and one neighbour class.

## Checks / expected result

* Mixed lines (only some segments are top) are listed. `widen.py` does not move them.
* Brenta: 394 top lines, 67 lines touching `sponda_antro`; identical to the original script (the class names are now the config names).

## Limits

* Only the first part of a multipart geometry is used.
* A segment with no face (`outside`) or a face with no region point (`noname`) is never a top segment.
