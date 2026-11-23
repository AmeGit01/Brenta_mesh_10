# fix_manual.py - repair the side effects of sections edited by hand, without moving any section/nodestring vertex in plan
# Purpose: after hand edits of sections in a GIS:
#   1. sections with z or m different from 0 (vertices snapped onto a 3D line): z = m = 0 (plan coordinates unchanged);
#   2. a section that crosses a breakline at less than params.near from a breakline vertex (but not exactly on it): that vertex is moved
#      onto the crossing point, in every breakline that shares it (rule: move the breakline, never the nodestring). Not done if the
#      vertex belongs to a non-section nodestring or to a locked line: such cases are only reported;
#   3. faces of the planar graph (breaklines + all boundary lines) without a region point: a new point at the pole of inaccessibility
#      (polylabel), with the attributes of the ORIGINAL region (original regions layer, graph of the original breaklines + boundary)
#      whose face contains that point; ambiguous or missing origin -> reported, no point.
#      Angle rule: a move that would create an angle sharper than rules.min_angle_deg (inside a breakline, or between it and another
#      line) is not done, it is reported and counted.
#   It also reports section ends lying at 0 < d < params.end_gap_report from a line (ends that should be snapped exactly).
# Inputs : derived layers breaklines, boundary, regions (cfg 'outputs'); original layers breaklines, boundary, regions (cfg 'inputs');
#          locked lines work/<cfg locked.lines_file> (locked_lines.py); cfg sections.name_pattern, fields;
#          cfg params.fix_manual {near, polylabel_tol, end_gap_report}. argv: output payload json.
# Output : payload {bd: {fid: coords}, bl: {fid: coords}, reg_new: [{name, mat_id, max_area, hole, x, y}]} (logical keys, for write3.py);
#          prints every change.
# Run    : cd <working folder> ; ~/anaconda3/bin/python3 <toolkit>/scripts/fix_manual.py [-c rcs_config.json] payload.json
#          then  /usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>      (read-only on the layers)
import sys, os, json, collections, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union, polylabel
ap = common.parser('repair side effects of hand-edited sections'); ap.add_argument('out')
args = ap.parse_args(); cfg = common.load(args); OUT = args.out
P = cfg['params']['fix_manual']; NEAR = P['near']; F = cfg.f
rd = lambda which, k: gpd.read_file(cfg.layer(which, k), fid_as_index=True)
bl, bd, rg = rd('out', 'breaklines'), rd('out', 'boundary'), rd('out', 'regions'); LOCK = cfg.locked_lines()
co = lambda g: shapely.get_coordinates(g)[:, :2]
bn = F('boundary', 'name'); rn, rm, ra, rh = (F('regions', k) for k in ('name', 'mat_id', 'max_area', 'hole'))
sec = bd[[cfg.is_section(n) for n in bd[bn]]]; oth = bd[[not cfg.is_section(n) for n in bd[bn]]]
# 1. sections with z/m != 0
out_bd = {}
for f, g in sec.geometry.items():
    z = shapely.get_coordinates(g, include_z=True)[:, 2]
    if np.abs(z).max() > 0: out_bd[int(f)] = co(g).tolist(); print('section z set to 0:', sec[bn][f], z.tolist())
# 2. near-coincident crossings
Fl = {int(f): co(g).copy() for f, g in bl.geometry.items() if g is not None and not g.is_empty}
NSV = {tuple(np.round(p, 6)) for g in oth.geometry for p in co(g)}
moved = collections.OrderedDict()
# angle rule: lines that stay (nodestrings and sections), current state of the breaklines (updated with every accepted move)
MIN_ANGLE = cfg.min_angle(); n_ang = 0
BD_LINES = {('bd', k): co(g) for k, g in bd.geometry.items() if g is not None and not g.is_empty}
cur = {h: c.copy() for h, c in Fl.items()}
for nm, g in zip(sec[bn], sec.geometry):
    l = LineString(co(g))
    for f, c in Fl.items():
        lf = LineString(c)
        if not l.intersects(lf): continue
        for p in co(l.intersection(lf)):
            d = np.hypot(*(c - p).T); j = int(np.argmin(d))
            if not (1e-9 < d[j] < NEAR): continue
            v = tuple(c[j]); key = tuple(np.round(v, 6))
            share = [h for h, cc in Fl.items() if (np.hypot(*(cc - np.array(v)).T) < 1e-9).any()]
            if key in NSV or any(h in LOCK for h in share):
                print('NOT moved (nodestring or locked line):', nm, f, round(d[j] * 1000, 1), 'mm', share); continue
            # angle rule: the move of vertex v to p, in every line that shares it
            newc = {h: np.where((np.hypot(*(cur[h] - np.array(v)).T) < 1e-9)[:, None], p, cur[h]) for h in share}
            na = common.new_acute_angles(MIN_ANGLE, {('bl', h): cur[h] for h in share}, {('bl', h): newc[h] for h in share},
                                         {**BD_LINES, **{('bl', h): c for h, c in cur.items() if h not in share}})
            if na:
                n_ang += 1; print(f'NOT moved (new acute angle {na[0][3]:.1f} deg at ({na[0][2][0]:.2f}, {na[0][2][1]:.2f})):', nm, f, round(d[j] * 1000, 1), 'mm', share); continue
            cur.update(newc)
            moved[key] = (nm, np.array(v), p, share); print(f'vertex moved onto the crossing: {nm} lines {share} by {d[j] * 1000:.1f} mm')
print('moves rejected by the angle rule (< %g deg):' % MIN_ANGLE, n_ang)
out_bl = {}
for key, (nm, v, p, share) in moved.items():
    for h in share:
        c = out_bl.get(h, Fl[h].copy()) if isinstance(out_bl.get(h), np.ndarray) else Fl[h].copy()
        i = np.hypot(*(c - v).T) < 1e-9; c[i] = p; out_bl[h] = c
out_bl = {h: c.tolist() for h, c in out_bl.items()}
# section ends close to, but not on, a line
U = unary_union([LineString(c) for c in Fl.values()] + [LineString(co(g)) for g in oth.geometry])
gap = [(nm, i, round(U.distance(Point(p)) * 1000, 2)) for nm, g in zip(sec[bn], sec.geometry) for i, p in enumerate(co(g)) if 0 < U.distance(Point(p)) < P['end_gap_report']]
print('section ends at 0-%g mm from a line (mm):' % (P['end_gap_report'] * 1000), gap)
# 3. faces without region point (graph with the corrected breaklines)
F2 = {**Fl, **{h: np.array(c) for h, c in out_bl.items()}}
ln = [LineString(c) for c in F2.values()] + [LineString(co(g)) for g in bd.geometry]
fc = list(polygonize(unary_union(ln))); T = shapely.STRtree(fc); g = rg[rg.geometry.notna()]
cnt = collections.Counter(int(f) for p, f in zip(*T.query(g.geometry.values, predicate='within')))
empty = [i for i in range(len(fc)) if cnt[i] == 0]; print('faces', len(fc), 'without point', len(empty))
rg0 = rd('in', 'regions'); ob = rd('in', 'breaklines'); obd = rd('in', 'boundary')
OL = [LineString(co(x)) for x in list(ob.geometry) + list(obd.geometry) if x is not None and not x.is_empty]
ofc = list(polygonize(unary_union(OL))); TO = shapely.STRtree(ofc); og = rg0[rg0.geometry.notna()]; oatt = {}
for p, f in zip(*TO.query(og.geometry.values, predicate='within')): oatt.setdefault(int(f), []).append(og.index[p])
reg_new = []
for i in empty:
    q = polylabel(fc[i], P['polylabel_tol']); f0 = TO.query(q, predicate='within'); src = [s for x in f0 for s in oatt.get(int(x), [])]
    names = {rg0[rn][s] for s in src}
    if len(names) != 1: print('face', i, 'area %.1f' % fc[i].area, 'origin ambiguous/missing', sorted(names), '-> no point'); continue
    s = min(src); r = rg0.loc[s]; hv = r[rh]
    reg_new.append(dict(name=r[rn], mat_id=int(r[rm]), max_area=float(r[ra]), hole=None if hv != hv else float(hv), x=q.x, y=q.y))
    print(f'new region point: face {i} area {fc[i].area:.1f} m2, clearance {fc[i].exterior.distance(q):.2f} m, attributes of original fid {s} ({r[rn]}, mat_id {int(r[rm])}, max_area {r[ra]})')
json.dump(dict(bd=out_bd, bl=out_bl, reg_new=reg_new), open(OUT, 'w')); print('written', OUT, 'bd', len(out_bd), 'bl', len(out_bl), 'reg_new', len(reg_new))
