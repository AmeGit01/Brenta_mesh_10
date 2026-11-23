# verify3.py

Independent check of all attributes and geometries of the six derived layers, read back from disk. Run it after any change, by hand or by script. It writes nothing. Bankpoint z values against the DTM are checked separately by `verify3_dtm.py`.

## Requirements

* Geo interpreter (`~/anaconda3/bin/python3`): geopandas, shapely 2.x, numpy, scipy.

## Inputs

Config keys:

* `outputs.*`: the six derived layers (breaklines, boundary, regions, centerline, centerpoints, bankpoints).
* `inputs.regions`, `inputs.breaklines`, `inputs.boundary`: the originals (attributes and original region fids; original planar graph).
* `fields.*`, `bankpoint_values`, `project.crs`.
* `sections.*`: `name_pattern`, `digits`, `spacing`, `tol`, `first_fid`, `first_id`.
* `reaches[*]`: `code`, `first_number`, `chainage`. For `chainage.mode = "cut_reference"`: `reference_file`, `reference_line`, `origin_section`.
* `nodestrings.count`.
* `exceptions.*`, read through `cfg.exc_near_node()`, `cfg.exc_wall()`, `cfg.exc_spacing()`. This is the single source of the exceptions.
* `locked.*`, read through `cfg.locked_lines()` (file `work/<locked.lines_file>`, written by `locked_lines.py`).
* `originals.region_fid_max`, `region_fids_replaced`, `region_fids_deleted`.
* `rules.near_node.radius`, `rules.regions.clearance`.
* `params.verify3`: `kinds` (allowed bankpoint kinds), `kind_max`, `kind_wall`, `prom_min`, optional `notes` (text appended to three check lines).

## Outputs

Print only: one numbered line per check, ending with `OK` or `**CHECK**` and listing the offending items.

## Usage

```bash
cd <working folder>
~/anaconda3/bin/python3 <toolkit>/scripts/verify3.py [-c rcs_config.json]
```

## How it works

Expected counts are derived, never fixed: non-section nodestrings = `nodestrings.count`; sections = number of centerpoints; bankpoints = 2 x sections; centerlines = number of reaches.

* **(A) Boundary:** counts; section names consecutive per reach (from `first_number`, step `sections.spacing`) in reach order; unique names and ids; section fid from `first_fid`, id from `first_id`; each section is one part with 2 vertices and z = 0.
* **(B) Centerline:** `length` equals the geometry length. For a `cut_reference` reach, the start chainage equals the chainage of the origin section on the reference line, and the line starts on that section.
* **(C) Centerpoints:** one per section, same name, reach code correct; the point is on the section and on the centerline; chainage is within the reach; `dist_next` is consistent and null for the last section of each reach.
* **(D) Bankpoints:** two per section, equal to the section vertices (left first); chainage and `dist_cp` consistent; kind in the allowed set; prominence only for the `max` kind and at least `prom_min`; manual, wall and nodestring points consistent with their rule; z not null; the section runs from left to right bank relative to the centerline direction.
* **(E) Spacing and near-node rule:** spacing along the centerline and straight distance outside `spacing +- tol` (numerical tolerance 1e-6 m), compared with the spacing exceptions. Crossings with a breakline vertex in (1 mm, radius) are split into: listed exceptions, vertices on locked lines (compared with the wall exceptions) and other vertices (must be none). Also the number of breaklines crossed per section.
* **(F) Crossings:** no section-section crossing. Section-nodestring contacts are `equal`, `section end on nodestring` or `cross`; `cross` must not occur. A section that coincides with a nodestring (anchor) is allowed.
* **(G) Region points:** one point per face of the planar graph; none outside a face; no null geometry; original points (fid <= `region_fid_max`, minus the deleted ones) present, unmoved and with the same attributes, except the replaced fids; no null attribute and no attribute combination absent from the originals; points closer than the clearance to a line are original only; diagnostic list of new points whose name differs from the original region.
* **(H) GeoPackage:** `integrity_check`, R-tree entries, CRS and geometry type of every derived layer.

* **(I) Angle rule:** the last check line. It calls the logic of `check_angles.py`: it is `OK` only if no NEW angle sharper than `rules.min_angle_deg` exists (angles covered by `exceptions.angle` and pre-existing ones are counted, not failed). Config: `rules.min_angle_deg`, `exceptions.angle`; the original layers `inputs.breaklines`, `inputs.boundary`.

## Checks / expected result

All checks `OK` on a consistent set of layers. A `**CHECK**` is a real finding (for example a region face without point, or a combination of attributes not in the originals) or a new case that needs an entry in `exceptions`.

## Limits

* Exceptions must be listed in the config; an unlisted anomaly is reported as `**CHECK**`.
* The locked-lines file must exist (`locked_lines.py`).
* The reading of regions uses fid as index; layers must keep the fids.

Origin: Brenta project, `verify3.py`, 2026-11-18.
