# How BASEmesh and BASEMENT read the layers

These facts drive many rules of the method.

- **Unique nodestring names.** If two nodestrings have the same name, BASEmesh keeps the last one and silently drops the other. Check the names before writing.
- **Single-part nodestrings.** A nodestring must be a line with one part. The format is MultiLineStringZM with z = m = 0. BASEmesh orders the nodes of a string by distance from its first vertex, so in a multi-part string the nodes of the parts would be mixed. A node within the tolerance of two strings belongs to both.
- **Orientation.** Sections are drawn from left to right, looking downstream. In BASEMENT this corresponds to `upstream_direction: "right"`.
- **One region point per closed region.** Breaklines and nodestrings together divide the plane into faces (the planar graph). BASEmesh gives each face the attributes of the region point inside it: material (`mat_id`), maximum element area (`max_area`) and the hole flag. A face without a point has no material. A face with two points has ambiguous attributes. Whenever a line is added or moved, the graph must be recounted.
- **Holes.** Region points with the hole flag (bridges, piers, culverts) make BASEmesh leave the face empty. Their position and attributes must stay as in the originals.
- **Sections are nodestrings.** BASEMENT uses them as control strings (discharge and water level output). The model file lists every nodestring in its `STRINGDEF` block.
  - After the sections are created or renamed, `STRINGDEF` must be updated. Prepare the block (names in reach order) and give it to the user: model files are never written.
- **Section on a gauging nodestring.** A section anchored on a gauging nodestring coincides with it (same two vertices). How BASEmesh and BASEMENT treat two coincident strings must be checked on the generated mesh.
- **Regenerate the mesh after every change.** After every change to the geometry, the user regenerates the mesh in QGIS:
  - first the quality mesh;
  - then the elevation interpolation that produces the computational mesh.

  The `.2dm` files in `mesh/` are valid only if they are newer than the last layer change.
- **Tiny edges.** A section crossing a breakline a fraction of a millimetre from one of its vertices produces mesh edges of that length (seen on the Brenta: 0.2 mm). The near-node rule and the check of crossings closer than 1 mm to a vertex prevent this.
