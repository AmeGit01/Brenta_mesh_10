# widen.py - how far each top-of-bank line must move outward, and the new geometry of the moved lines
# Purpose: along every centerline named in config widening.zones, measure toe / top-of-bank / next outer line distances on the normal,
#          compute the outward shift that gives the wanted width (zone mode 'corridor': top-to-top width >= min, shift split
#          symmetrically; mode 'bank': each bank, toe to top, >= min), cap it so that min_gap_outer remains to the next outer line,
#          and build the new geometry of the top lines. Lines of faces listed in widening.never_move, mixed lines and locked lines
#          do not move. A move that would create a new angle sharper than rules.min_angle_deg inside the line is rejected.
# Inputs : work/graph.pkl, work/chains.pkl, work/cltab.pkl (centerline step: dict keyed by centerline name, key 'q' = 1 m points);
#          original boundary layer; locked lines (cfg.locked_lines()); config: widening.*, face_classes.{fixed,editable,default},
#          rules.min_angle_deg, params.widen.{cltab_alias,ray_range,station_radius,min_shift,oblique_cos}.
# Outputs: work/widen.pkl = dict(bmove, bgeo, endT, newf, ST, sL, sR, PTS, SH, DN, rejected); read by apply_widen.py. Diagnostics on stdout.
#          ST = (names, D): names are config centerline names; D columns i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/widen.py [-c rcs_config.json]
# Convention: n = left normal of the centerline; L = positive-t side (left), R = negative-t side; distances in m from the centerline.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, collections, numpy as np, shapely, geopandas as gpd
from shapely.geometry import LineString, Point
from scipy.spatial import cKDTree

args = common.parser('widen the top-of-bank lines to the configured widths').parse_args()
cfg = common.load(args)
WZ = cfg.get('widening')
if not WZ:
    raise SystemExit("config error: section 'widening' is missing (see config_fragments/widen.json)")
if not WZ.get('enabled', False):
    print('widening.enabled is false: nothing to do'); sys.exit(0)
P = cfg.get('params', {}).get('widen', {})
RAY = P.get('ray_range', 1500.0)          # m, half length of the normal
STATION_R = P.get('station_radius', 3.0)  # m, max distance of a top station from a vertex to apply its shift
MIN_SHIFT = P.get('min_shift', 1e-3)      # m, smaller shifts are ignored
OBLIQUE = P.get('oblique_cos', 0.5)       # forced vertices move along the incident line if cos(angle with normal) > this
ALIAS = P.get('cltab_alias', {})          # config centerline name -> key in cltab.pkl (for tables written with other keys)
for k in ('zones', 'min_gap_outer', 'simplify', 'merge'):
    if k not in WZ:
        raise SystemExit(f"config error: widening.{k} is missing")
ZONES = WZ['zones']; GAP = WZ['min_gap_outer']; SIMPL = WZ['simplify']; MERGE = WZ['merge']; DENS = WZ.get('densify', MERGE)
MIN_ANG = cfg['rules']['min_angle_deg'] if 'min_angle_deg' in cfg.get('rules', {}) else None
if MIN_ANG is None:
    raise SystemExit("config error: rules.min_angle_deg is missing")
FC = cfg['face_classes']
for k in ('fixed', 'editable'):
    if k not in FC:
        raise SystemExit(f"config error: face_classes.{k} is missing")
if 'bank_class' not in WZ:
    raise SystemExit("config error: widening.bank_class is missing")
BANK = WZ['bank_class']; WALLS = WZ.get('wall_classes', [])
NEVER = set(WZ.get('never_move', FC.get('fixed_bank_names', [])))
for z in ZONES:
    if z['mode'] not in ('corridor', 'bank'):
        raise SystemExit(f"config error: widening.zones mode must be 'corridor' or 'bank' ({z['mode']})")
LOCKED = cfg.locked_lines()
CLN = list(dict.fromkeys(z['centerline'] for z in ZONES))      # centerlines used by the zones, in order of first appearance

# zone_of(name, s): the first zone of the centerline whose s range contains the chainage s (s_to null = no upper limit)
def zone_of(name, s):
    for z in ZONES:
        if z['centerline'] == name and z.get('s_from', 0) <= s and (z.get('s_to') is None or s <= z['s_to']): return z
    return None

# C = chains.pkl; T0 = cltab.pkl
faces, rows = geom.load_graph(cfg)
with open(cfg.work('chains.pkl'), 'rb') as f: C = pickle.load(f)
with open(cfg.work('cltab.pkl'), 'rb') as f: T0 = pickle.load(f)
def cl_table(name):
    k = name if name in T0 else ALIAS.get(name)
    if k not in T0:
        raise SystemExit(f"cltab.pkl has no centerline '{name}' (keys {list(T0)}): run the centerline step or set params.widen.cltab_alias")
    return T0[k]
# unpack the chain data (see chains.py): feat fid->xy, S segments, meta (fid,i), L/R face names, Lc/Rc classes, istop flags
feat, S, meta, L, R, Lc, Rc, istop = [C[k] for k in 'feat S meta L R Lc Rc istop'.split()]
# tb = toe segments (fixed classes); tc = top-of-bank segments (fixed + bank + wall classes); to = outer segments (also the other editable classes)
fixed = set(FC['fixed']); topc = fixed | {BANK} | set(WALLS); outc = topc | set(FC['editable'])
tb = geom.boundary_segs(faces, rows, lambda n: cfg.face_class(n) in fixed)
tc = geom.boundary_segs(faces, rows, lambda n: cfg.face_class(n) in topc)
to = geom.boundary_segs(faces, rows, lambda n: cfg.face_class(n) in outc)
Rb, Rc_, Ro = geom.Rays(tb), geom.Rays(tc), geom.Rays(to)
# ST: one row per centerline point and per name
ST = []
for name in CLN:
    # q = centerline points (1 m step, index i = s in m)
    q = cl_table(name)['q']; N = len(q)
    for i in range(N):
        # a,b = neighbours; t = unit tangent; n = left normal
        a = q[max(i - 1, 0)]; b = q[min(i + 1, N - 1)]; t = (b - a) / np.hypot(*(b - a)); n = np.array([-t[1], t[0]])
        # hb/hc/ho = signed hit distances (m) of the normal with toe / top / outer lines
        hb = Rb.hits(q[i], n, RAY); hc = Rc_.hits(q[i], n, RAY); ho = Ro.hits(q[i], n, RAY)
        # skip points where the normal does not cross the toe on both sides
        if not (len(hb) and (hb > 0).any() and (hb < 0).any()): continue
        # tL,tR = centerline-to-toe distances (+side, -side), both positive m
        tL = hb[hb > 0].min(); tR = -hb[hb < 0].max()
        # cL,cR = centerline-to-top-of-bank distances beyond the toe (NaN if none)
        cL = hc[hc > tL - 1e-6].min() if (hc > tL - 1e-6).any() else np.nan; cR = -hc[hc < -tR + 1e-6].max() if (hc < -tR + 1e-6).any() else np.nan
        # W = distance between the two top lines (m)
        W = cL + cR if np.isfinite(cL + cR) else np.nan
        # oL,oR = distance to the next outer line beyond the top; NaN if none
        oL = ho[ho > cL + 1e-6].min() if np.isfinite(cL) and (ho > cL + 1e-6).any() else np.nan; oR = -ho[ho < -cR - 1e-6].max() if np.isfinite(cR) and (ho < -cR - 1e-6).any() else np.nan
        # row: (name, i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR)
        ST.append((name, i, q[i][0], q[i][1], n[0], n[1], tL, tR, cL, cR, W, oL, oR))
# D = numeric columns as float array; nm = names
D = np.array([s[1:] for s in ST], float); nm = np.array([s[0] for s in ST])
# unpack columns (ix = index i = s in m)
ix, x, y, nxx, nyy, tL, tR, cL, cR, W, oL, oR = D.T
# rule(...) -> (shift left, shift right) in m, the outward displacement of the top line, from the zone of the point
def rule(name, i, W, tL, tR, cL, cR):
    z = zone_of(name, i)
    if z is None: return 0, 0
    # bank mode: bank width (toe to top) brought to min, per side
    if z['mode'] == 'bank':
        return max(0, z['min'] - (cL - tL)), max(0, z['min'] - (cR - tR))
    # no valid width: no shift
    if not np.isfinite(W): return 0, 0
    # corridor mode: width W brought to min (symmetric shift)
    s = max(0, (z['min'] - W) / 2); return s, s
# sL,sR = shift per point; computed only where both top distances are finite
sL = np.zeros(len(D)); sR = np.zeros(len(D))
for j, (n0, i, w, a, b, c, d) in enumerate(zip(nm, ix, W, tL, tR, cL, cR)):
    if not np.isfinite(c + d): continue
    sL[j], sR[j] = rule(n0, i, w, a, b, c, d)
# outward clearance: keep >= GAP to the next line; okL/okR = gap between top line and next outer line (1e9 m if none)
okL = np.nan_to_num(oL - cL, nan=1e9); okR = np.nan_to_num(oR - cR, nan=1e9)
# cap: never shift more than (gap - GAP), so that at least GAP remains to the next line
capL = np.minimum(sL, np.maximum(okL - GAP, 0)); capR = np.minimum(sR, np.maximum(okR - GAP, 0))
print('clamped by clearance L/R', int((capL < sL - 1e-6).sum()), int((capR < sR - 1e-6).sum()))
sL, sR = capL, capR
# statistics per centerline and per zone: fraction of points widened on L/R and maximum shifts
for n0 in CLN:
    m = nm == n0
    if m.any(): print(n0, 'widen frac L,R', round(float((sL[m] > 0).mean()), 3), round(float((sR[m] > 0).mean()), 3), 'max', round(float(sL[m].max()), 2), round(float(sR[m].max()), 2))
for k, z in enumerate(ZONES):
    m = np.array([zone_of(n0, i) is z for n0, i in zip(nm, ix)], bool)
    if m.any():
        print(f"zone {k} {z['centerline']} {z['mode']} min {z['min']}: widened frac L,R", round(float((sL[m] > 0).mean()), 3), round(float((sR[m] > 0).mean()), 3),
              'km', round(float((sL[m] > 0).sum() / 1000), 2), round(float((sR[m] > 0).sum() / 1000), 2), 'max', round(float(sL[m].max()), 2), round(float(sR[m].max()), 2))
# station points on top line: TL/TR = top-of-bank points on the left/right at each centerline point (centre + n*cL, centre - n*cR)
TL = np.c_[x + nxx * cL, y + nyy * cL]; TR = np.c_[x - nxx * cR, y - nyy * cR]
vL = np.isfinite(cL); vR = np.isfinite(cR)
# PTS = all top stations (valid ones), SH = their shifts (m), DN = unit outward directions (left: +n, right: -n)
PTS = np.vstack([TL[vL], TR[vR]]); SH = np.r_[sL[vL], sR[vR]]; DN = np.vstack([np.c_[nxx, nyy][vL], -np.c_[nxx, nyy][vR]])
# kd = KD-tree of PTS; used to find the shift applicable to any vertex of a top line (within STATION_R)
kd = cKDTree(PTS)
# shift_at(P): shift (m) and outward direction at point P from the nearest top station; (0,None) if none within STATION_R
def shift_at(Pt):
    d, j = kd.query(Pt)
    if d > STATION_R: return 0.0, None
    return SH[j], DN[j]
# top features: fid -> indices of their top segments; locked features are never moved
topfid = collections.defaultdict(set)
for (fid, i), t in zip(meta, istop):
    if t: topfid[fid].add(i)
ALL = {f for f in topfid if f not in LOCKED}
print('top feats total', len(topfid), 'locked (not moved)', len(set(topfid) & LOCKED))
# newf: fid -> new vertex array; changed = counter; bmove: tag -> new position of a forced point
newf = {}; changed = 0; bmove = {}; rejected = []
# forced vertices: ends of other lines lying on a top line (interior T)
keys = list(feat); LS = [LineString(feat[k]) for k in keys]; TT = shapely.STRtree(LS)
# forced[f2]: list of (original point, unit direction of the incident line towards the point, tag ('bl',fid,end))
forced = collections.defaultdict(list)
for k, a in feat.items():
    if not len(a): continue
    for e in (0, -1):
        idx = TT.query(Point(a[e]), predicate='dwithin', distance=1e-3)
        for i in idx:
            f2 = keys[i]
            if f2 == k or f2 not in ALL: continue
            b = feat[f2]
            # ignore if the end of k coincides with an end of f2 (a plain end-to-end junction, not a T)
            if min(np.hypot(*(b[0] - a[e])), np.hypot(*(b[-1] - a[e]))) < 1e-3: continue
            # u = direction of the incident line at its end
            u = a[e] - a[1 if e == 0 else -2]; u = u / np.hypot(*u); forced[f2].append((a[e].copy(), u, ('bl', k, e)))
# same for boundary lines (bgeo: boundary fid -> vertices); tag ('bd',k,e)
bdf = gpd.read_file(cfg.layer('in', 'boundary'), fid_as_index=True); bgeo = {}; bname = cfg.f('boundary', 'name')
for k, g in bdf.geometry.items():
    a = shapely.get_coordinates(next(iter(shapely.get_parts(g)))); bgeo[k] = a
    for e in (0, -1):
        idx = TT.query(Point(a[e]), predicate='dwithin', distance=1e-3)
        # chains = top features touched by the boundary end; others = other breaklines ending at the same point
        chains = [keys[i] for i in idx if keys[i] in ALL]
        others = [keys[i] for i in idx if keys[i] not in ALL and min(np.hypot(*(feat[keys[i]][0] - a[e])), np.hypot(*(feat[keys[i]][-1] - a[e]))) < 1e-3]
        if not chains: continue
        # boundary end shared with another (non-top) breakline: left as is
        if others: print('  boundary end coincident w breakline: left as is', bdf[bname][k], e, others[:2]); continue
        f2 = chains[0]; b = feat[f2]
        if min(np.hypot(*(b[0] - a[e])), np.hypot(*(b[-1] - a[e]))) < 1e-3:
            print('  boundary end at chain vertex', bdf[bname][k], e)
        u = a[e] - a[1 if e == 0 else -2]; u = u / np.hypot(*u); forced[f2].append((a[e].copy(), u, ('bd', k, e)))
print('forced T points', sum(len(v) for v in forced.values()))
endT = {}
mseg = np.array([m[0] for m in meta])
# main loop: build the new geometry of each top feature
for fid in ALL:
    a = feat[fid]; idx = topfid[fid]
    # exclude features that touch a never-move face (region name or class)
    sel = np.where(mseg == fid)[0]
    labs = set(L[sel]) | set(R[sel]) | set(Lc[sel]) | set(Rc[sel])
    if labs & NEVER: continue
    # mixed features (only some segments are top): not moved, reported
    if len(idx) != sum(np.hypot(*(a[i + 1] - a[i])) > 1e-6 for i in range(len(a) - 1)):
        print('mixed skip', fid); continue
    # densify: s = chainages every DENS m, the end, all original vertices and the forced points; Pp = the points
    l = LineString(a); fp = [l.project(Point(p[0])) for p in forced.get(fid, [])]
    s = np.unique(np.r_[np.arange(0, l.length, DENS), [l.length], [l.project(Point(p)) for p in a], fp]); Pp = shapely.get_coordinates(shapely.line_interpolate_point(l, s))
    # out = displaced points
    out = []; moved = False
    for p in Pp:
        # shifted by the local widening if > MIN_SHIFT
        sh, n = shift_at(p)
        if sh > MIN_SHIFT: out.append(p + n * sh); moved = True
        else: out.append(p)
    # feature not touched by widening: keep the original
    if not moved: continue
    out = np.array(out)
    # forced vertices: move along the incident line direction u so that the T junction stays on the incident line (u/c, c=cos angle with n); if too oblique (c<=OBLIQUE) move along n
    for v, (orig, u, tag) in zip(fp, forced.get(fid, [])):
        i = int(np.argmin(np.abs(s - v))); sh, n = shift_at(Pp[i])
        if sh > MIN_SHIFT:
            c = float(u @ n); out[i] = (Pp[i] + u * sh / c) if c > OBLIQUE else (Pp[i] + n * sh)
    # isf[i] = point is a forced vertex
    isf = np.zeros(len(s), bool)
    for v in fp: isf[int(np.argmin(np.abs(s - v)))] = True
    # split into parts at the forced vertices, simplify each then thin vertices closer than MERGE m, so that the forced vertices are retained
    cuts = [0] + [i for i in np.where(isf)[0] if 0 < i < len(s) - 1] + [len(s) - 1]
    res = []
    for c0, c1 in zip(cuts[:-1], cuts[1:]):
        part = shapely.get_coordinates(LineString(out[c0:c1 + 1]).simplify(SIMPL, preserve_topology=False))
        keep = [0]
        for i in range(1, len(part) - 1):
            if np.hypot(*(part[i] - part[keep[-1]])) >= MERGE: keep.append(i)
        keep.append(len(part) - 1); part = part[keep]
        # join the parts without duplicating the shared vertex
        res.append(part if not res else part[1:])
    # b = new vertex array
    b = np.vstack(res)
    # angle rule: the moved line must not get a new acute angle inside it (more acute vertices than before, or a sharper one)
    ao = [v for _, v in geom.vertex_angles(a)]; an = [v for _, v in geom.vertex_angles(b)]
    no = sum(v < MIN_ANG for v in ao); nn = sum(v < MIN_ANG for v in an)
    if nn > no or (nn > 0 and min(an) < min(ao + [180.]) - 1e-6):
        rejected.append((fid, round(float(min(an)), 1))); print('angle rule: move of', fid, 'rejected (min angle', round(float(min(an)), 1), 'deg)'); continue
    newf[fid] = b; changed += 1
    # record where each forced point went: endT keyed by original xy rounded to mm; bmove keyed by tag
    for v, (orig, u, tag) in zip(fp, forced.get(fid, [])):
        i = int(np.argmin(np.abs(s - v))); endT[(round(orig[0], 3), round(orig[1], 3))] = out[i].copy(); bmove[tag] = out[i].copy()
print('changed top features', changed)
print('moves rejected by the angle rule', len(rejected), [r[0] for r in rejected])
# save: bmove (tag->new xy), bgeo (original boundary vertices), endT, newf (fid->new xy), ST=(names,D), sL/sR shifts, PTS/SH/DN top stations
with open(cfg.work('widen.pkl'), 'wb') as f:
    pickle.dump(dict(bmove=bmove, bgeo=bgeo, endT=endT, newf=newf, ST=(nm, D), sL=sL, sR=sR, PTS=PTS, SH=SH, DN=DN, rejected=rejected), f)
print('OK widen.pkl written')
