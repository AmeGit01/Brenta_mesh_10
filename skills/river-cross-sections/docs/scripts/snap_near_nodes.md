# snap_near_nodes.py

Applies the near-node rule by **moving the near breakline vertex exactly onto the crossing**, instead of inserting a new vertex. This is the preferred fix. `fix_near_nodes.py` stays for the cases this one cannot solve.

Where a section crosses a breakline, BASEmesh creates a node. A breakline vertex closer than `rules.near_node.radius` to that crossing produces tiny or stretched elements. Once the vertex is moved onto the crossing:
* the breakline passes through the crossing at one of its own vertices;
* the section still crosses it at the same point;
* no vertex is added.

## Requirements

* Interpreter: geo (geopandas, shapely 2.x, numpy, scipy).

## Inputs

* The derived breaklines, the boundary layer (sections and nodestrings) and the regions layer.
* The locked lines (`cfg.locked_lines()`, from `locked.mat_ids`).
* `rules.near_node.radius`, `rules.min_angle_deg`, `rules.regions.clearance`.
* `exceptions.near_node` and `exceptions.locked_line`: those sections are skipped, unless `--all` is given.

## Output

* The payload for `write3.py`, `work/snap_payload.json` (or the path given as argument): `{"bl": {fid: [[x, y], ...]}}`.
* Printed:
  1. vertices moved onto a crossing;
  2. near vertices deleted;
  3. moves rejected, with the reason;
  4. cases still open.

Nothing is written to the layers.

## Usage

```bash
cd <working folder>
<geo python> <skill>/scripts/snap_near_nodes.py
<ogr python> <skill>/scripts/write3.py work/snap_payload.json <tag>
```

Then run `verify3.py`, `check_regions.py` and `check_angles.py`. Run `snap_near_nodes.py` again: it must move nothing.

## How it works

For every crossing of a section with a breakline, the script uses the same definition as `verify3.py`:
* **near vertices:** the vertices of any breakline within the radius of the crossing;
* **excluded:** the vertices on the crossings of the same section;
* **coincident:** only a vertex within 10⁻⁶ m counts as the crossing itself. A vertex 0.1 mm away would give a 0.1 mm mesh edge, so it is moved too.

Then:

1. **Move.** The nearest near vertex on the **crossed** breakline is moved onto the crossing. Every line that has a vertex at the same point moves with it (junction nodes, T-junctions ending there), so no connection is lost.
2. **Delete.** Other near vertices on the crossed breakline are deleted if they are plain inner vertices: not shared, not ends.
3. **Report.** A near vertex on **another** line cannot be moved onto the crossing, because that would connect two lines. It is reported as still open.

A move is rejected when:
* the vertex lies on a nodestring or on another section;
* it belongs to a locked line;
* it is the end of a line that lies on another line (a T-junction would detach);
* a changed line is no longer simple;
* a new crossing between lines appears;
* a region point lies in the area swept by the moved segments, or ends up closer than min(previous, clearance) to a line;
* a new angle under `rules.min_angle_deg` appears.

Moves are applied one after the other, so each check sees the lines already changed.

## Expected result

After writing:
* `verify3.py` lists only near-node violations that are locked lines, rejected moves or vertices on other lines;
* those are proposed to the user as exceptions or fixed by hand.

## Limits

* Only section crossings are treated, not crossings of other nodestrings.
* The moved vertex travels at most the near-node radius. With a large radius, check the shape of the changed lines.

Origin: written for the skill on 2026-11-24. On the Brenta, with a radius of 2 m:
* 68 vertices were moved, including two that were 0.1 and 0.8 mm off, and one was deleted;
* the violations went from 153 to 10;
* the 10 left are 6 on locked wall lines and 4 rejected moves at two narrow places.
