# <Case name>: rules and decisions

This document records the decisions of this case. The general method is the one of the river-cross-sections skill, and every check reads the configuration in `rcs_config.json`. What was done, with dates and results, is in [workflow.md](workflow.md).

## 1. Project

- **Model:** BASEMENT <version>, mesh built with BASEmesh in QGIS. CRS: EPSG:<code>.
- **Domain:** <short description: river, length, upstream and downstream boundary conditions, branches>.
- **Goal:** cross-sections every <spacing> ± <tol> m, from left bankpoint to right bankpoint, as nodestrings.

## 2. Layers

| File | Origin | Content |
|---|---|---|
| `<breaklines>.gpkg` | original | <count> breaklines; known defects: <...> |
| `<boundary>.gpkg` | original | <count> nodestrings: boundary conditions, bridges, gauges, ... |
| `<regions>.gpkg` | original | <count> region points; known defects: <...> |
| `<dtm>` | original | cell <size> m, nodata <value> |
| `*_<suffix>.gpkg` | derived | written by the skill, with tagged backups |

## 3. Decisions of this case

| Topic | Decision | Config key |
|---|---|---|
| Spacing | <dx_c> ± <tol> m | `sections.spacing`, `sections.tol` |
| Near-node distance | <R> m | `rules.near_node.radius` |
| Locked regions | <names / mat_id, or none> | `locked.mat_ids` |
| Fixed-geometry regions | <e.g. bed> | `face_classes.fixed` |
| Editable regions | <e.g. bank, intermediate> | `face_classes.editable` |
| Reaches | <codes, start and end of each> | `reaches` |
| Anchored sections | <section = nodestring, or none> | `anchors` |
| Bank widening | <no / criterion and zones> | `widening` |
| Bankpoint parameters | <defaults or changes> | `params.bank` |
| Minimum angle | <30°> | `rules.min_angle_deg` |

## 4. Known defects of the original data

They are left in the originals. List them here, and say how the derived layers handle each one.

## 5. Exceptions

The exceptions accepted by the user. They are the same as in `rcs_config.json` → `exceptions`.

**Near-node rule**

| Sections | Reason | Accepted on |
|---|---|---|

**Spacing**

| Sections | Reason | Accepted on |
|---|---|---|

**Angles**

| Where | Reason | Accepted on |
|---|---|---|

## 6. Open points

1. <...>
