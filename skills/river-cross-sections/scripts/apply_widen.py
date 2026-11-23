# apply_widen.py - apply the result of widen.py to the whole breakline set and validate the new planar graph
# Purpose: propagate the moved end points to the lines that touch them, slide ends onto unmoved lines, extend/move boundary-line ends,
#          and validate the new graph (simple lines, faces, region points per face). New acute angles (< rules.min_angle_deg) created
#          by the changes, inside a line or where two lines meet, are listed and flagged (a global change cannot be rejected line by
#          line here; widen.py already rejects the in-line spikes of the top lines). Locked lines are never touched.
# Inputs : work/chains.pkl, work/widen.pkl; original boundary and regions layers; locked lines (cfg.locked_lines());
#          config: widening.enabled, rules.min_angle_deg, fields.boundary.name.
# Outputs: work/widen2.pkl = dict(newf, endmap) (newf: fid -> new vertices of ALL changed breaklines; endmap: old end (x,y to mm) -> new end);
#          work/bgn.pkl = dict boundary fid -> new vertices (only changed boundaries); work/widen_faces.pkl = dict(fc, A); stdout.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/apply_widen.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, numpy as np, shapely, geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
from scipy.spatial import cKDTree

args = common.parser('apply the widening to all breaklines and boundaries, validate the graph').parse_args()
cfg = common.load(args)
WZ = cfg.get('widening')
if not WZ:
    raise SystemExit("config error: section 'widening' is missing (see config_fragments/widen.json)")
if not WZ.get('enabled', False):
    print('widening.enabled is false: nothing to do'); sys.exit(0)
if 'min_angle_deg' not in cfg.get('rules', {}):
    raise SystemExit("config error: rules.min_angle_deg is missing")
MIN_ANG = cfg['rules']['min_angle_deg']
LOCKED = cfg.locked_lines()
# C = chains.pkl; W = widen.pkl
with open(cfg.work('chains.pkl'), 'rb') as f: C = pickle.load(f)
with open(cfg.work('widen.pkl'), 'rb') as f: W = pickle.load(f)
# feat: original geometry; newf: new geometry of the moved top features
feat = C['feat']; newf = dict(W['newf'])
# endmap: old end (x,y rounded to 1 mm) -> new end coordinates, for moved top features
endmap = {}
for fid, b in newf.items():
    a = feat[fid]
    for old, new in ((a[0], b[0]), (a[-1], b[-1])):
        endmap[(round(old[0], 3), round(old[1], 3))] = new
print('moved ends', len(endmap))
# add the forced T points (endT from widen.py)
endmap.update(W['endT'])
# moved = ends displaced by more than 1 mm
moved = [k for k, v in endmap.items() if np.hypot(k[0] - v[0], k[1] - v[1]) > 1e-3]; print('ends really moved', len(moved))
# other features whose end coincides with a moved end: move the end accordingly (locked lines are skipped)
tk = set(newf); nfix = 0; lst = []; nlocked = 0
for fid, a in feat.items():
    if fid in tk: continue
    b = a.copy(); ch = False
    for e in (0, -1):
        k = (round(a[e][0], 3), round(a[e][1], 3))
        if k in endmap and np.hypot(*(endmap[k] - a[e])) > 1e-6:
            if fid in LOCKED: nlocked += 1; continue
            b[e] = endmap[k]; ch = True; lst.append((fid, e))
    if ch: newf[fid] = b; nfix += 1
print('dependent features moved at ends', nfix, lst[:30])
print('ends of locked lines left in place', nlocked)
# old = original LineStrings; to = their STRtree
keys = list(feat); old = [LineString(feat[k]) for k in keys]; to = shapely.STRtree(old)
# ends slid onto unmoved lines: a moved feature whose old end lay on another line that is NOT moved gets its new end projected onto that old line, so it remains connected
slid = []
for i, k in enumerate(keys):
    if k not in newf: continue
    b = newf[k].copy(); ch = False
    for e in (0, -1):
        if np.hypot(*(b[e] - feat[k][e])) < 1e-6: continue
        for j in to.query(Point(feat[k][e]), predicate='dwithin', distance=1e-3):
            k2 = keys[j]
            if k2 == k: continue
            if k2 not in newf and (np.hypot(*(feat[k2][0] - feat[k][e])) > 1e-3 and np.hypot(*(feat[k2][-1] - feat[k][e])) > 1e-3 or k2 not in newf):
                l2 = old[j]; q = shapely.get_coordinates(l2.interpolate(l2.project(Point(b[e]))))[0]; slid.append((k, e, k2, round(float(np.hypot(*(q - b[e]))), 3))); b[e] = q; ch = True; break
    if ch: newf[k] = b
print('ends slid onto unmoved lines', slid)
# save newf (all changed features) and endmap
with open(cfg.work('widen2.pkl'), 'wb') as f: pickle.dump(dict(newf=newf, endmap=endmap), f)
# ===== validation graph
# r = region points
r = gpd.read_file(cfg.layer('in', 'regions'), fid_as_index=True)
# L = new geometry of every breakline
L = [LineString(newf.get(f, a)) for f, a in feat.items()]
# bgn: boundary fid -> new vertices (only for boundaries whose end moved)
bgn = {}
bdf = gpd.read_file(cfg.layer('in', 'boundary'), fid_as_index=True); bname = cfg.f('boundary', 'name')
# moves: (name, end, displacement m) of boundary ends that were extended to the moved top line
moves = []
for tag, new in W['bmove'].items():
    if tag[0] != 'bd': continue
    _, k, e = tag
    b = bgn.get(k, W['bgeo'][k].copy())
    if np.hypot(*(b[e] - new)) > 1e-6: moves.append((bdf[bname][k], e, round(float(np.hypot(*(b[e] - new))), 2)))
    b[e] = new; bgn[k] = b
print('boundary ends extended', moves)
with open(cfg.work('bgn.pkl'), 'wb') as f: pickle.dump(bgn, f)
# bg = boundary lines (new where changed)
bg = [LineString(bgn.get(k, W['bgeo'][k])) for k in W['bgeo']]
# checks: number of non-simple (self-intersecting) new lines and, for comparison, in the original
print('simple?', sum(not l.is_simple for l in L), [f for f, l in zip(feat, L) if not l.is_simple][:20])
print('non-simple orig', sum(not LineString(a).is_simple for a in feat.values()))
# new planar graph: union, polygonize; number of faces and of faces <1 m2
u = unary_union(L + bg); fc = list(polygonize(u)); A = np.array([f.area for f in fc]); print('faces', len(fc), 'small<1', (A < 1).sum())
# region points per face: expect exactly one per named face
t = shapely.STRtree(fc); ix = t.query(r.geometry.values, predicate='within'); pts = np.bincount(ix[1], minlength=len(fc))
print('faces per npoints', dict(zip(*np.unique(pts, return_counts=True))), 'pts in face', len(set(ix[0])), 'of', len(r))
# faces without region point (area, centroid), top 20 by area
nop = [(round(A[i], 2), [int(c) for c in fc[i].centroid.coords[0]]) for i in np.where(pts == 0)[0]]; print('no point faces', sorted(nop, key=lambda x: -x[0])[:20])
# faces with >=2 region points (area, ids of the points)
two = [(i, list(ix[0][ix[1] == i])) for i in np.where(pts >= 2)[0]]; print('multi', [(round(A[i], 1), [int(r.index[p]) for p in ps]) for i, ps in two])
with open(cfg.work('widen_faces.pkl'), 'wb') as f: pickle.dump(dict(fc=fc, A=A), f)
# ===== angle rule: new acute angles (< MIN_ANG) in the changed lines, inside them or where they meet other lines.
# Lines are keyed ('bl', fid) / ('bd', fid); an acute angle that existed in the original data is reported as pre-existing.
orig_lines = {('bl', k): a for k, a in feat.items()}; orig_lines.update({('bd', k): a for k, a in W['bgeo'].items()})
new_lines = {('bl', k): newf.get(k, a) for k, a in feat.items()}; new_lines.update({('bd', k): bgn.get(k, a) for k, a in W['bgeo'].items()})
chg = [k for k in new_lines if not (len(new_lines[k]) == len(orig_lines[k]) and np.array_equal(new_lines[k], orig_lines[k]))]
sp_n, me_n = geom.acute_angles(new_lines, MIN_ANG, only=chg); sp_o, me_o = geom.acute_angles(orig_lines, MIN_ANG, only=chg)
cnt_o = {}
for i, _, _ in sp_o: cnt_o[i] = cnt_o.get(i, 0) + 1
cnt_n = {}
for i, _, _ in sp_n: cnt_n[i] = cnt_n.get(i, 0) + 1
new_sp = [(i, cnt_n[i], cnt_o.get(i, 0)) for i in cnt_n if cnt_n[i] > cnt_o.get(i, 0)]
pairs_o = {frozenset((i, k)) for i, k, _, _, _ in me_o}
new_me = [(i, k, round(x, 1), round(y, 1), round(a, 1)) for i, k, x, y, a in me_n if frozenset((i, k)) not in pairs_o]
print(f'angle rule (< {MIN_ANG} deg): changed lines {len(chg)}; acute vertices pre-existing {len(sp_o)}, now {len(sp_n)}; acute meetings pre-existing {len(me_o)}, now {len(me_n)}')
print('new acute vertices (line, now, before):', new_sp[:30])
print('new acute meetings (line1, line2, x, y, angle):', new_me[:30])
print('OK' if not new_sp and not new_me and not W.get('rejected') else '**CHECK** new acute angles flagged above (or moves rejected by widen.py: %d)' % len(W.get('rejected', [])))
