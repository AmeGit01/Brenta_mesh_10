# check_widen.py - verify the widening, read back from the derived layers on disk (print-only, sections A-I)
# Purpose: verify that boundary lines and breaklines changed only where intended, that no changed line crosses another, that the
#          channel widths reach the targets of widening.zones, and that no new acute angle (< rules.min_angle_deg) was created.
# Inputs : derived layers breaklines and boundary (outputs) and the original ones (inputs); original regions layer (the region points
#          that classify the faces); work/cltab.pkl (centerline points, keyed by centerline name); config: widening.zones
#          (centerline, s_from, s_to, mode, min, optional check_min), face_classes.{fixed,editable} + widening.{bank_class,wall_classes},
#          rules.min_angle_deg, params.widen.cltab_alias, fields.boundary.name, fields.regions.name, cfg.is_section.
# Outputs: none (stdout), sections:
#          A boundary features changed;  B breaklines changed;  C changed lines crossing another line;  D faces rebuilt from the layers;
#          E widths per zone (samples every 0.5 m along the centerline; W = top-to-top, SL/SR = bank widths) with the runs below the
#          check limit;  G crossings that already existed in the original data;  H sections that meet exactly 3 breaklines;
#          I new acute angles in the changed lines.  Last line: OK / **CHECK** (new crossings or new acute angles).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/check_widen.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, numpy as np, shapely, geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize

args = common.parser('check the widening on the derived layers').parse_args()
cfg = common.load(args)
WZ = cfg.get('widening')
if not WZ:
    raise SystemExit("config error: section 'widening' is missing (see config_fragments/widen.json)")
if not WZ.get('enabled', False):
    print('widening.enabled is false: nothing to do'); sys.exit(0)
for k in ('bank_class',):
    if k not in WZ: raise SystemExit(f'config error: widening.{k} is missing')
FC = cfg['face_classes']
for k in ('fixed',):
    if k not in FC: raise SystemExit(f'config error: face_classes.{k} is missing')
if 'min_angle_deg' not in cfg.get('rules', {}):
    raise SystemExit("config error: rules.min_angle_deg is missing")
MIN_ANG = cfg['rules']['min_angle_deg']
ALIAS = cfg.get('params', {}).get('widen', {}).get('cltab_alias', {})
fixed = set(FC['fixed']); topc = fixed | {WZ['bank_class']} | set(WZ.get('wall_classes', []))
bname = cfg.f('boundary', 'name'); rname = cfg.f('regions', 'name')
# rd(): read a layer with the fid as index. bl/bd = derived breaklines/boundary, bl0/bd0 = originals, rg = original region points
rd = lambda p: gpd.read_file(p, fid_as_index=True)
bl, bl0 = rd(cfg.layer('out', 'breaklines')), rd(cfg.layer('in', 'breaklines'))
bd, bd0 = rd(cfg.layer('out', 'boundary')), rd(cfg.layer('in', 'boundary'))
rg = rd(cfg.layer('in', 'regions'))
def co(g): return shapely.get_coordinates(next(iter(shapely.get_parts(g))))
# A. boundary features whose geometry differs from the original: (fid, name, max abs coordinate shift in m).
dif = [(k, bd0[bname][k], float(np.abs(co(bd.geometry[k]) - co(bd0.geometry[k])).max())) for k in bd0.index
       if k in bd.index and not bd.geometry[k].equals_exact(bd0.geometry[k], 0)]
print('A. boundary features changed', dif)
# B. breaklines whose coordinates (count or values) differ from the original: fA = new coordinates, fB = original coordinates.
keep = bl.dropna(subset=['geometry']); keep = keep[~keep.geometry.is_empty]
fA = {k: co(g) for k, g in keep.geometry.items()}
fB = {k: co(g) for k, g in bl0.dropna(subset=['geometry']).geometry.items() if not g.is_empty}
chg = [k for k in fA if k in fB and not (len(fA[k]) == len(fB[k]) and np.array_equal(fA[k], fB[k]))]; print('B. breaklines changed', len(chg))
# C. for each changed line, other lines that it properly crosses ('crosses' predicate); also lines that are not simple.
ls = {k: LineString(v) for k, v in fA.items()}
rs = [ls[k] for k in ls]; keys = list(ls); T = shapely.STRtree(rs)
xs = []
for k in chg:
    for j in T.query(ls[k], predicate='crosses'):
        o = keys[j]
        if o != k: xs.append((k, o))
print('C. changed lines crossing another line', len(xs), xs[:20]); print('   not simple', [k for k in ls if not ls[k].is_simple][:10])
# D. rebuild the planar graph (breaklines + boundary excluding the section nodestrings), give each face the name of an original region
# point it contains, and use rays against two outlines: Rb = fixed-class edges (toe), Rc = fixed + bank + wall edges (top of bank).
gb = [LineString(co(g)) for n, g in zip(bd[bname], bd.geometry) if not cfg.is_section(n)]
fc = list(polygonize(unary_union(list(ls.values()) + gb))); t = shapely.STRtree(fc); rg2 = rg.dropna(subset=['geometry']); ix = t.query(rg2.geometry.values, predicate='within')
rows = []; seen = set()
for p, f in zip(*ix):
    if int(f) in seen: continue
    seen.add(int(f)); rows.append(dict(face=int(f), nome=rg2[rname].iloc[int(p)]))
print('D. faces', len(fc), 'with point', len(rows))
tb = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in fixed); tc = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in topc)
Rb, Rc = geom.Rays(tb), geom.Rays(tc)
with open(cfg.work('cltab.pkl'), 'rb') as f: T0 = pickle.load(f)
def runs(m, ss, W=None):
    up = np.where(np.diff(np.r_[0, m.astype(int), 0]) == 1)[0]; dn = np.where(np.diff(np.r_[0, m.astype(int), 0]) == -1)[0] - 1
    return [(round(float(ss[a])), round(float(ss[b]))) for a, b in zip(up, dn)]
# E. for each centerline of the zones: sample every 0.5 m (s from 1 m to length-1 m); normal from the chord s-1..s+1 m; nearest toe on the
# left (tl) and right (tr), then the nearest top-of-bank edge beyond each toe (cl_, cr_). W = cl_+cr_ = top-to-top width; SL = cl_-tl, SR = cr_-tr.
# Samples without a toe or top edge on both sides give NaN. Each sample belongs to the first zone whose range contains its chainage.
for name in dict.fromkeys(z['centerline'] for z in WZ['zones']):
    k = name if name in T0 else ALIAS.get(name)
    if k not in T0: raise SystemExit(f"cltab.pkl has no centerline '{name}' (keys {list(T0)})")
    ln = LineString(T0[k]['q'])
    ss = np.arange(1, ln.length - 1, 0.5); Pp = shapely.get_coordinates(shapely.line_interpolate_point(ln, ss)); A = shapely.get_coordinates(shapely.line_interpolate_point(ln, ss - 1)); B = shapely.get_coordinates(shapely.line_interpolate_point(ln, ss + 1)); d = (B - A) / np.hypot(*(B - A).T)[:, None]; n = np.c_[-d[:, 1], d[:, 0]]
    W = []; SL = []; SR = []
    for i in range(len(ss)):
        hb = Rb.hits(Pp[i], n[i], 1500); hc = Rc.hits(Pp[i], n[i], 1500)
        if len(hb) == 0 or not (hb > 0).any() or not (hb < 0).any(): W.append(np.nan); SL.append(np.nan); SR.append(np.nan); continue
        tl = hb[hb > 0].min(); tr = -hb[hb < 0].max(); cc1 = hc[hc > tl - 1e-6]; cc2 = hc[hc < -tr + 1e-6]
        if not len(cc1) or not len(cc2): W.append(np.nan); SL.append(np.nan); SR.append(np.nan); continue
        cl_ = cc1.min(); cr_ = -cc2.max(); W.append(cl_ + cr_); SL.append(cl_ - tl); SR.append(cr_ - tr)
    W, SL, SR = np.array(W), np.array(SL), np.array(SR); taken = np.zeros(len(ss), bool)
    for kz, z in enumerate(WZ['zones']):
        if z['centerline'] != name: continue
        m = (ss >= z.get('s_from', 0)) & ((ss <= z['s_to']) if z.get('s_to') is not None else True) & ~taken; taken |= m
        if not m.any(): continue
        lim = z.get('check_min', z['min']); tag = f"E. {name} zone {kz} ({z['mode']}, s {z.get('s_from', 0)}..{z.get('s_to')}, limit {lim})"
        if z['mode'] == 'corridor':
            print(f"{tag}: {int(m.sum())} samples; W min/p1/median {np.nanmin(W[m]):.2f} {np.nanpercentile(W[m], 1):.2f} {np.nanmedian(W[m]):.2f}; W<limit samples {int((W[m] < lim).sum())} ({(W[m] < lim).mean() * 100:.2f}%)")
            print('   runs W<limit:', runs(m & (W < lim), ss)[:30])
        else:
            print(f"{tag}: {int(m.sum())} samples; bank L min/p1 {np.nanmin(SL[m]):.2f} {np.nanpercentile(SL[m], 1):.2f}, R {np.nanmin(SR[m]):.2f} {np.nanpercentile(SR[m], 1):.2f}; side<limit: L {int((SL[m] < lim).sum())} R {int((SR[m] < lim).sum())}")
            print('   runs bank<limit:', runs(m & ((SL < lim) | (SR < lim)), ss)[:30])
# G. for the crossing pairs found in C, whether the same pair already crossed in the original geometry (True = pre-existing).
Lo = {k: LineString(v) for k, v in fB.items()}
pre = [(a, b, Lo[a].crosses(Lo[b])) for a, b in xs]
print('G. pairs crossing in original too:', pre)
# H. sections (boundary nodestrings of the section pattern) that intersect exactly 3 breaklines: listed with the intersection points (informational).
Tt = shapely.STRtree(list(ls.values()))
sec = bd[[cfg.is_section(n) for n in bd[bname]]]
for nome, g in zip(sec[bname], sec.geometry):
    l = LineString(co(g)); ids = [keys[i] for i in Tt.query(l, predicate='intersects')]
    if len(ids) == 3: print('H. 3-lines', nome, ids, [Point(p).wkt for p in shapely.get_coordinates(l.intersection(unary_union([ls[i] for i in ids])))])
# I. angle rule: new acute angles (< MIN_ANG) in the changed lines (breaklines and boundary lines), inside them or where they meet others.
orig_lines = {('bl', k): v for k, v in fB.items()}; orig_lines.update({('bd', k): co(g) for k, g in bd0.geometry.items()})
new_lines = {('bl', k): v for k, v in fA.items()}; new_lines.update({('bd', k): co(g) for k, g in bd.geometry.items() if k in bd0.index})
chg_all = [k for k in new_lines if k in orig_lines and not (len(new_lines[k]) == len(orig_lines[k]) and np.array_equal(new_lines[k], orig_lines[k]))]
sp_n, me_n = geom.acute_angles(new_lines, MIN_ANG, only=chg_all); sp_o, me_o = geom.acute_angles(orig_lines, MIN_ANG, only=chg_all)
cnt_o = {}; cnt_n = {}
for i, _, _ in sp_o: cnt_o[i] = cnt_o.get(i, 0) + 1
for i, _, _ in sp_n: cnt_n[i] = cnt_n.get(i, 0) + 1
new_sp = [(i, cnt_n[i], cnt_o.get(i, 0)) for i in cnt_n if cnt_n[i] > cnt_o.get(i, 0)]
pairs_o = {frozenset((i, k)) for i, k, _, _, _ in me_o}
new_me = [(i, k, round(x, 1), round(y, 1), round(a, 1)) for i, k, x, y, a in me_n if frozenset((i, k)) not in pairs_o]
print(f'I. acute angles (< {MIN_ANG} deg) in {len(chg_all)} changed lines: vertices pre-existing {len(sp_o)}, now {len(sp_n)}; meetings pre-existing {len(me_o)}, now {len(me_n)}')
print('   new acute vertices (line, now, before):', new_sp[:30]); print('   new acute meetings (line1, line2, x, y, angle):', new_me[:30])
newx = [p for p in pre if not p[2]]
print('OK' if not newx and not new_sp and not new_me else f'**CHECK** new crossings {len(newx)}, new acute vertices {len(new_sp)}, new acute meetings {len(new_me)}')
