# The case configuration `rcs_config.json`

One file per case, in the working folder. Paths are relative to that folder.

- **New case:** start from `templates/rcs_config.template.json`. Values marked `<FIND>` come from the case material; values marked `<ASK>` come from the user ([kickoff.md](kickoff.md)).
- **Complete example:** `reference/brenta/rcs_config.json`.
- **Comments:** keys starting with `_` are comments and are ignored.
- **Missing values:** a script that needs a missing value stops and names the key.

## Contents

- [Project and files](#project-and-files)
- [Region classes and protected lines](#region-classes-and-protected-lines)
- [Sections, centerlines and reaches](#sections-centerlines-and-reaches)
- [Widening](#widening)
- [Rules](#rules)
- [Exceptions](#exceptions)
- [Script parameters](#script-parameters)

## Project and files

| Key | Content |
|---|---|
| `project.name`, `project.crs` | Case name; EPSG code of every layer. |
| `python.geo`, `python.ogr` | The interpreter with geopandas/shapely ≥ 2.1/scipy, and the one with GDAL/OGR. |
| `paths.layers`, `.work`, `.docs`, `.mesh` | Folders of the working folder ([working-folder.md](working-folder.md)). |
| `inputs.breaklines`, `.boundary`, `.regions` | Names (without `.gpkg`) of the original layers in `paths.layers`. Never written. |
| `inputs.dtm` | DTM file name in `paths.layers`. |
| `outputs.*` | Names of the derived layers (`breaklines`, `boundary`, `regions`, `centerline`, `centerpoints`, `bankpoints`) and the path of the sections table (`sections_csv`). |
| `fields.<layer>.<logical>` | Real field name of each logical field. Logical fields: `boundary` {id, name}; `breaklines` {id}; `regions` {name, mat_id, max_area, hole}; `centerline` {name, reach, length, s0}; `centerpoints` {name, reach, s, dist_next}; `bankpoints` {name, section, s, z, dist_cp, kind, rule, prom}. |
| `bankpoint_values` | Values written in the bankpoint fields: `left`/`right` name suffixes (`sx`/`dx`), and the `manual`, `nodestring` and `wall` kinds. |
| `dtm.nodata` | Nodata value of the DTM. |

## Region classes and protected lines

| Key | Content |
|---|---|
| `face_classes.classes.<class>` | `names`, `prefix` and `suffix` lists that map a region-point name to a class. The classes are `bed`, `bank`, `wall`, `inter` (intermediate strip). |
| `face_classes.order`, `.default` | Order in which the classes are tried; class of unmatched names (`flood`). |
| `face_classes.fixed` | Classes whose outline must not change (e.g. `["bed"]`: the toes never move). |
| `face_classes.editable` | Classes whose outline may move (e.g. `["bank", "inter"]`: the top of bank between them may be widened). |
| `face_classes.fixed_bank_names` | Bank region names that never move (e.g. anthropic banks). |
| `locked.mat_ids` | `mat_id` of the regions whose bounding breaklines are never touched (e.g. walls). |
| `locked.lines_file` | File in `work/` where `locked_lines.py` writes the fids of those lines. |
| `originals.region_fid_max` | Last fid of the original region points. Points up to this fid are never moved. |
| `originals.region_fids_replaced`, `.region_fids_deleted` | Original points replaced or deleted with the user's consent. The checks expect them to be missing. |
| `nodestrings.bc_upstream`, `.bc_downstream`, `.count` | Inflow and outflow boundary conditions; number of non-section nodestrings. |

## Sections, centerlines and reaches

| Key | Content |
|---|---|
| `sections.spacing`, `.tol` | Target spacing and tolerance (dx_c ± tol). |
| `sections.digits`, `.name_pattern` | Digits of the section number; regex that recognises a section name (e.g. `^[NVB]\d{5}$`). |
| `sections.first_fid`, `.first_id` | fid and id of the first section in the nodestring layer. The others follow in reach order. |
| `centerlines[]` | One entry per line: `name`; `from` and `to` (a nodestring name, `[x, y]`, or for `to` also `join:<other line>`); `waypoints` (names or `[x, y]`, to force a branch); `cost` (`centre` = stay in the middle of the bed, `length` = shortest); `join_point` (optional end point when joining). |
| `reaches[]` | One entry per reach, as many as the user wants; they can be added, removed, merged or split later ([method](method.md#changing-the-reaches)). See the details below. |
| `anchors[]` | `{section, nodestring}`: the section must coincide with that nodestring. The reach shifts to make it so. |

Each `reaches[]` entry has these keys:

| Key | Content |
|---|---|
| `code` | Letter of the section names. |
| `centerline` | Name of the output centerline feature. |
| `source` | Name in `centerlines`. |
| `first_number` | Number of the first section: 50 for `N00050`, 0 for `B00000`. |
| `chainage` | `{mode: own}`, or `{mode: cut_reference, reference_file, reference_line, origin_section}` for a reach cut from a longer line. |
| `start` | `{s}`, `{nodestring}` or `{section_of: code}`, plus optional `window` and `prefer_target`. |
| `end` | `{s}`, `{nodestring}`, `{count}`, `{line_end}` or `{section_of}`, plus optional `gap`, `rule` (`window` or `farthest`) and `truncate_full`. |
| `reference` | Optional `{dp, window, weight}`: re-places an anchored reach close to an earlier placement. |

## Widening

| Key | Content |
|---|---|
| `widening.enabled` | `true` or `false`. If `false`, skip step 4. |
| `widening.zones[]` | `{centerline, s_from, s_to (null = to the end), mode, min, check_min}`. `mode` is `corridor` (top-to-top width ≥ `min`, split symmetrically) or `bank` (each bank, toe to top, ≥ `min`). The first matching zone applies. |
| `widening.bank_class`, `.wall_classes` | Classes of the bank faces and of the wall faces. |
| `widening.min_gap_outer` | Minimum distance between a moved line and the next line outward. |
| `widening.simplify`, `.merge` | Simplification tolerance of the moved lines; minimum vertex spacing. |
| `widening.never_move` | Region names whose lines never move. |

## Rules

| Key | Content |
|---|---|
| `rules.near_node.radius` | Near-node distance R, **chosen by the user** (Brenta: 2 m). |
| `rules.near_node.slide_margin` | A slid node stops at R + margin. |
| `rules.near_node.max_displacement` | Maximum displacement of the line network per operation. |
| `rules.near_node.ignore_below` | Distances below this are a coincident vertex, not a violation. |
| `rules.min_angle_deg` | Minimum angle between lines after an edit (30). |
| `rules.regions.clearance` | Minimum distance of a region point from the lines (1 m). |
| `rules.regions.snap` | Tolerance that connects line ends (1 mm). |
| `rules.regions.sliver_width` | Width below which a face is a sliver. |
| `rules.regions.robust_rounding` | Roundings of the robustness check (`[0.001, 0.01]`). |
| `rules.noise` | Displacements below this are numerical noise. |

## Exceptions

Accepted by the user, each with a `reason` and a `date`. This is the only place where exceptions are defined ([exceptions.md](exceptions.md)).

| Key | Entry |
|---|---|
| `exceptions.near_node[]` | `{section, reason, date}` |
| `exceptions.locked_line[]` | `{section, reason, date}`. The near vertex belongs to a locked line. |
| `exceptions.spacing[]` | `{pair: [a, b], reason, date}` |
| `exceptions.vertices[]` | `{section, reason, date}`. The section may have more than two vertices; the first is the left end, the last the right end. |
| `exceptions.angle[]` | `{where: [x, y] or a list of ids (int = breakline fid, string = nodestring name), reason, date}` |

## Script parameters

`params.<script>` holds the constants of one script. Each sheet in [../docs/scripts/](../docs/scripts/) describes them. The ones to review with the user on a new case are:

| Key | Content |
|---|---|
| `params.bank` | Bankpoint definition: `min_prominence`, `lower_fraction`, `top_buffer` (distance from the intermediate strip), `mid_halfwidth`, `wide_bed`, `toe_window`, `min_window`. See [method.md](method.md#bankpoints). |
| `params.placement.weights` | Priorities of the section placement. |
| `params.placement.keep_clear` | Stretches where no section may fall (bridges). |
| `params.fix_near_nodes.laid_on_section`, `.source_strip` | Special breaklines handled by hand. |
| `params.fix_bridges.nodestring_regex`, `.exclude` | Which bridge closures to fix. |
| `params.assemble.side_overrides` | A section extended into a second channel. |
| `params.prep_write.centerline_sources` | The line each output centerline is cut from. |

The other parameters (skeleton, smoothing, ray lengths, tolerances) rarely change. Keep the defaults unless a check shows a problem.
