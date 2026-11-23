# Method

Rules for building the sections and why each one exists. The values in brackets are the Brenta values; each case sets its own in `rcs_config.json`.

## Contents

1. [Terms](#1-terms)
2. [Centerlines](#2-centerlines)
3. [Bank widening (optional)](#3-bank-widening-optional)
4. [Section positions and centerpoints](#4-section-positions-and-centerpoints)
5. [Bankpoints](#bankpoints)
6. [Drawing the sections](#6-drawing-the-sections)
7. [Near-node rule](#7-near-node-rule)
8. [Editing lines: topology and angles](#8-editing-lines-topology-and-angles)
9. [Region points](#9-region-points)
10. [Manual edits by the user](#10-manual-edits-by-the-user)
11. [Attributes of the derived layers](#11-attributes-of-the-derived-layers)

## 1. Terms

| Term | Meaning |
|---|---|
| Left / right (`sx` / `dx`) | Orographic: looking downstream. |
| Bed | The channel bottom, bounded by the two **toe** lines. |
| Bank | The strip between the toe and the **top-of-bank** line. |
| Intermediate strip | The strip just outside the top of bank (Brenta: `intermedio_*`). Its edge towards the bank is the top-of-bank line. |
| Section | A nodestring crossing the bed from the left bankpoint to the right bankpoint. |
| Centerline | The line along the middle of the bed of a reach. Chainage `s` is measured along it from 0 at the start of the reach. |
| Centerpoint | The intersection of a section with its centerline. |
| Bankpoint | The end of a section on one bank. |
| Planar graph | The faces into which breaklines and nodestrings divide the plane. BASEmesh gives each face the attributes of the region point inside it. |

## 2. Centerlines

The sections are placed along a centerline that follows the middle of the bed.

- **Path.** Build a Voronoi skeleton of the bed polygon (the union of the faces of class `bed`). Holes larger than a threshold are kept (1000 m²), because filling them would merge branches. Among the skeleton paths between the start and end nodestrings of the line, take the one that stays closest to the centre of the bed.
- **Branches.** Where the bed splits, the path follows the branch the user chooses. By default this is the wider one, measured by the median bed width. Waypoints in the configuration force the path through a branch.
- **Side channels** (old courses, diversions) get their own centerline, from the nodestring where they leave the main stem to the point where they rejoin it.
- **Smoothing.** The skeleton is jagged, so the path is smoothed with a Gaussian filter whose width follows the bed width (6 m where the bed is narrow, up to 60 m where it is wide). It is then resampled every 1 m, so that the array index is the chainage in metres.
- **Measurements.** At every metre the table also stores the perpendicular distances to the toe lines and to the top-of-bank lines on both sides.

A **reach** is a stretch of a centerline that gets its own numbered sections. It is defined by its start and end: a nodestring, a chainage or the end of another reach. Reaches are separate where a junction cannot be represented by a 1D model. In the 2D mesh the reaches stay connected, and the stretch between them has no sections.

The centerline layer contains one line per reach.

## 3. Bank widening (optional)

The bankpoint must stay far enough from the top of bank (5 m), and the section must stay compact. Both are possible only if the bed + bank corridor is wide enough. Where it is too narrow, the top-of-bank lines are moved outward.

- **Measuring.** The width is measured every metre, perpendicular to the centerline.
- **Two criteria,** chosen per zone:
  - **corridor:** the distance between the two top-of-bank lines must be at least a minimum (40.10 m). Each side moves out by half the difference.
  - **bank:** each bank, toe to top, must be at least a minimum wide (16.05 m). Each side is moved separately. This is for wide rivers, where a fixed corridor width makes no sense.
- **What moves.** Only lines between an **editable** bank face and an **editable** intermediate face. Toes (outline of the **fixed** bed) never move, and neither do the lines of **locked** regions (walls) or anthropic banks.
- **Clearance.** A moved line stays at least 5 m from the next line outward.
- **Topology.** All the rules of [§8](#8-editing-lines-topology-and-angles) apply. After widening, the planar graph must have the same faces as before: no new faces and no merged regions.

## 4. Section positions and centerpoints

- **Spacing.** Sections are `spacing ± tol` apart along the centerline (50 ± 0.5 m). The straight distance between consecutive centerpoints is also checked; it can be shorter in tight bends.
- **Direction.** Each section is perpendicular to the **chord** of the centerline between s − 1 m and s + 1 m. The chord is less sensitive than the local tangent to small irregularities of the line.
- **Choosing the positions.** The positions are chosen for the whole reach at once, not one section at a time. Candidates are generated every 0.25 m along the centerline, and dynamic programming picks the best sequence. The priorities, in order:
  1. no crossing of nodestrings or transverse lines, and no crossing with the sections of other reaches;
  2. fewest near-node violations ([§7](#7-near-node-rule)) and no crossing at an angle sharper than the minimum ([§8](#8-editing-lines-topology-and-angles));
  3. spacing as close as possible to the target.

  Perpendicularity is a penalty, not a hard constraint, otherwise some stretches would have no admissible sequence.
- **Anchors.** A section can be required to coincide exactly with an existing nodestring, for example a gauging station: same two vertices, left one first. The whole reach is shifted so that the anchored section falls there, and the other sections keep their spacing. The bankpoints of an anchored section are the ends of the nodestring.
- **Names.** A section is named with the reach code followed by its position in the reach times the spacing, with a fixed number of digits (`N00050`, `B00000`). The name is nominal: over long distances it drifts from the true chainage, which is always in the `s` field of the centerpoint.
- **Centerpoints.** The centerpoint is the intersection of the section with its centerline. Its attributes are:
  - `s`, the true chainage in the reach;
  - `dist_next`, the chainage difference to the next section of the same reach, empty for the last one.

## Bankpoints

The bankpoint is where the section ends on each bank. The aim is the **first significant crest met when climbing from the bed outward,** not the highest point of the bank. The section then stays close to the channel and does not climb onto the floodplain.

**Orthogonality.** The search runs along the section line, which is perpendicular to the centerline chord ([§4](#4-section-positions-and-centerpoints)). Both bankpoints lie on that line.

**The profile.** Starting from the toe and moving outward, every DTM cell crossed by the section is visited and its value is read. The value is never interpolated, so it matches what QGIS *Identify* shows. Sampling at a fixed step is not used, because it could miss a cell crossed only at a corner.

**The crest.** A local maximum counts only if its **prominence** is at least a minimum (5 cm): it must stand that much above the lowest ground separating it from higher ground. This filters DTM noise. A flat top counts as one maximum.

Maxima in the **lower half of the bank** are discarded: those below z_toe + 0.5 · (z_max − z_toe) are humps at the toe, not the top.

**The choice.** The **first** valid maximum from the channel is taken (`kind` = local maximum). If there is none, because the ground keeps rising, the **highest cell** of the search window is taken (`kind` = highest cell).

**The search window** ends at the first of these limits:

- **distance from the intermediate strip:** at least `top_buffer` (5 m) **before the top-of-bank line,** which is the edge of the intermediate strip (widened, if widening was done). The bankpoint never lands on the edge of the bank;
- **compactness:** at most `mid_halfwidth` (15 m) from the mid-width of the corridor, so the two bankpoints are at most 30 m apart;
- **wide beds:** where the bed is wider than `wide_bed` (30 m), the toe is already beyond the previous limit. The search then reaches `toe_window` (15 m) beyond each toe, still respecting the distance from the intermediate strip. The same applies where the mid-width limit would leave less than `min_window` (2 m) beyond the toe, as at confluences;
- **obstacles:** 0.5 m before a nodestring, an inner line (a building), or the toe of another bed, at any distance. With two parallel channels the section does not jump over the island. If the obstacle coincides with the toe, the section ends 0.5 m before it, inside the bed, and crosses only one toe (`kind` = wall).

**The position.** The bankpoint is placed at the middle of the stretch of section that crosses the chosen cell. If that cell contains the crossing with the top-of-bank line, the point goes exactly on the crossing.

**Revisions.**
- **Anchored section:** the bankpoints are the nodestring ends. Their `kind` is `nodestring` and their `rule` is the nodestring name.
- **Section edited by hand:** the bankpoint follows the new end. Its `kind` and `rule` become `manual`, and `z` is the value of the cell under the point.
- **Centerpoint after an edit:** it is recomputed as the new intersection with the centerline, and `s`, `dist_next` and `dist_cp` are updated with it.

**The attributes** are listed in [§11](#11-attributes-of-the-derived-layers).

## 6. Drawing the sections

- A section is a **straight line with exactly two vertices,** from the left bankpoint to the right bankpoint. The vertices are copied exactly from the bankpoint coordinates.
- **Orientation: left to right, looking downstream.** In BASEMENT this is `upstream_direction: "right"`.
- It is written as a nodestring: MultiLineStringZM with a single part, z = m = 0, and a unique name.
- A correct section crosses only the two toe lines, so it divides only the bed. The exception is a section that meets a wall coinciding with the toe: it stops 0.5 m before the wall and crosses one line.
- Each section must also respect the near-node rule and the angle rule at every line it crosses.

## 7. Near-node rule

Where a section crosses a breakline, BASEmesh creates a mesh node. A breakline vertex close to that node produces tiny or very elongated elements between the two. Therefore **no breakline vertex may lie closer than the near-node distance R to a crossing** with a section or a nodestring. R is chosen by the user (Brenta: 5 m).

The vertex of the other toe of the same section does not count: in a bed narrower than R it is necessarily within R, and it is a node of the section, not of the breakline.

**How it is fixed.** The breakline moves, never the nodestring, and the crossing point stays exactly where it is:

1. every crossing of a section or nodestring with a breakline becomes a fixed vertex of the breakline. So does every T-junction (a line ending on the inside of another), so removing a vertex can never detach a line and merge two regions;
2. intermediate vertices within R of the crossing are removed;
3. a node shared with other lines is moved onto the crossing, and the connected lines follow it;
4. a node belonging to another line (for example on the opposite toe) slides along its own line to R + 0.05 m from the crossing;
5. a transverse breakline (for example the limit of a source area) passing a few metres from a section is laid onto the section. Its ends slide along the toes, and the thin strip between the two lines disappears.

**Every operation is accepted only if:**
- the line network moves by at most `max_displacement` (2 m);
- no new crossing between lines appears;
- no vertex lying on a nodestring is touched;
- no locked line is touched;
- no region point ends up closer than 1 m to a line, or closer than before if it already was;
- no new angle sharper than the minimum appears ([§8](#8-editing-lines-topology-and-angles)).

The violations that remain are reported. The user decides whether each one becomes an exception ([exceptions.md](exceptions.md)). They are reduced already when choosing the positions ([§4](#4-section-positions-and-centerpoints)).

## 8. Editing lines: topology and angles

Every edit of a breakline or nodestring (widening, near-node fixes, closures, manual repairs) follows these rules:

- **Angles: never sharper than `min_angle_deg` (30°).** No edit may create:
  - a spike inside a line, meaning an angle under 30° between two consecutive segments;
  - an angle under 30° where two lines meet, whether at a crossing, a T-junction or a shared end. This includes a section crossing a breakline.

  Sharp angles produce badly shaped elements. Angles already present in the original data are reported, not counted as new.
- **Connections.** A line ending on another is connected within 1 mm. Many ends snapped in QGIS lie 10⁻¹¹–10⁻⁹ m off the other line because of floating-point arithmetic; without the 1 mm tolerance the graph would be open. A T-junction gets a common vertex, so no tiny face appears.
- **Coincident lines.** A breakline that should coincide with a nodestring (for example a bridge closure) must contain exactly its vertices, with no other vertex in the shared stretch. A vertex even 10⁻¹⁰ m off the nodestring creates a sliver between the two lines (`fix_bridges.py`).
- **Moving ends.** Where a moved line ends on the domain boundary or on a line that does not move, its end slides along that line. Transverse lines that ended on a moved line are extended straight to it.
- **Each line keeps its fid** and stays connected to its neighbours.
- **Simplification.** New lines are simplified with a 2 cm tolerance, and vertices closer than 2 m are merged. Displacements under 10⁻⁶ m are numerical noise and are ignored.
- **The nodestring is never moved** to fix a breakline. The breakline is moved.
- **After every edit the planar graph is recounted.** Each face must have exactly one region point.

## 9. Region points

- **One point per face.** Every face of the final planar graph has exactly one region point. A face without a point has no material; a face with two points has ambiguous attributes.
- **Merged faces.** If two regions merge, the original point is kept if there is one, otherwise the one with the lowest fid.
- **Clearance.** A kept point must be at least 1 m from every line; otherwise another candidate is chosen. This does not apply to an original point in a strip narrower than 2 m (walls), where no point can be 1 m from the lines: an original point is never replaced there.
- **Kept points** are neither moved nor changed.
- **A new face** gets a point at the place farthest from its edges, with the attributes of the region it comes from.
- **Too close to a new section:** an existing point that ends up less than 1 m from a new section is replaced by a new point in the same region.
- **Defects of the original data** (null geometries, two points in one face) stay in the originals. They are removed from the derived layer only with the user's consent (`drop_regions.py`).
- **Robustness.** The result must not change when the line coordinates are rounded to 1 mm and to 1 cm, as a mesh generator merging close vertices would do (`check_regions.py`).

## 10. Manual edits by the user

The user often refines sections by hand in QGIS. After that:

- the bankpoints follow the new ends (`manual`), and the centerpoints and centerlines are recomputed (`sync_cp_bp.py`);
- side effects are repaired without moving any section vertex in plan (`fix_manual.py`):
  - z or m values different from 0, introduced by snapping onto 3D lines;
  - vertices a few millimetres from a crossing;
  - faces left without a point;
- a section may end exactly on a wall or on a building nodestring;
- all checks are run again, and the remaining violations are proposed to the user as exceptions;
- the mesh must be regenerated. Check that the `.2dm` files in `mesh/` are newer than the last layer change.

## 11. Attributes of the derived layers

The field names are mapped in `fields` of the configuration. The Brenta names are in brackets.

**Centerline**, one line per reach:

| Logical | Brenta | Content |
|---|---|---|
| name | `nome` | Line name. |
| reach | `ramo` | Reach code. |
| length | `lung_m` | Length (m). |
| s0 | `s0_asta` | For a reach cut from a longer line: the chainage of its start on that line. |

**Centerpoints**, one per section:

| Logical | Brenta | Content |
|---|---|---|
| name | `nome` | Section name. |
| reach | `stream` | Reach code. |
| s | `s_m` | True chainage in the reach (m). |
| dist_next | `dist_next` | `s` of the next section minus `s` of this one; empty for the last. |

**Bankpoints**, two per section:

| Logical | Brenta | Content |
|---|---|---|
| name | `nome` | `<section>_sx` or `<section>_dx`. |
| section | `sezione` | Section name. |
| s | `s_m` | Chainage of the section. |
| z | `z_dtm` | Value of the DTM cell under the point, never interpolated. |
| dist_cp | `dist_cp` | Plan distance from the centerpoint (m). |
| kind | `tipo` | Local maximum, highest cell, wall, `nodestring` or `manual`. |
| rule | `regola` | Which search limit applied (`mid`, `toe15`, an obstacle, the nodestring name or `manual`). |
| prom | `prom` | Prominence of the chosen maximum (m). |

**Sections**, in the nodestring layer:
- `name` and `id` are unique;
- fids and ids are consecutive in reach order, starting from `sections.first_fid` and `sections.first_id`;
- each section has two vertices, left first, and z = m = 0.
