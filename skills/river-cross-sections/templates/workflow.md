# <Case name>: work log

One entry per action that changes the work: a layer written, a rule decided, an exception accepted, a check run after a change. Trivial file operations are not logged. The newest entry goes at the bottom.

Each entry states:

* **What changed and why.**
* **Backup tag** of every layer written (`<layer>_backup_<tag>.gpkg`).
* **Checks** run on the files read back from disk, as a numbered list with the result.
* **Open points** left for the next step.

---

## <YYYY-MM-DD>: start of the work

* **Material found:** <layers, counts, CRS, DTM, existing meshes, documents>.
* **Known defects of the original data:** <faces without a point, faces with two points, null geometries, duplicate names>.
* **Decisions taken with the user:** <spacing, near-node distance, locked/fixed/editable regions, reaches, anchors, widening>. They are recorded in `rcs_config.json` and in [rules.md](rules.md).
* **SHA-256 of the originals:** recorded in `work/sha_originals.txt`.
