# check_regions.py  (2026-11-19; independent of verify3.py, group G)
# Purpose: check that regioni_ponti_50m.gpkg can be used directly as the region-marker layer for BASEmesh quality meshing:
#          (1) layer structure (geometry type, CRS, fields, null/empty/invalid geometries, Z);
#          (2) attributes (nulls, max_area > 0, one mat_id and one max_area set per name, buco only on the original hole points);
#          (3) planar graph of breaklines_50m + boundary_50m built with shapely.node + polygonize_full (verify3 uses unary_union + polygonize):
#              dangles / cut edges / invalid rings, faces without point, faces with more than one point (and whether their attributes agree),
#              points outside every face;
#          (4) robustness: the same graph after rounding all line coordinates to 1 mm and to 1 cm (BASEmesh merges nearby vertices):
#              the face of every point must not change, and no face may gain a second point;
#          (5) geometry margins: distance of every point from the nearest line, smallest faces, narrowest faces.
# Inputs : layers/regioni_ponti_50m.gpkg, layers/breaklines_50m.gpkg, layers/boundary_50m.gpkg, layers/regioni_ponti.gpkg (originals, for buco)
# Output : print only (numbered list, each check 'OK' or '**CHECK**').
# Run    : ~/anaconda3/bin/python3 scripts/check_regions.py [layers_dir]     (Anaconda python3; read-only)
import sys, collections, warnings, numpy as np, geopandas as gpd, shapely
warnings.filterwarnings('ignore')
L = sys.argv[1] if len(sys.argv) > 1 else '/home/amedeo/Documents/Brenta_mesh_10/layers'
rd = lambda n: gpd.read_file(f'{L}/{n}.gpkg', fid_as_index=True)
rg, bl, bd, rg0 = rd('regioni_ponti_50m'), rd('breaklines_50m'), rd('boundary_50m'), rd('regioni_ponti')
k = 0
def out(msg, ok=None):
    global k; k += 1; print(f'{k}. {msg}' + ('' if ok is None else ('  OK' if ok else '  **CHECK**')))

# ---- (1) structure
nullg = sorted(rg.index[rg.geometry.isna() | rg.geometry.is_empty])
g = rg[~(rg.geometry.isna() | rg.geometry.is_empty)]
out(f'layer: {len(rg)} rows, {len(g)} with geometry; null/empty geometry fids {nullg}; CRS {rg.crs.to_epsg()}; types {set(g.geom_type)}; has Z {bool(g.has_z.any())}; invalid {int((~g.is_valid).sum())}; fields {list(rg.columns.drop("geometry"))}',
    not nullg and rg.crs.to_epsg() == 25832 and set(g.geom_type) == {'Point'} and g.is_valid.all())
dup = g.geometry.apply(lambda p: (round(p.x, 4), round(p.y, 4))); dd = dup[dup.duplicated(keep=False)]
out(f'coincident points (0.1 mm): {sorted(dd.index)}', dd.empty)

# ---- (2) attributes
nul = {c: sorted(rg.index[rg[c].isna()]) for c in ('nome', 'mat_id', 'max_area') if rg[c].isna().any()}
bad_area = sorted(rg.index[~(rg.max_area > 0)])
mats = {n: sorted(set(rg.mat_id[rg.nome == n])) for n in set(rg.nome)}; multi_mat = {n: m for n, m in mats.items() if len(m) > 1}
mat_names = {m: sorted(set(rg.nome[rg.mat_id == m])) for m in set(rg.mat_id)}; shared = {m: n for m, n in mat_names.items() if len(n) > 1}
out(f'attributes: nulls {nul}; max_area <= 0 {bad_area}; names with more than one mat_id {multi_mat}; mat_id shared by several names {shared}',
    not nul and not bad_area and not multi_mat)
areas = {n: sorted(set(rg.max_area[rg.nome == n])) for n in set(rg.nome)}
out(f'names with more than one max_area (allowed, present in the originals): { {n: a for n, a in areas.items() if len(a) > 1} }')
hb = rg[rg.buco.notna()]; hb0 = rg0[rg0.buco.notna()]
same_b = set(hb.index) == set(hb0.index) and all(hb.geometry[i].equals(hb0.geometry[i]) for i in hb.index)
out(f'buco: {len(hb)} points with buco (values {sorted(set(hb.buco))}), originals {len(hb0)}; same fids and positions as the originals {same_b}; names {sorted(set(hb.nome))}', same_b)

# ---- (3) planar graph, built differently from verify3.py
def parts(gs):
    res = []
    for gg in gs:
        if gg is None or gg.is_empty: continue
        for p in getattr(gg, 'geoms', [gg]):
            c = shapely.get_coordinates(p)
            if len(c) >= 2: res.append(shapely.linestrings(c))
    return res
lines0 = parts(bl.geometry) + parts(bd.geometry)
# T-junctions: an endpoint snapped in QGIS onto the interior of another line lies 1e-11..1e-9 m off it (floating point).
# Rule (Brenta_regole_e_metodo.md, par. 4): endpoints closer than 1 mm to another line are connected. Here every line is snapped
# (shapely.snap, 1 mm) to the set of all endpoints, which inserts the endpoint as a vertex of the line it touches.
TOL = 1e-3
ends = shapely.multipoints(np.vstack([shapely.get_coordinates(l)[[0, -1]] for l in lines0]))
tr0 = shapely.STRtree(lines0); njun = 0
for i, l in enumerate(lines0):
    for e in (shapely.get_point(l, 0), shapely.get_point(l, -1)):
        for j in tr0.query(e, predicate='dwithin', distance=TOL):
            if j != i and 0 < lines0[j].distance(e) < TOL and min(shapely.get_coordinates(lines0[j]).tolist(), key=lambda c: (c[0]-e.x)**2+(c[1]-e.y)**2) != [e.x, e.y]: njun += 1
lines = [shapely.snap(l, ends, TOL) for l in lines0]
out(f'endpoints within 1 mm of another line but not on it (T-junctions closed by snapping): {njun}')
def faces_of(grid):
    # node all lines, explode into 2-vertex segments and drop duplicates: overlapping lines (B00400 on idrometro_Borgo,
    # breaklines 987 and 1225 laid on sections) would otherwise give zero-area faces and break polygonize
    ls = lines if grid is None else [shapely.set_precision(l, grid) for l in lines]
    noded = shapely.node(shapely.multilinestrings([l for l in ls if not l.is_empty]))
    seen, segs = set(), []
    for part in shapely.get_parts(noded):
        c = shapely.get_coordinates(part)
        for a, b in zip(c[:-1], c[1:]):
            ka, kb = tuple(np.round(a, 7)), tuple(np.round(b, 7))
            if ka == kb: continue
            key = (ka, kb) if ka < kb else (kb, ka)
            if key not in seen: seen.add(key); segs.append(shapely.linestrings(list(key)))  # rounded coords: shared endpoints stay identical
    polys, cuts, dangles, invalid = shapely.polygonize_full(segs)
    return list(shapely.get_parts(polys)), len(shapely.get_parts(cuts)), len(shapely.get_parts(dangles)), len(shapely.get_parts(invalid))
def assign(faces):
    tr = shapely.STRtree(faces); ip, ifc = tr.query(g.geometry.values, predicate='within')
    f_of = collections.defaultdict(list)
    for p, f in zip(ip, ifc): f_of[g.index[p]].append(int(f))
    return f_of
F, ncut, ndang, ninv = faces_of(None); fo = assign(F)
cnt = collections.Counter(f for v in fo.values() for f in v)
outside = sorted(i for i in g.index if i not in fo); twice = sorted(i for i, v in fo.items() if len(v) > 1)
empty = [j for j in range(len(F)) if cnt[j] == 0]
multi = sorted(sorted(i for i, v in fo.items() if j in v) for j, c in cnt.items() if c > 1)
out(f'planar graph (node + polygonize_full): {len(lines)} lines, {len(F)} faces; dangles {ndang}, cut edges {ncut}, invalid rings {ninv}', ninv == 0)
out(f'points outside every face {outside}; points in more than one face {twice}', not outside and not twice)
# a face without point is a 'sliver' if its largest inscribed circle has radius < 1 mm: two nearly coincident lines, not a region
SLIV = 1e-3
isliver = lambda f: shapely.maximum_inscribed_circle(f, 1e-4).length < SLIV
real_empty = [j for j in empty if not isliver(F[j])]; sliv = [j for j in empty if isliver(F[j])]
out(f'faces without point: {len(real_empty)} real (areas m2 {sorted(round(F[j].area, 1) for j in real_empty)}); '
    f'slivers < 1 mm wide between nearly coincident lines: {len(sliv)} at {[(round(F[j].centroid.x, 1), round(F[j].centroid.y, 1)) for j in sliv]}', not real_empty)
desc = []
for m in multi:
    a = {(rg.nome[i], int(rg.mat_id[i]), float(rg.max_area[i]), None if rg.buco[i] != rg.buco[i] else float(rg.buco[i])) for i in m}
    desc.append((m, 'same attributes' if len(a) == 1 else f'DIFFERENT attributes {a}'))
out(f'faces with more than one point: {desc}', not multi)

# ---- (4) robustness to vertex merging
for grid in (0.001, 0.01):
    Fg, *_ = faces_of(grid); fg = assign(Fg); cg = collections.Counter(f for v in fg.values() for f in v)
    # map faces by the set of points they contain; a point whose face changes its companions is a change
    grp = lambda fo_, i: frozenset(j for j, v in fo_.items() if v and v[0] == fo_[i][0]) if fo_.get(i) else None
    changed = sorted(i for i in g.index if grp(fo, i) != grp(fg, i))
    emp = [j for j in range(len(Fg)) if cg[j] == 0]; remp = [j for j in emp if Fg[j].area > 1.0]  # rounding widens slivers to ~1e-3 m2
    out(f'coordinates rounded to {grid*1000:g} mm: {len(Fg)} faces, without point {len(emp)} (of which larger than 1 m2: {len(remp)}), '
        f'points whose face membership changes {changed}', not changed and not remp)

# ---- (5) margins
U = shapely.union_all(lines); dist = g.geometry.apply(lambda p: U.distance(p))
near = dist[dist < 1.0].sort_values()
out(f'points closer than 1 m to a line: {len(near)} ({[(i, rg.nome[i], round(d, 3)) for i, d in near.items()]}); minimum {dist.min():.3f} m (fid {dist.idxmin()})',
    dist.min() > 0.01)
ar = sorted((round(f.area, 2), j) for j, f in enumerate(F))[:5]
out(f'smallest faces (area m2, point fids): {[(a, sorted(i for i, v in fo.items() if j in v)) for a, j in ar]}')
rad = sorted((round(shapely.maximum_inscribed_circle(f, 0.01).length, 3), j) for j, f in enumerate(F))[:5]
out(f'narrowest faces (radius of the largest inscribed circle, m; point fids): {[(r, sorted(i for i, v in fo.items() if j in v)) for r, j in rad]}')
