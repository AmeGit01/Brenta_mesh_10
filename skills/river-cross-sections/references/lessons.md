# Lessons from the Brenta case

Problems met on the Brenta (November 2026), how to recognise them and what to do.

| Symptom | Cause | What to do |
|---|---|---|
| A nodestring disappears from the mesh | Two nodestrings with the same name: BASEmesh keeps the last | Check unique names before every write (`verify3.py`) |
| Nodes of a string out of order | Multi-part nodestring | Always single-part MultiLineStringZM |
| Sections with z ≠ 0 after a manual edit | Vertices snapped in QGIS onto a 3D line | `fix_manual.py` sets z = m = 0 without moving them in plan |
| The planar graph is "open"; faces merge | Line ends snapped onto another line lie 10⁻¹¹–10⁻⁹ m off it | Connect ends within 1 mm; give every T-junction a common vertex |
| Faces 10⁻⁸ m wide (slivers) at bridges | A closure breakline should coincide with the bridge nodestring but has extra vertices 10⁻¹⁰ m off it | `fix_bridges.py`: the breakline takes exactly the nodestring vertices |
| Mesh edges of 0.2 mm | A section crosses a breakline 0.2 mm from a breakline vertex | The near-node rule must also catch distances below 1 mm; check crossings with `verify3.py` |
| Spacing 50.505 m with tolerance 0.5 | Manual edit moved a section by a few millimetres | Report it and propose it as an exception; never round |
| A region point sits on a new section | The section passes within 1 m of an existing point | Replace it with a new point in the same region (`regions2.py`) |
| Two region points in one face, points without geometry | Defects of the original data | Leave the originals as they are; remove them from the derived layer only with consent |
| A face without a point after the user's edits | The user moved or added lines and points in QGIS | `check_regions.py` and `verify3.py` after every manual session; `fix_manual.py` proposes the missing point |
| A section must coincide with a gauging nodestring | The gauge is the most reliable measurement of the model | Anchor it (`anchors`); the whole reach shifts |
| Section names drift from the true chainage | Names are nominal (index × spacing) | The true chainage is always in `s` of the centerpoint |
| The mesh in `mesh/` did not show the fix | The regenerated mesh had not been saved there | Compare the `.2dm` dates with the layers (`check_mesh.py`) before saying the mesh is up to date |
| A write fails or loses edits | The layer was open in QGIS (`-wal` file present) | Ask the user to close it; `write3.py` refuses open layers |
| `python3` has no geopandas | Two interpreters: one with geopandas and shapely, one with GDAL/OGR | Record both in `python` of the configuration and use the one each sheet names |
| Bankpoint values not reproducible in QGIS | Interpolated DTM values | Always read the cell value |
| A sharp angle gives distorted elements | A moved line or a section meets another line at a small angle | Angle rule: no new angle under 30° (`check_angles.py`) |
| A section edited by hand no longer crosses its centerline | The centerline had been cut at the last section | Each centerline runs to the end of its source line |
| New faces without a region point after manual edits | An edited section goes beyond the toe and cuts a bank, a wall or a culvert | Shorten the section, or add a point with the attributes of the region it comes from (a hole point for a culvert); ask the user |
| Merging two reaches breaks the spacing at the junction | The gap between the reaches is not a multiple of the spacing | Compute the shift needed first; move all the sections of one reach by the same amount and add sections in the gap |
| A nodestring must become a section | Example: a branch starts at a divergence nodestring | Rename it (`write3.py` `rename`); it keeps its fid; its ends are its bankpoints |
| A breakline vertex 0.1–0.8 mm from a crossing | The crossing was moved by hand after the breakline was fixed | `snap_near_nodes.py` moves any vertex farther than 1e-6 m onto the crossing |
