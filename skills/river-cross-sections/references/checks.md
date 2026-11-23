# Checks

All checks run on the files **read back from disk**, with code different from the code that produced them. An error in the production code therefore cannot hide behind the same error in the check.

Each script prints a numbered list. Each line ends with `OK` or `**CHECK**`, or with nothing when it is information only. Report the result to the user as a numbered list too, and log it in `docs/workflow.md`.

## When to run what

| Moment | Scripts |
|---|---|
| Start of the work | `init_outputs.py` (SHA-256 of the originals), `graph.py --layers in` (defects of the original data) |
| After bank widening | `gaps.py`, `check_widen.py`, `check_angles.py` |
| After the near-node fix | `check_near_nodes.py`, `check_geom.py`, `check_angles.py` |
| After every write | `verify3.py`, `verify3_dtm.py`, `check_regions.py`, `check_angles.py` |
| After the first complete write | also `check_bp.py` (bankpoints recomputed independently) |
| After manual edits | `sync_cp_bp.py` (must report 0 changes once the layers are realigned), then the after-write checks |
| After the user regenerates the mesh | `check_mesh.py mesh/<file>.2dm` |
| End of the work | `init_outputs.py --check` (originals unchanged) |

## What must hold

1. **Counts:** the number of features of every layer is the expected one, derived from the data and the configuration. Examples: two bankpoints per section, one centerpoint per section, one centerline per reach.
2. **Names and ids:** unique names and ids; sections named per reach as consecutive multiples of the spacing, in reach order.
3. **Layer structure:** geometry type, CRS and fields unchanged; nodestrings single-part with z = m = 0.
4. **GeoPackage integrity:** `PRAGMA integrity_check` is ok, and the R-tree index holds as many entries as there are non-null geometries.
5. **Untouched features** are identical to the originals.
6. **Spacing:** consecutive sections are `spacing ± tol` apart along the centerline; the straight distance is checked too. Violations equal the accepted exceptions.
7. **Section geometry:** two vertices, left first, perpendicular to the centerline chord, vertices equal to the bankpoints.
8. **Crossings:** no section crosses another section or a nodestring. An anchored section may coincide with its nodestring.
9. **Lines crossed:** every section crosses the expected lines, namely the two toes, or one toe at a wall.
10. **Near-node rule:** the violations, plus crossings closer than 1 mm to a vertex, equal the accepted exceptions.
11. **Angle rule:** no new angle sharper than `min_angle_deg` where lines were created or edited (`check_angles.py`). Angles already in the original data are listed separately.
12. **Region points:** one point per face; no face without a point; attributes consistent (one `mat_id` per name, combinations as in the originals); original points not moved; no point closer than 1 m to a line unless it was already there. The result must hold after rounding the coordinates to 1 mm and 1 cm (`check_regions.py`).
13. **Bankpoints:**
    - `z` equals the value of the DTM cell under the point (`verify3_dtm.py`);
    - each bankpoint is at least `top_buffer` from the top-of-bank line;
    - recomputed with independent code, they coincide (`check_bp.py`), except for the `manual` and `nodestring` ones.
14. **Attributes:** the attributes of the centerlines, centerpoints and bankpoints agree with the geometries (`verify3.py`):
    - `s`, `dist_next` and `dist_cp`;
    - `kind` and `rule`;
    - `s0` of a reach cut from a longer line.
15. **Widening:** the width sampled every 0.5 m meets the criterion (`check_widen.py`), and the faces are the same as before.
16. **Originals unchanged:** their SHA-256 matches the one recorded at the start.
17. **Mesh** (`check_mesh.py`):
    - it is newer than the last change of the layers;
    - no edge is shorter than `min_edge`;
    - no element has material 0, which means a face without a region point;
    - the materials match the region points;
    - the nodestrings match the layer.

    The smallest element angles are information only.

## When a check fails

1. **Do not fix silently.** Find the cause and explain it to the user.
2. **If the cause is in the user's edits,** for example a face without a point after an edit in QGIS, show where it is and propose the fix (`fix_manual.py`).
3. **If it is a rule violation that cannot be removed,** propose an exception ([exceptions.md](exceptions.md)).
4. **After the fix,** run the checks again on the files read back from disk.
