# fix_bridges.py  (2026-11-19; next: write3.py, then check_regions.py and verify3.py)
# Purpose: remove the sub-micrometre slivers between the bridge-closure breaklines and the bridge nodestrings.
#          Originally each closure breakline was an exact copy of its bridge nodestring (same 2 vertices). On 2026-11-09 it was extended
#          beyond both ends to the widened top lines, and later steps inserted vertices on the overlapping stretch that lie 1e-11..1e-10 m
#          off the nodestring: the two lines no longer coincide and polygonize finds slivers ~1e-8 m wide.
#          Fix (move the breakline, never the nodestring): on the stretch that overlaps the nodestring, the breakline gets EXACTLY the
#          nodestring vertices; the vertices in between are dropped; the extensions outside the nodestring are kept as they are.
#          A breakline that only touches the nodestring end (1124 at P27_valle) gets that vertex set exactly to the nodestring end.
# Acceptance (Brenta_regole_e_metodo.md par. 9): max displacement of the line network < 1e-6 m; no vertex of a nodestring touched;
#          no new crossing between lines; no locked wall line (mat11_lines.json) touched; region-point clearance unchanged.
# Inputs : argv[1] = layers folder; argv[2] = mat11_lines.json; argv[3] = output json payload for write3.py ({"bl": {fid: [[x,y],...]}}).
# Output : the payload; prints every change and the acceptance checks.
# Run    : ~/anaconda3/bin/python3 scripts/fix_bridges.py layers WD/mat11_lines.json WD/write_bridges.json   (Anaconda python3; read-only)
import sys, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
L, LOCKF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
rd = lambda n: gpd.read_file(f'{L}/{n}.gpkg', fid_as_index=True)
bl, bd, rg = rd('breaklines_50m'), rd('boundary_50m'), rd('regioni_ponti_50m'); LOCK = set(json.load(open(LOCKF)))
co = lambda g: shapely.get_coordinates(g)[:, :2]
NS = {n: co(g) for n, g in zip(bd.nome, bd.geometry)}
PAIRS = {1113: 'P17_monte', 1116: 'P20_valle', 1118: 'P27_valle', 1124: 'P27_valle', 1421: 'P13_monte_idrometro_Ponte_Cervia'}
TOL = 1e-6   # a breakline vertex closer than this to the nodestring is 'on' it
new = {}
for f, ns in PAIRS.items():
    if f in LOCK: sys.exit(f'locked line {f}')
    c, N = co(bl.geometry[f]), NS[ns]; Nl = shapely.linestrings(N)
    on = [k for k, p in enumerate(c) if Nl.distance(shapely.points(p)) < TOL]
    if not on: sys.exit(f'{f}: no vertex on {ns}')
    i0, i1 = on[0], on[-1]
    if on != list(range(i0, i1 + 1)): sys.exit(f'{f}: vertices on {ns} not contiguous {on}')
    if i0 == i1 and min(np.hypot(*(N - c[i0]).T)) < TOL:
        # only touches the nodestring at one end: snap that vertex exactly onto the end
        e = N[np.argmin(np.hypot(*(N - c[i0]).T))]; out = c.copy(); out[i0] = e
    else:
        # overlapping stretch: replace vertices i0..i1 with the nodestring vertices, oriented like the breakline
        Nn = N if np.hypot(*(N[0] - c[0])) <= np.hypot(*(N[-1] - c[0])) else N[::-1]
        out = np.vstack([c[:i0], Nn, c[i1 + 1:]])
    new[f] = out
    print(f'breakline {f} on {ns}: {len(c)} -> {len(out)} vertices; dropped/moved vertices {[list(np.round(c[k], 4)) for k in on]}')
# ---- acceptance
old_lines = {f: shapely.linestrings(co(g)) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
new_lines = dict(old_lines); new_lines.update({f: shapely.linestrings(v) for f, v in new.items()})
hd = max(shapely.hausdorff_distance(old_lines[f], new_lines[f]) for f in new)
print(f'1. max displacement (Hausdorff) {hd:.2e} m', 'OK' if hd < 1e-6 else '**CHECK**')
nsv = np.vstack(list(NS.values()))
touched = [f for f in new if any(min(np.hypot(*(co(bl.geometry[f]) - v).T)) < 1e-9 and not any(np.all(new[f] == v, axis=1)) for v in nsv)]
print(f'2. breaklines losing a vertex that coincides with a nodestring vertex: {touched}', 'OK' if not touched else '**CHECK**')
# shared vertices with other lines: a dropped vertex used by another line becomes a T-junction (reported)
allv = {}
for g_f, l in old_lines.items():
    for p in co(l): allv.setdefault((round(p[0], 6), round(p[1], 6)), set()).add(g_f)
shared = []
for f in new:
    for p in co(old_lines[f]):
        if not any(np.hypot(*(new[f] - p).T) < 1e-9):
            others = allv.get((round(p[0], 6), round(p[1], 6)), set()) - {f}
            if others: shared.append((f, sorted(others), round(new_lines[f].distance(shapely.points(p)), 12)))
print(f'3. dropped vertices shared with other breaklines (they become T-junctions on the new line, distance m): {shared}')
allL = list(new_lines.values()) + [shapely.linestrings(v) for v in NS.values()]
tr = shapely.STRtree(allL); keys = list(new_lines) + list(NS)
newx = []
for f in new:
    for j in tr.query(new_lines[f], predicate='crosses'):
        k = keys[j]
        if k != f and not old_lines[f].crosses(allL[j] if k not in old_lines else old_lines[k]): newx.append((f, k))
print(f'4. new crossings: {newx}', 'OK' if not newx else '**CHECK**')
U0, U1 = shapely.union_all(list(old_lines.values())), shapely.union_all(list(new_lines.values()))
g = rg.geometry.dropna(); d0, d1 = g.apply(U0.distance), g.apply(U1.distance)
worse = [(i, round(d0[i], 3), round(d1[i], 3)) for i in g.index if d1[i] < d0[i] - 1e-9]
print(f'5. region points closer to the breaklines than before: {worse}', 'OK' if not worse else '**CHECK**')
json.dump({'bl': {str(f): v.tolist() for f, v in new.items()}}, open(OUT, 'w'))
print('payload', OUT)
