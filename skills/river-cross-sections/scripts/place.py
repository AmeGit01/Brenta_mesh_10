# place.py - candidate section positions along the centerlines and their evaluation (input of dp.py)
# Purpose: generate a candidate section every params.placement.candidate_step metres along every centerline used by a reach and
#          evaluate each one: distances to the toe and to the top of bank on both sides, near-node violations on the toe crossings,
#          crossings with nodestrings and with inner breaklines, and crossing angles sharper than rules.min_angle_deg.
#          The stations are chosen later by dp.py. The faces of the (widened) planar graph are also saved.
# Inputs : work/cltab.pkl (cl2.py: dict centerline name -> dict with q = centerline at 1 m step); the original breaklines, boundary and
#          regions layers (cfg 'in'); work/widen2.pkl and work/bgn.pkl (apply_widen.py; optional: without them the original lines
#          are used, i.e. widening disabled); work/xn_points.json (xn_points.py; needed when params.placement.weights.xn > 0).
#          Config: centerlines[*].name, reaches[*].source, rules.near_node {radius, ignore_below}, rules.min_angle_deg,
#          params.placement {toe_classes, top_classes, candidate_step, ray_range, tangent_half, extent_beyond_toe, extent_inside_top,
#          wide_section, min_beyond_toe, angle_penalty, perp_window, weights.xn}.
# Outputs: work/cands.pkl = dict centerline name -> dict of arrays aligned per candidate (see below); work/newfaces.pkl = dict(fc, rows)
#          (faces of the widened planar graph and one row {face, nome} per face that holds a region point); diagnostics on stdout.
#          cands[name] keys: ss (s in m), P (x,y on the centerline), n (left unit normal), tL,tR (centerline -> toe, + and - side, m),
#          cL,cR (centerline -> top of bank, m), eL,eR (half-extent of the approximate section on each side, m),
#          pen_near (0..2: toe crossings closer than the near-node radius to a toe vertex), pen_xn (0..2: toe crossings closer than that
#          radius to a meeting point of nodestring and breakline), pen_angle (crossings with a line at an angle < rules.min_angle_deg),
#          perp_dev (deviation in degrees of the section normal from the normal of the longer chord), hitB (1 if the approximate
#          section crosses a nodestring), hitO (1 if it crosses an inner breakline), ok (toe and top found on both sides).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/place.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, json, numpy as np, shapely, geopandas as gpd, warnings
from shapely.geometry import LineString
from shapely.ops import unary_union, polygonize
from scipy.spatial import cKDTree
warnings.filterwarnings('ignore')

cfg = common.load(common.parser('candidate section positions along the centerlines and their evaluation').parse_args())
PR = cfg.get('params', {}).get('placement')
if PR is None:
    raise SystemExit("config error: params.placement is missing (see config_fragments/placement.json)")
RN = cfg['rules']['near_node']; R_NEAR, R_IGN = RN['radius'], RN['ignore_below']
MIN_ANG = cfg['rules']['min_angle_deg']
GR, RAY = PR['candidate_step'], PR['ray_range']
W_XN = PR['weights']['xn']
# centerlines used by the reaches, in the order of first use
names = []
for rc in cfg.reaches():
    if 'source' not in rc:
        raise SystemExit(f"config error: reaches[{rc['code']}].source is missing (name of the centerline the reach follows)")
    if rc['source'] not in names: names.append(rc['source'])
with open(cfg.work('cltab.pkl'), 'rb') as f: T0 = pickle.load(f)
miss = [n for n in names if n not in T0]
if miss:
    raise SystemExit(f"work/cltab.pkl has no centerline {miss}: run cl.py and cl2.py with the same config (centerlines[*].name)")

# ---- geometry of the widened planar graph: breaklines (feat: fid -> vertices, newf: moved ones), boundary lines (bgeo)
bl = gpd.read_file(cfg.layer('in', 'breaklines'), fid_as_index=True); bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
feat = {fid: shapely.get_coordinates(next(iter(shapely.get_parts(g)))) for fid, g in bl.geometry.items()}
wp, bp_ = cfg.work('widen2.pkl'), cfg.work('bgn.pkl')
if os.path.exists(wp) and os.path.exists(bp_):
    with open(wp, 'rb') as f: newf = pickle.load(f)['newf']
    with open(bp_, 'rb') as f: bgn = pickle.load(f)
    print('widened lines: breaklines', len(newf), 'boundaries', len(bgn))
elif cfg.get('widening', {}).get('enabled', False):
    raise SystemExit('widening is enabled in the config but work/widen2.pkl or work/bgn.pkl is missing: run widen.py and apply_widen.py')
else:
    newf, bgn = {}, {}; print('widening disabled: original breaklines and boundaries')
bdf = gpd.read_file(cfg.layer('in', 'boundary'), fid_as_index=True)
rg = gpd.read_file(cfg.layer('in', 'regions'), fid_as_index=True)
fN = cfg.f('regions', 'name')
# bgeo: boundary fid -> vertices (new if changed in bgn, else original); sections (if any) are not obstacles
bgeo = {k: bgn.get(k, shapely.get_coordinates(next(iter(shapely.get_parts(g))))) for k, g in bdf.geometry.items()
        if not cfg.is_section(bdf.loc[k, cfg.f('boundary', 'name')])}
# all lines -> planar graph faces carrying the region names
L = [LineString(newf.get(f, a)) for f, a in feat.items()] + [LineString(a) for a in bgeo.values()]
u = unary_union(L); fc = list(polygonize(u)); t = shapely.STRtree(fc); ix = t.query(rg.geometry.values, predicate='within')
# rows: one per face containing region points; later points on the same face are discarded (the first one gives the name)
rows = [dict(face=int(f), nome=rg[fN].iloc[int(p)]) for p, f in zip(*ix)]
seen = set(); rows = [x for x in rows if not (x['face'] in seen or seen.add(x['face']))]; print('faces', len(fc), 'named', len(rows))
with open(cfg.work('newfaces.pkl'), 'wb') as f: pickle.dump(dict(fc=fc, rows=rows), f)

# tb = toe segments, tc = top segments of the new graph; ray objects Rb/Rc
toe_c, top_c = set(PR['toe_classes']), set(PR['top_classes'])
tb = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in toe_c)
tc = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in top_c)
Rb, Rc = geom.Rays(tb), geom.Rays(tc)
tb_keys = {geom.key(s) for s in tb}
# vtx: vertices of every breakline that contains at least one toe segment; vk = KD-tree (near-node rule on the toe crossings)
vtx = []
for f, a in feat.items():
    a2 = newf.get(f, a); S = np.c_[a2[:-1], a2[1:]]
    if any(geom.key(s) in tb_keys for s in S): vtx.append(a2)
vtx = np.vstack(vtx); vk = cKDTree(vtx); print('toe vertices', len(vtx))
# obstacles: nodestrings (OT) and single segments of breaklines that are neither toe nor top (OTB: cross lines, buildings)
OT = shapely.STRtree([LineString(a) for a in bgeo.values()])
tops = {geom.key(s) for s in tc}
OT2 = []
for f, a in feat.items():
    a2 = newf.get(f, a)
    for s in np.c_[a2[:-1], a2[1:]]:
        k = geom.key(s)
        if k not in tb_keys and k not in tops: OT2.append(LineString(s.reshape(2, 2)))
OTB = shapely.STRtree(OT2); print('obstacles: boundary', len(bgeo), 'inner bl', len(OT2))
# all single segments of all lines with their directions (crossing-angle rule)
ASEG = []
for f, a in feat.items():
    a2 = newf.get(f, a); ASEG += [s for s in np.c_[a2[:-1], a2[1:]] if np.hypot(*(s[2:] - s[:2])) > 1e-9]
for a in bgeo.values(): ASEG += [s for s in np.c_[a[:-1], a[1:]] if np.hypot(*(s[2:] - s[:2])) > 1e-9]
ASEG = np.array(ASEG); ADIR = ASEG[:, 2:] - ASEG[:, :2]; ADIR /= np.hypot(*ADIR.T)[:, None]
AT = shapely.STRtree(shapely.linestrings(ASEG.reshape(-1, 2, 2)))
# xn points (meeting points of nodestrings and breaklines)
kx = None
if W_XN > 0:
    xp = cfg.work('xn_points.json')
    if not os.path.exists(xp): raise SystemExit(f'missing {xp}: run xn_points.py (or set params.placement.weights.xn to 0)')
    with open(xp) as f: XN = np.array(json.load(f))
    kx = cKDTree(XN) if len(XN) else None


def cand(q, step=GR):
    """Chainages ss, points P and left normals n of the candidates; the normal is perpendicular to the chord between s-h and s+h."""
    l = LineString(q); ss = np.arange(0, l.length, step); P = shapely.get_coordinates(shapely.line_interpolate_point(l, ss))
    h = PR['tangent_half']
    def nrm(h):
        A = shapely.get_coordinates(shapely.line_interpolate_point(l, np.maximum(ss - h, 0)))
        B = shapely.get_coordinates(shapely.line_interpolate_point(l, np.minimum(ss + h, l.length)))
        d = (B - A) / np.hypot(*(B - A).T)[:, None]; return np.c_[-d[:, 1], d[:, 0]]
    n = nrm(h)
    # perp_dev: angle between this normal and the normal of the longer chord (perpendicularity of the section to the local course)
    nw = nrm(PR['perp_window']); dev = np.degrees(np.arccos(np.clip((n * nw).sum(1), -1, 1)))
    return ss, P, n, dev


def eval_cand(ss, P, n):
    """For each candidate the distances to the toe (tL,tR) and to the first top line beyond the toe (cL,cR) on each side,
    from ray hits within +-ray_range; NaN if absent."""
    N = len(ss); res = np.full((N, 4), np.nan)
    for i in range(N):
        hb = Rb.hits(P[i], n[i], RAY); hc = Rc.hits(P[i], n[i], RAY)
        if len(hb) == 0 or not (hb > 0).any() or not (hb < 0).any(): continue
        tL = hb[hb > 0].min(); tR = -hb[hb < 0].max()
        cc1 = hc[hc > tL - 1e-6]; cc2 = hc[hc < -tR + 1e-6]
        if not len(cc1) or not len(cc2): continue
        res[i] = [tL, tR, cc1.min(), -cc2.max()]
    return res


out = {}
EB, EI, WIDE, MINB = PR['extent_beyond_toe'], PR['extent_inside_top'], PR['wide_section'], PR['min_beyond_toe']
for name in names:
    q = T0[name]['q']; ss, P, n, perp = cand(q); res = eval_cand(ss, P, n)
    tL, tR, cL, cR = res.T; ok = np.isfinite(tL)
    # near-node rule on the 2 toe crossings: d = distances to the 2 nearest toe vertices; violation if the crossing is closer than the
    # radius to a vertex (if a vertex coincides with it, d <= ignore_below, the next vertex is used); pen_near = number of sides (0..2)
    pen_near = np.zeros(len(ss)); pen_xn = np.zeros(len(ss))
    for sgn, tt in ((1, tL), (-1, tR)):
        p = P + n * (sgn * tt[:, None]); m = np.isfinite(p[:, 0])
        d, _ = vk.query(p[m], k=2)
        v = ((d[:, 0] > R_IGN) & (d[:, 0] < R_NEAR)) | ((d[:, 0] <= R_IGN) & (d[:, 1] < R_NEAR))
        a = np.zeros(len(ss)); a[m] = v.astype(float); pen_near += a
        if kx is not None:
            dd, _ = kx.query(p[m]); a = np.zeros(len(ss)); a[m] = (dd < R_NEAR).astype(float); pen_xn += a
    # approximate section extent: toe + extent_beyond_toe but not beyond extent_inside_top inside the top line. When the section is
    # wide (> wide_section) use it; otherwise at least toe + min_beyond_toe (or top - extent_inside_top if larger).
    # Note: eL tests tL+cR > wide, eR tests tL+tR > wide (asymmetric as in the Brenta original)
    ext = lambda c, t: np.minimum(t + EB, c - EI)
    eL = np.where(tL + cR > WIDE, ext(cL, tL), np.minimum(ext(cL, tL), np.maximum(tL + MINB, cL - EI)))
    eR = np.where(tL + tR > WIDE, ext(cR, tR), np.minimum(ext(cR, tR), np.maximum(tR + MINB, cR - EI)))
    ln = shapely.linestrings(np.stack([P + n * np.nan_to_num(eL, nan=0)[:, None], P - n * np.nan_to_num(eR, nan=0)[:, None]], axis=1))
    i0, _ = OT.query(ln, predicate='intersects'); hitB = np.zeros(len(ss)); hitB[np.unique(i0)] = 1
    j0, _ = OTB.query(ln, predicate='intersects'); hitO = np.zeros(len(ss)); hitO[np.unique(j0)] = 1
    # crossing angle rule: crossings of the approximate section with any line (toe, top, inner, nodestring) sharper than min_angle_deg
    pen_angle = np.zeros(len(ss))
    if PR['angle_penalty']:
        ii, jj = AT.query(ln[ok], predicate='intersects'); ii = np.where(ok)[0][ii]
        ang = np.degrees(np.arccos(np.clip(np.abs((n[ii] * ADIR[jj]).sum(1)), 0, 1)))
        np.add.at(pen_angle, ii[ang < MIN_ANG], 1)
    print(name, 'cands', len(ss), 'valid', int(ok.sum()), 'hit bd', int(hitB[ok].sum()), 'hit inner', int(hitO[ok].sum()),
          'near-node>0', int((pen_near[ok] > 0).sum()), 'xn>0', int((pen_xn[ok] > 0).sum()),
          f'angle<{MIN_ANG:g}>0', int((pen_angle[ok] > 0).sum()))
    out[name] = dict(ss=ss, P=P, n=n, tL=tL, tR=tR, cL=cL, cR=cR, eL=eL, eR=eR, pen_near=pen_near, pen_xn=pen_xn, pen_angle=pen_angle,
                     perp_dev=perp, hitB=hitB, hitO=hitO, ok=ok)
with open(cfg.work('cands.pkl'), 'wb') as f: pickle.dump(out, f)
