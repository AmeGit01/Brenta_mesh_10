# First interaction: work plan and questions

At the first interaction after the skill is activated, before running anything that writes, do three things.

1. **Survey the material** without asking.
2. **Present a short work plan.**
3. **Ask the questions** whose answers cannot be found in the material.

The goal is to get straight to the point. The user should answer once, with everything needed to fill `rcs_config.json`.

## 1. Survey (read-only)

- **Folders:** list the working folder and map it to the roles of [working-folder.md](working-folder.md).
- **Layers,** for each one:
  - geometry type, CRS, feature count and fields;
  - null, empty or invalid geometries;
  - for nodestrings, whether the names are unique and each feature is a single part.
- **Region points:**
  - the distinct names with their `mat_id` and `max_area`, and the hole flag;
  - which names look like bed, bank, intermediate strip, wall or floodplain.
- **Nodestrings:**
  - the names that look like boundary conditions (`BC_*`), bridges, gauging stations or culverts;
  - the existing sections, if any.
- **Planar graph** of the original layers (`graph.py`): number of faces, faces without a region point and faces with two points. Report these as known defects of the original data. They are not corrected in the originals.
- **DTM:** cell size, nodata value and extent compared with the layers.
- **`mesh/`:** the existing meshes and their dates.
- **Documents in `docs/`:** documents and model files that already state rules or decisions.

## 2. Work plan (show it to the user)

A numbered list of the steps of [SKILL.md](../SKILL.md#workflow), with the ones that do not apply marked as skipped (for example: no bank widening). For each step, say what will be written and where the user will be asked to confirm.

## 3. Questions

Ask with one grouped set of questions, offering the value found in the survey as the proposed answer when there is one. Always cover:

| Topic | Question | Config key |
|---|---|---|
| Spacing | Target spacing between consecutive sections and tolerance (dx_c ± tol, e.g. 50 ± 0.5 m) | `sections.spacing`, `sections.tol` |
| Near-node rule | Minimum distance between a breakline vertex and the node where a section crosses that breakline (e.g. 5 m) | `rules.near_node.radius` |
| Locked regions | Are there regions whose bounding breaklines must never be touched (e.g. walls, buildings, piers)? Which names or `mat_id`? | `locked.mat_ids` |
| Fixed-geometry regions | Which regions must keep their outline (e.g. the bed: toes never move)? | `face_classes.fixed` |
| Editable regions | Which regions may change outline (e.g. intermediate strips, banks to widen)? | `face_classes.editable` |
| Region classes | Confirm the mapping of region names to classes: bed, bank, intermediate, wall, floodplain | `face_classes` |
| Reaches | Upstream and downstream boundary conditions; branches (side channels, old courses) that need their own sections; junctions where a reach ends | `nodestrings`, `centerlines`, `reaches` |
| Anchors | Sections that must coincide with an existing nodestring (gauging station, measuring section) | `anchors` |
| Naming | Section names: reach code plus nominal chainage (`N00050`), number of digits, first number | `sections`, `reaches[*].first_number` |
| Bankpoints | The bankpoint definition is in [method.md](method.md#bankpoints). Confirm or change the parameters: minimum prominence, distance from the top-of-bank line (edge of the intermediate strip), maximum half-width | `params.bank` |
| Widening | Should the banks be widened where the bed + bank corridor is too narrow? With which criterion (corridor width or width of each bank) and where? | `widening` |
| Angles | Minimum angle between lines after an edit (default 30°) | `rules.min_angle_deg` |
| Outputs | Suffix of the derived layers (e.g. `_50m`), field names of the new layers if a convention exists | `outputs`, `fields` |
| Environment | Interpreters with geopandas/shapely and with GDAL/OGR (propose the ones found) | `python` |

Add any other question the survey raised: unclear region names, duplicate nodestring names, faces without a point, a DTM that does not cover the layers.

## After the answers

- Write `rcs_config.json`. Start from `templates/rcs_config.template.json`, using the answers and the survey.
- Write `docs/rules.md` from `templates/rules.md`, so the decisions of this case are on record.
- Start `docs/workflow.md` from `templates/workflow.md`.
- Show the configuration to the user and start step 0 only after their confirmation.
