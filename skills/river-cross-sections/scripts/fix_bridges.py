# fix_bridges.py - remove the sub-micrometre slivers between closure breaklines and the nodestrings they run along
# Purpose: a closure breakline starts as an exact copy of its nodestring (same vertices). When it is later extended beyond the nodestring
#          ends and vertices are inserted on the overlapping stretch, these vertices can lie 1e-11..1e-10 m off the nodestring: the two
#          lines no longer coincide and polygonize finds slivers ~1e-8 m wide.
#          Fix (move the breakline, never the nodestring): on the stretch that overlaps the nodestring, the breakline gets EXACTLY the
#          nodestring vertices; the vertices in between are dropped; the extensions outside the nodestring are kept as they are.
#          A breakline that only touches the nodestring end gets that vertex set exactly to the nodestring end.
#          The (breakline, nodestring) pairs are FOUND AUTOMATICALLY: a non-section nodestring N (optionally limited by
#          params.fix_bridges.nodestring_regex) and a non-locked breakline B form a pair when
#            * overlap : the length of B within params.tol of N is > params.min_overlap   (B runs along N), or
#            * touch   : B has a vertex within params.tol of an END vertex of N and no overlap.
#          A pair listed in params.fix_bridges.exclude ([[breakline fid, nodestring name], ...]) is reported and skipped.
#          Pairs already exact give no change (not written to the payload).
# Angle rule: a pair whose fix would create an angle sharper than rules.min_angle_deg (inside the breakline, or between it and another
#          line) is skipped, reported and counted.
# Acceptance: max displacement of the line network < params.max_shift; no vertex of a nodestring touched; no new crossing between
#          lines; region-point clearance unchanged; locked lines are never touched (pairs with a locked line are skipped and reported).
# Inputs : derived layers breaklines, boundary, regions (cfg 'outputs'); locked lines work/<cfg locked.lines_file> (locked_lines.py);
#          cfg sections.name_pattern, fields.boundary.name; cfg params.fix_bridges {tol, min_overlap, max_shift, nodestring_regex, exclude}.
#          argv: output payload json.
# Output : payload {"bl": {fid: [[x,y],...]}}  for write3.py; prints the pairs found, every change and the acceptance checks.
# Run    : cd <working folder> ; ~/anaconda3/bin/python3 <toolkit>/scripts/fix_bridges.py [-c rcs_config.json] payload.json
#          then  /usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>     (read-only on the layers)
import sys, os, re, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
ap = common.parser('find closure breaklines that run along a nodestring and make them coincide with it'); ap.add_argument('out')
args = ap.parse_args(); cfg = common.load(args); OUT = args.out
P = cfg['params']['fix_bridges']; TOL = P['tol']          # a breakline vertex closer than TOL to the nodestring is 'on' it
rd = lambda k: gpd.read_file(cfg.layer('out', k), fid_as_index=True)
bl, bd, rg = rd('breaklines'), rd('boundary'), rd('regions'); LOCK = cfg.locked_lines()
co = lambda g: shapely.get_coordinates(g)[:, :2]
bn = cfg.f('boundary', 'name')
NS = {n: co(g) for n, g in zip(bd[bn], bd.geometry)}                       # every boundary line (for the acceptance checks)
cand = [n for n in NS if not cfg.is_section(n) and (P.get('nodestring_regex') is None or re.search(P['nodestring_regex'], n))]
EXC = {(int(f), n) for f, n in P.get('exclude', [])}
BL = {int(f): co(g) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
BLl = {f: shapely.linestrings(c) for f, c in BL.items()}
tree = shapely.STRtree(list(BLl.values())); keys = list(BLl)

# ---- 1. find the pairs
pairs = []                                                                 # (fid, nodestring, kind)
for n in cand:
    N = NS[n]; Nl = shapely.linestrings(N); Nb = Nl.buffer(TOL)
    for j in tree.query(Nb):
        f = keys[j]; c = BL[f]
        d = shapely.distance(shapely.points(c), Nl); on = np.where(d < TOL)[0]
        if len(on) == 0: continue
        ov = BLl[f].intersection(Nb).length
        if ov > P['min_overlap']: kind = 'overlap'
        elif len(on) == 1 and min(np.hypot(*(N[[0, -1]] - c[on[0]]).T)) < TOL: kind = 'touch'
        else: continue                                                      # a plain crossing
        if f in LOCK: print(f'pair {f} {n} ({kind}): locked line, skipped'); continue
        if (f, n) in EXC: print(f'pair {f} {n} ({kind}): excluded by the configuration, skipped'); continue
        pairs.append((f, n, kind))
pairs.sort()
print(f'pairs found: {len(pairs)}')
for f, n, k in pairs: print(f'  breakline {f}  nodestring {n}  ({k})')

# ---- 2. the fix, pair by pair
new = {}; MIN_ANGLE = cfg.min_angle(); n_ang = 0
NS_LINES = {('bd', n): v for n, v in NS.items()}
for f, ns, kind in pairs:
    c, N = new.get(f, BL[f]), NS[ns]; Nl = shapely.linestrings(N)
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
    if out.shape == c.shape and np.array_equal(out, c): print(f'breakline {f} on {ns}: already exact, no change'); continue
    na = common.new_acute_angles(MIN_ANGLE, {('bl', f): c}, {('bl', f): out},
                                 {**NS_LINES, **{('bl', g): new.get(g, BL[g]) for g in BL if g != f}})
    if na:
        n_ang += 1; print(f'breakline {f} on {ns}: NOT fixed, it would create an acute angle {na[0][3]:.1f} deg at ({na[0][2][0]:.2f}, {na[0][2][1]:.2f})'); continue
    new[f] = out
    print(f'breakline {f} on {ns}: {len(c)} -> {len(out)} vertices; dropped/moved vertices {[np.round(c[k], 4).tolist() for k in on]}')
print(f'pairs rejected by the angle rule (< {MIN_ANGLE:g} deg): {n_ang}')
if not new:
    json.dump({'bl': {}}, open(OUT, 'w')); print('nothing to change; payload', OUT, '(empty)'); sys.exit(0)

# ---- 3. acceptance
old_lines = BLl
new_lines = dict(old_lines); new_lines.update({f: shapely.linestrings(v) for f, v in new.items()})
hd = max(shapely.hausdorff_distance(old_lines[f], new_lines[f]) for f in new)
print(f'1. max displacement (Hausdorff) {hd:.2e} m', 'OK' if hd < P['max_shift'] else '**CHECK**')
nsv = np.vstack(list(NS.values()))
touched = [f for f in new if any(min(np.hypot(*(BL[f] - v).T)) < 1e-9 and not any(np.all(new[f] == v, axis=1)) for v in nsv)]
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
tr = shapely.STRtree(allL); allk = list(new_lines) + list(NS)
newx = []
for f in new:
    for j in tr.query(new_lines[f], predicate='crosses'):
        k = allk[j]
        if k != f and not old_lines[f].crosses(allL[j] if k not in old_lines else old_lines[k]): newx.append((f, k))
print(f'4. new crossings: {newx}', 'OK' if not newx else '**CHECK**')
U0, U1 = shapely.union_all(list(old_lines.values())), shapely.union_all(list(new_lines.values()))
g = rg.geometry.dropna(); d0, d1 = g.apply(U0.distance), g.apply(U1.distance)
worse = [(i, round(d0[i], 3), round(d1[i], 3)) for i in g.index if d1[i] < d0[i] - 1e-9]
print(f'5. region points closer to the breaklines than before: {worse}', 'OK' if not worse else '**CHECK**')
json.dump({'bl': {str(f): v.tolist() for f, v in new.items()}}, open(OUT, 'w'))
print('payload', OUT)
