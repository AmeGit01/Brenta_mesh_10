# check_regions.py - independent check that the derived region-point layer can be used directly as the BASEmesh region-marker layer.
# Purpose: (1) layer structure (geometry type, CRS, fields, null/empty/invalid geometries, Z);
#          (2) attributes (nulls, max_area > 0, one mat_id and one max_area set per name, hole values only on the original hole points);
#          (3) planar graph of the derived breaklines + boundary built with shapely.node + polygonize_full (verify3 uses unary_union + polygonize):
#              dangles / cut edges / invalid rings, faces without point, faces with more than one point (and whether their attributes agree),
#              points outside every face;
#          (4) robustness: the same graph after rounding all line coordinates to the grid sizes of rules.regions.robust_rounding (the mesher merges
#              nearby vertices): the face of every point must not change, and no face may gain a second point;
#          (5) geometry margins: distance of every point from the nearest line, smallest faces, narrowest faces.
# Inputs : config keys: outputs.regions / breaklines / boundary, inputs.regions (originals, for the hole field), fields.regions,
#          project.crs, rules.regions {clearance, snap, sliver_width, robust_rounding}. Optional argument: layers folder (default: paths.layers).
# Outputs: print only (numbered list, each check 'OK' or '**CHECK**').
# Run    : cd <working folder>; ~/anaconda3/bin/python3 <toolkit>/scripts/check_regions.py [-c rcs_config.json]   (geo interpreter; read-only)
# Origin : Brenta project, check_regions.py, 2026-11-19.
import sys, os, collections, warnings, numpy as np, geopandas as gpd, shapely
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
warnings.filterwarnings('ignore')
cfg = common.load(common.parser('check the region-point layer against the planar graph').parse_args())
RR = cfg['rules']['regions']; CLEAR, SNAP, SLIV, GRIDS = RR['clearance'], RR['snap'], RR['sliver_width'], RR['robust_rounding']
def rd(which, key):
    """GeoDataFrame indexed by fid; columns renamed to the logical field names (name, mat_id, max_area, hole for the regions)."""
    return gpd.read_file(cfg.layer(which, key), fid_as_index=True).rename(columns={cfg.f(key, l): l for l in cfg['fields'].get(key, {})})
rg, bl, bd, rg0 = rd('out', 'regions'), rd('out', 'breaklines'), rd('out', 'boundary'), rd('in', 'regions')
# generic constants: face area (m2) above which an empty face after rounding is real; minimum distance (m) of a point from any line
SLIVER_AREA = 1.0; MIN_CLEAR = 0.01
PHYS = {l: cfg.f('regions', l) for l in cfg['fields']['regions']}  # logical -> stored field name (for printing)
k = 0
def out(msg, ok=None):
    global k; k += 1; print(f'{k}. {msg}' + ('' if ok is None else ('  OK' if ok else '  **CHECK**')))

# ---- (1) structure
nullg = sorted(rg.index[rg.geometry.isna() | rg.geometry.is_empty])
g = rg[~(rg.geometry.isna() | rg.geometry.is_empty)]
out(f'layer: {len(rg)} rows, {len(g)} with geometry; null/empty geometry fids {nullg}; CRS {rg.crs.to_epsg()}; types {set(g.geom_type)}; has Z {bool(g.has_z.any())}; invalid {int((~g.is_valid).sum())}; fields {[PHYS.get(c, c) for c in rg.columns.drop("geometry")]}',
    not nullg and rg.crs.to_epsg() == cfg['project']['crs'] and set(g.geom_type) == {'Point'} and g.is_valid.all())
dup = g.geometry.apply(lambda p: (round(p.x, 4), round(p.y, 4))); dd = dup[dup.duplicated(keep=False)]
out(f'coincident points (0.1 mm): {sorted(dd.index)}', dd.empty)

# ---- (2) attributes
nul = {c: sorted(rg.index[rg[c].isna()]) for c in ('name', 'mat_id', 'max_area') if rg[c].isna().any()}
bad_area = sorted(rg.index[~(rg.max_area > 0)])
mats = {n: sorted(set(rg.mat_id[rg['name'] == n])) for n in set(rg['name'])}; multi_mat = {n: m for n, m in mats.items() if len(m) > 1}
mat_names = {m: sorted(set(rg['name'][rg.mat_id == m])) for m in set(rg.mat_id)}; shared = {m: n for m, n in mat_names.items() if len(n) > 1}
out(f'attributes: nulls {nul}; max_area <= 0 {bad_area}; names with more than one mat_id {multi_mat}; mat_id shared by several names {shared}',
    not nul and not bad_area and not multi_mat)
areas = {n: sorted(set(rg.max_area[rg['name'] == n])) for n in set(rg['name'])}
out(f'names with more than one max_area (allowed, present in the originals): { {n: a for n, a in areas.items() if len(a) > 1} }')
hb = rg[rg.hole.notna()]; hb0 = rg0[rg0.hole.notna()]
same_b = set(hb.index) == set(hb0.index) and all(hb.geometry[i].equals(hb0.geometry[i]) for i in hb.index)
out(f'buco: {len(hb)} points with buco (values {sorted(set(hb.hole))}), originals {len(hb0)}; same fids and positions as the originals {same_b}; names {sorted(set(hb["name"]))}', same_b)

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
# Rule (method, planar graph): endpoints closer than 1 mm to another line are connected. Here every line is snapped
# (shapely.snap, 1 mm) to the set of all endpoints, which inserts the endpoint as a vertex of the line it touches.
TOL = SNAP
ends = shapely.multipoints(np.vstack([shapely.get_coordinates(l)[[0, -1]] for l in lines0]))
tr0 = shapely.STRtree(lines0); njun = 0
for i, l in enumerate(lines0):
    for e in (shapely.get_point(l, 0), shapely.get_point(l, -1)):
        for j in tr0.query(e, predicate='dwithin', distance=TOL):
            if j != i and 0 < lines0[j].distance(e) < TOL and min(shapely.get_coordinates(lines0[j]).tolist(), key=lambda c: (c[0]-e.x)**2+(c[1]-e.y)**2) != [e.x, e.y]: njun += 1
lines = [shapely.snap(l, ends, TOL) for l in lines0]
out(f'endpoints within 1 mm of another line but not on it (T-junctions closed by snapping): {njun}')
def faces_of(grid):
    # node all lines, explode into 2-vertex segments and drop duplicates: overlapping lines (a section anchored on a gauge
    # nodestring, breaklines laid on sections) would otherwise give zero-area faces and break polygonize
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
isliver = lambda f: shapely.maximum_inscribed_circle(f, 1e-4).length < SLIV
real_empty = [j for j in empty if not isliver(F[j])]; sliv = [j for j in empty if isliver(F[j])]
out(f'faces without point: {len(real_empty)} real (areas m2 {sorted(round(F[j].area, 1) for j in real_empty)}); '
    f'slivers < 1 mm wide between nearly coincident lines: {len(sliv)} at {[(round(F[j].centroid.x, 1), round(F[j].centroid.y, 1)) for j in sliv]}', not real_empty)
desc = []
for m in multi:
    a = {(rg['name'][i], int(rg.mat_id[i]), float(rg.max_area[i]), None if rg.hole[i] != rg.hole[i] else float(rg.hole[i])) for i in m}
    desc.append((m, 'same attributes' if len(a) == 1 else f'DIFFERENT attributes {a}'))
out(f'faces with more than one point: {desc}', not multi)

# ---- (4) robustness to vertex merging
for grid in GRIDS:
    Fg, *_ = faces_of(grid); fg = assign(Fg); cg = collections.Counter(f for v in fg.values() for f in v)
    # map faces by the set of points they contain; a point whose face changes its companions is a change
    grp = lambda fo_, i: frozenset(j for j, v in fo_.items() if v and v[0] == fo_[i][0]) if fo_.get(i) else None
    changed = sorted(i for i in g.index if grp(fo, i) != grp(fg, i))
    emp = [j for j in range(len(Fg)) if cg[j] == 0]; remp = [j for j in emp if Fg[j].area > SLIVER_AREA]  # rounding widens slivers to ~1e-3 m2
    out(f'coordinates rounded to {grid*1000:g} mm: {len(Fg)} faces, without point {len(emp)} (of which larger than 1 m2: {len(remp)}), '
        f'points whose face membership changes {changed}', not changed and not remp)

# ---- (5) margins
U = shapely.union_all(lines); dist = g.geometry.apply(lambda p: U.distance(p))
near = dist[dist < CLEAR].sort_values()
out(f'points closer than {CLEAR:g} m to a line: {len(near)} ({[(i, rg['name'][i], round(d, 3)) for i, d in near.items()]}); minimum {dist.min():.3f} m (fid {dist.idxmin()})',
    dist.min() > MIN_CLEAR)
ar = sorted((round(f.area, 2), j) for j, f in enumerate(F))[:5]
out(f'smallest faces (area m2, point fids): {[(a, sorted(i for i, v in fo.items() if j in v)) for a, j in ar]}')
rad = sorted((round(shapely.maximum_inscribed_circle(f, 0.01).length, 3), j) for j, f in enumerate(F))[:5]
out(f'narrowest faces (radius of the largest inscribed circle, m; point fids): {[(r, sorted(i for i, v in fo.items() if j in v)) for r, j in rad]}')
