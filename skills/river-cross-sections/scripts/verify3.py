# verify3.py - independent checks of all attributes and geometries of the derived section layers, read back from disk.
# Purpose: after the sections, centerpoints and bankpoints are built, check everything again with code that does not share logic with
#          the writers. Each check prints 'OK' or '**CHECK**' with the offending items.
#          Groups: (A) boundary: counts, names, ids, section geometry; (B) centerline; (C) centerpoints; (D) bankpoints;
#          (E) spacing and the near-node rule compared with the exception lists; (F) crossings; (G) region points (one per face, attributes,
#          originals, clearance); (H) GeoPackage integrity; (I) angle rule.
# Inputs : config keys: outputs.* (the six derived layers), inputs.regions/breaklines/boundary (originals), fields.*, bankpoint_values,
#          sections.* (name_pattern, digits, spacing, tol, first_fid, first_id), reaches[*] (code, first_number, chainage),
#          nodestrings.count, exceptions.* (via cfg.exc_near_node/exc_wall/exc_spacing), locked.* (via cfg.locked_lines(): work/<lines_file>),
#          originals.*, rules.near_node.radius, rules.min_angle_deg, exceptions.angle (check (I), see check_angles.py), rules.regions.clearance, project.crs,
#          params.verify3 {kinds, kind_max, kind_wall, prom_min, notes{multi,null,moved}}; for reaches with chainage mode
#          'cut_reference': the reference GeoPackage named in the config.
# Outputs: print only.
# Run    : cd <working folder>; ~/anaconda3/bin/python3 <toolkit>/scripts/verify3.py [-c rcs_config.json]   (geo interpreter; read-only)
# Origin : Brenta project, verify3.py, 2026-11-18 (exceptions updated 2026-11-19).
import sys, os, sqlite3, re, json, numpy as np, geopandas as gpd, shapely, warnings, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union
from scipy.spatial import cKDTree

cfg = common.load(common.parser('independent verification of the derived section layers').parse_args())
P3 = cfg['params']['verify3']
SC = cfg['sections']; REACHES = cfg.reaches(); CODES = [r['code'] for r in REACHES]
SP = SC['spacing']; TOL = SC['tol']; STEP = int(round(SP))
BV = cfg['bankpoint_values']; LEFT, RIGHT, MANUAL, NSTR = BV['left'], BV['right'], BV['manual'], BV['nodestring']
KINDS = set(P3['kinds']); KMAX, KWALL, PROM_MIN = P3['kind_max'], P3['kind_wall'], P3['prom_min']
NOTE = P3.get('notes', {})
R5 = cfg['rules']['near_node']['radius']; CLEAR = cfg['rules']['regions']['clearance']
O = cfg['originals']; FMAX = O['region_fid_max']; REPL = sorted(O['region_fids_replaced']); DELE = set(O['region_fids_deleted'])
MATS = cfg['locked']['mat_ids']


def rd(which, key, path=None):
    """GeoDataFrame indexed by fid, columns renamed to the LOGICAL field names of the layer."""
    df = gpd.read_file(path or cfg.layer(which, key), fid_as_index=True)
    return df.rename(columns={cfg.f(key, l): l for l in cfg['fields'][key]})


bl, bd, rg, cp, bp, cl = (rd('out', k) for k in ('breaklines', 'boundary', 'regions', 'centerpoints', 'bankpoints', 'centerline'))
rg0 = rd('in', 'regions')
EXCN = cfg.exc_near_node(); EXCW = cfg.exc_wall(); EXCD = cfg.exc_spacing(); LOCK = cfg.locked_lines()
# reference lines (chainage mode cut_reference): one reference geometry per reach
REF = {}
for r in REACHES:
    ch = r['chainage']
    if ch['mode'] == 'cut_reference':
        rf = rd('out', 'centerline', cfg.path(ch['reference_file']))
        REF[r['code']] = rf[rf['name'] == ch['reference_line']].geometry.iloc[0]
co = lambda g: shapely.get_coordinates(g)
k = 0
def out(msg, ok=None):
    global k; k += 1; print(f'{k}. {msg}' + ('' if ok is None else ('  OK' if ok else '  **CHECK**')))
issec = cfg.is_section
sec = bd[[issec(n) for n in bd['name']]]; oth = bd[[not issec(n) for n in bd['name']]]
# ---- (A) boundary
out(f'counts: breaklines {len(bl)}, boundary {len(bd)} ({len(oth)} nodestrings + {len(sec)} sections), regioni {len(rg)}, centerpoints {len(cp)}, bankpoints {len(bp)}, centerline {len(cl)}',
    len(oth) == cfg['nodestrings']['count'] and len(sec) == len(cp) and len(bp) == 2 * len(sec) and len(cl) == len(REACHES))
ok = True; order = []
for r in REACHES:
    n = [x for x in sec['name'] if cfg.reach_of(x) == r['code']]; v = [int(x[len(r['code']):]) for x in n]
    st = r['first_number']; ok &= v == list(range(st, st + STEP * len(v), STEP)); order += n
out(f'section names: per reach consecutive multiples of {STEP}, in reach order {", ".join(CODES)}, unique', ok and list(sec['name']) == order and sec['name'].is_unique)
F0, I0 = SC['first_fid'], SC['first_id']; ns = len(sec)
out(f'boundary: names unique {bd["name"].is_unique}, ids unique {bd["id"].is_unique}, no null id/name {bool(bd["id"].notna().all() and bd["name"].notna().all())}; section fid {F0}.. and id {I0}.. consecutive {list(sec.index) == list(range(F0, F0 + ns)) and list(sec["id"]) == list(range(I0, I0 + ns))}',
    bd['name'].is_unique and bd['id'].is_unique and list(sec.index) == list(range(F0, F0 + ns)) and list(sec['id']) == list(range(I0, I0 + ns)))
gt = set(sec.geometry.geom_type); np_ = [n for n, g in zip(sec['name'], sec.geometry) if len(g.geoms) != 1 or len(co(g)) != 2]
zm = [n for n, g in zip(sec['name'], sec.geometry) if np.abs(shapely.get_coordinates(g, include_z=True)[:, 2]).max() > 0]
out(f'sections: geometry types {gt}, not one part with 2 vertices {np_}, z not 0 {zm}', not np_ and not zm)
# ---- (B) centerline
line = {r.reach: r.geometry for r in cl.itertuples()}; lm = [(r.name, round(r.length - r.geometry.length, 6)) for r in cl.itertuples() if abs(r.length - r.geometry.length) > 1e-6]
out(f'centerline: ramo {sorted(line)}, lung_m = geometry length (differences {lm})', sorted(line) == sorted(CODES) and not lm)
# base[code] = line on which the chainage of the reach is measured; s0[code] = chainage of the reach start on that line
base = {}; s0v = {}; b0 = {}; okcl = True; parts = []
for r in REACHES:
    c = r['code']; ch = r['chainage']
    if ch['mode'] == 'cut_reference':
        b0[c] = LineString(co(sec[sec['name'] == ch['origin_section']].geometry.iloc[0])); xb = b0[c].intersection(REF[c]); s0 = cl[cl.reach == c].s0.iloc[0]
        base[c] = REF[c]; s0v[c] = s0
        parts.append((f"centerline {c}: s0_asta {s0:.3f} = chainage of {ch['origin_section']} on the asta {REF[c].project(xb):.3f}; starts on {ch['origin_section']} ({Point(co(line[c])[0]).distance(b0[c]):.2e} m)"))
        okcl &= abs(s0 - REF[c].project(xb)) < 1e-6 and Point(co(line[c])[0]).distance(b0[c]) < 1e-6
    else:
        base[c] = line[c]; s0v[c] = 0.0
        v = cl[cl.reach == c].s0.iloc[0]
        parts.append(f'{c} s0_asta null {bool(cl[cl.reach == c].s0.isna().iloc[0])}' if v != v else f'{c} s0_asta {v}')
isref = [r['chainage']['mode'] == 'cut_reference' for r in REACHES]
out('; '.join([p for p, f in zip(parts, isref) if f] + [', '.join(p for p, f in zip(parts, isref) if not f)]), okcl)
# ---- (C) centerpoints
C = {r.name: r for r in cp.itertuples()}; bad = []
for nm, g in zip(sec['name'], sec.geometry):
    if nm not in C: bad.append((nm, 'missing')); continue
    c = C[nm]; l = LineString(co(g)); p = c.geometry; rc = cfg.reach_of(nm); bs = base[rc]; sB = s0v[rc]
    if c.reach != rc: bad.append((nm, 'stream', c.reach))
    if l.distance(p) > 1e-6: bad.append((nm, 'not on section', l.distance(p)))
    if line[rc].distance(p) > 1e-6 and bs.distance(p) > 1e-6: bad.append((nm, 'not on centerline'))
    if abs(bs.project(p) - sB - c.s) > 1e-3: bad.append((nm, 's_m', c.s, bs.project(p) - sB))
out(f'centerpoints: one per section, same name, stream = reach letter, on the section and on the centerline, s_m = chainage within the reach: problems {bad}', not bad and set(C) == set(sec['name']))
dn = []
for i, n in enumerate(order):
    nx = order[i + 1] if i + 1 < len(order) and cfg.reach_of(order[i + 1]) == cfg.reach_of(n) else None; v = C[n].dist_next
    if nx is None:
        if v == v and v is not None: dn.append((n, 'last has dist_next', v))
    elif abs(v - (C[nx].s - C[n].s)) > 1e-6: dn.append((n, v, C[nx].s - C[n].s))
firsts = [cfg.section_name(r['code'], r['first_number']) for r in REACHES]
origin_ok = all(C[r['chainage']['origin_section']].s == 0 for r in REACHES if r['chainage']['mode'] == 'cut_reference')
out(f'centerpoints: dist_next = s_m(next) - s_m, null for the last of each reach (problems {dn}); s_m starts {"/".join(f"{C[n].s:.2f}" for n in firsts)}', not dn and origin_ok)
# ---- (D) bankpoints
B = {r.name: r for r in bp.itertuples()}; bad = []
NSg = {n: co(g) for n, g in zip(oth['name'], oth.geometry)}
for nm, g in zip(sec['name'], sec.geometry):
    v = co(g)
    for t, p in ((LEFT, v[0]), (RIGHT, v[-1])):
        q = B.get(f'{nm}_{t}')
        if q is None: bad.append((nm, t, 'missing')); continue
        if q.section != nm: bad.append((q.name, 'sezione', q.section))
        if not np.array_equal(co(q.geometry)[0], p): bad.append((q.name, 'not = section vertex'))
        if abs(q.s - C[nm].s) > 1e-9: bad.append((q.name, 's_m'))
        if abs(q.dist_cp - q.geometry.distance(C[nm].geometry)) > 1e-6: bad.append((q.name, 'dist_cp', q.dist_cp, q.geometry.distance(C[nm].geometry)))
        if q.kind not in KINDS: bad.append((q.name, 'tipo', q.kind))
        if q.z != q.z or q.z is None: bad.append((q.name, 'z null'))
        if q.kind == KMAX and not (q.prom == q.prom and q.prom >= PROM_MIN): bad.append((q.name, f'{KMAX} without prom>={PROM_MIN:g}'))
        if q.kind != KMAX and q.prom == q.prom and q.prom is not None: bad.append((q.name, f'prom on non-{KMAX}', q.kind))
        if q.kind == MANUAL and q.rule != MANUAL: bad.append((q.name, f'{MANUAL} regola', q.rule))
        if q.kind == NSTR and not (q.rule in NSg and any(np.abs(NSg[q.rule] - p).sum(1).min() < 1e-6 for _ in [0])): bad.append((q.name, 'nodestring end', q.rule))
        if q.kind == KWALL and q.rule != KWALL: bad.append((q.name, f'{KWALL} regola'))
out(f'bankpoints: two per section, sezione, = section vertices (sx first), s_m = centerpoint, dist_cp = distance to centerpoint, tipo/regola/prom coherent, z not null: problems {bad}', not bad and len(B) == 2 * len(sec))
# left/right: the left bankpoint must be on the left of the flow direction (local tangent of the centerline)
lr = []
for nm, g in zip(sec['name'], sec.geometry):
    bs = base[cfg.reach_of(nm)]; s = bs.project(C[nm].geometry); p0 = np.array(bs.interpolate(max(s - 1, 0)).coords[0]); p1 = np.array(bs.interpolate(s + 1).coords[0])
    t = p1 - p0; v = co(g)[0] - co(C[nm].geometry)[0]
    if t[0] * v[1] - t[1] * v[0] <= 0: lr.append(nm)
out(f'sections run from the left bank (sx) to the right bank (dx): wrong {lr}', not lr)
cnt = collections.Counter(zip(bp.kind, bp.rule)); out(f'bankpoints by tipo/regola: {dict(cnt)}')
out(f'bankpoints {MANUAL}: ' + str(sorted(n for n, r in B.items() if r.kind == MANUAL)) + f'; {NSTR}: ' + str(sorted(n for n, r in B.items() if r.kind == NSTR)))
# ---- (E) spacing and near-node rule vs exceptions
Pc = {n: co(C[n].geometry)[0] for n in order}; ds = []; ch = []
for a, b in zip(order[:-1], order[1:]):
    if cfg.reach_of(a) != cfg.reach_of(b): continue
    d = C[b].s - C[a].s; c = float(np.hypot(*(Pc[a] - Pc[b])))
    if not SP - TOL - 1e-6 <= d <= SP + TOL + 1e-6: ds.append((a, b, round(d, 3)))
    if not SP - TOL - 1e-6 <= c <= SP + TOL + 1e-6: ch.append((a, b, round(c, 3)))
out(f'spacing along the centerline out of {SP:g}+-{TOL:g} m (tolerance 1e-6 m): {ds}')
out(f'straight distance out of {SP:g}+-{TOL:g} m (tolerance 1e-6 m): {ch}')
out('spacing anomalies are exactly the listed exceptions ' + str(sorted(EXCD)), {(a, b) for a, b, _ in ds + ch} == EXCD)
F = {f: co(g)[:, :2] for f, g in bl.geometry.items() if g is not None and not g.is_empty}; keys = list(F); ln = [LineString(F[f]) for f in keys]; TB = shapely.STRtree(ln)
vt = np.vstack(list(F.values())); kd = cKDTree(vt); viol = []; ncr = 0; nl = collections.Counter(); SL = [LineString(co(g)) for g in sec.geometry]; per = {}
for nm, l in zip(sec['name'], SL):
    on = [i for i in TB.query(l, predicate='intersects') if l.distance(Point(F[keys[i]][0])) < 1e-6 and l.distance(Point(F[keys[i]][-1])) < 1e-6]
    hit = [i for i in TB.query(l, predicate='intersects') if i not in on]; nl[len(hit)] += 1; per[nm] = len(hit)
    Pp = [p for i in hit for p in co(l.intersection(ln[i]))]
    for p in Pp:
        ncr += 1; d = [float(np.hypot(*(vt[j] - p))) for j in kd.query_ball_point(p, R5) if np.hypot(*(vt[j] - p)) > 1e-3 and all(np.hypot(*(vt[j] - q)) > 1e-6 for q in Pp)]
        if d:
            j = min((j for j in kd.query_ball_point(p, R5) if np.hypot(*(vt[j] - p)) > 1e-3 and all(np.hypot(*(vt[j] - q)) > 1e-6 for q in Pp)), key=lambda j: np.hypot(*(vt[j] - p)))
            own = [keys[i] for i in TB.query(Point(vt[j]).buffer(1e-6)) if Point(vt[j]).distance(ln[i]) < 1e-6]
            viol.append((nm, round(min(d), 2), 'wall' if any(o in LOCK for o in own) else 'other', own))
v5 = [v for v in viol if v[0] not in EXCN]
out(f'near-node rule (radius {R5:g} m): {ncr} crossings, {len(viol)} with a breakline vertex in (0,{R5:g}) m; exceptions {sorted(EXCN)}: {[v[:2] for v in viol if v[0] in EXCN]}')
out(f'near-node rule (radius {R5:g} m), vertex on a locked wall line (mat_id {", ".join(map(str, MATS))}, cannot move): {[v[:2] for v in v5 if v[2] == "wall"]}; exactly the wall exceptions {sorted(EXCW)}', {v[0] for v in v5 if v[2] == 'wall'} == EXCW)
out(f'near-node rule (radius {R5:g} m) outside the exceptions, other vertices: {[v[:2] + (v[3],) for v in v5 if v[2] != "wall"]}', not [v for v in v5 if v[2] != 'wall'])
out(f'breaklines crossed per section: {dict(nl)}; sections with != 2: {[(n, c) for n, c in per.items() if c != 2]}')
# ---- (F) crossings between sections and with nodestrings
T = shapely.STRtree(SL); a, b = T.query(SL, predicate='intersects'); x1 = [(sec['name'].iloc[i], sec['name'].iloc[j]) for i, j in zip(a, b) if i < j]
NL = [LineString(co(g)) for g in oth.geometry]; a2, b2 = T.query(NL, predicate='intersects')
def kind(i, j):
    if NL[i].equals(SL[j]): return 'equal'
    e = [Point(p) for p in co(SL[j])]; x = co(NL[i].intersection(SL[j]))
    return 'section end on nodestring' if all(min(q.distance(Point(p)) for q in e) < 1e-6 for p in x) else 'cross'
x2 = [(oth['name'].iloc[i], sec['name'].iloc[j], kind(i, j)) for i, j in zip(a2, b2)]
out(f'section-section crossings {x1}; section-nodestring contacts {sorted(x2, key=lambda x: x[1])}; real crossings {[x for x in x2 if x[2] == "cross"]}', not x1 and not [x for x in x2 if x[2] == 'cross'])
# ---- (G) region points
U = unary_union(ln + NL + SL); fc = list(polygonize(U)); TF = shapely.STRtree(fc); g = rg[rg.geometry.notna()]; cnt = collections.Counter(); fof = {}
for p, f in zip(*TF.query(g.geometry.values, predicate='within')): cnt[int(f)] += 1; fof[g.index[p]] = int(f)
multi = [sorted(i for i, f in fof.items() if f == j) for j, c in cnt.items() if c > 1]; empty = [i for i in range(len(fc)) if cnt[i] == 0]; outside = [i for i in g.index if i not in fof]
nt = lambda key, sep: sep + NOTE[key] if key in NOTE else ''
out(f'planar graph: {len(fc)} faces; without point {len(empty)}; with >1 point {multi} (expected []{nt("multi", ": ")}); points not inside a face {outside}; null-geometry rows {sorted(rg.index[rg.geometry.isna()])} (expected []{nt("null", ": ")})',
    not empty and not multi and not outside and rg.geometry.notna().all())
orig = rg0.loc[[i for i in rg0.index if i <= FMAX and i not in DELE]]  # deleted originals are excluded (config: originals.region_fids_deleted)
moved = [i for i in orig.index if not (i in rg.index and ((rg.geometry[i] is None and orig.geometry[i] is None) or (rg.geometry[i] is not None and orig.geometry[i] is not None and rg.geometry[i].equals(orig.geometry[i]))))]
attr = [i for i in orig.index if i in rg.index and any(not (rg.loc[i, c] == orig.loc[i, c] or (rg.loc[i, c] != rg.loc[i, c] and orig.loc[i, c] != orig.loc[i, c])) for c in ('name', 'mat_id', 'max_area', 'hole'))]
out(f'original region points (fid<={FMAX}, from {cfg.layer_name("in", "regions")}.gpkg): missing or moved {moved} (expected {REPL}{nt("moved", ", ")}), attributes changed {attr}', moved == REPL and not attr)
# attribute combinations: every (name, mat_id, max_area, hole) must exist among the original points
key = lambda r: (r.name, int(r.mat_id), float(r.max_area), None if r.hole != r.hole else float(r.hole))
K0 = {key(r) for r in rg0.itertuples()}; unk = collections.Counter(key(r) for r in rg.itertuples() if key(r) not in K0)
nul = [i for i in rg.index if rg.loc[i, ['name', 'mat_id', 'max_area']].isna().any()]
out(f'region attributes: null nome/mat_id/max_area {nul}; combinations not present in the original {dict(unk)}; mat_id per name unique {all(len(set(rg.mat_id[rg["name"] == n])) == 1 for n in set(rg["name"]))}', not nul and not unk)
# clearance from the lines, split into original points and new points
cl1 = [(i, rg['name'][i], round(U.distance(gg), 2)) for i, gg in g.geometry.items() if U.distance(gg) < CLEAR]
out(f'region points closer than {CLEAR:g} m to a line: originals {[x for x in cl1 if x[0] <= FMAX]}; new {[x for x in cl1 if x[0] > FMAX]}', all(x[0] <= FMAX for x in cl1))
# coherence with the original data: the original face (planar graph of the original layers) that contains each new point should carry the same name
ob = rd('in', 'breaklines'); obd = rd('in', 'boundary'); OL = [LineString(co(gg)[:, :2]) for gg in list(ob.geometry) + list(obd.geometry) if gg is not None and not gg.is_empty]
ofc = list(polygonize(unary_union(OL))); TO = shapely.STRtree(ofc); og = rg0[rg0.geometry.notna()]; oname = {}
for p, f in zip(*TO.query(og.geometry.values, predicate='within')): oname.setdefault(int(f), set()).add(og['name'].iloc[p])
mis = []
for i, gg in g.geometry.items():
    if i <= FMAX: continue
    f = TO.query(gg, predicate='within')
    nm = set().union(*[oname.get(int(x), set()) for x in f]) if len(f) else set()
    if rg['name'][i] not in nm: mis.append((i, rg['name'][i], sorted(nm)))
out(f'new region points whose name differs from the original region at the same place (widened banks expected): {len(mis)} {mis[:30]}')
# ---- (H) GeoPackage integrity
for key_ in ('breaklines', 'boundary', 'regions', 'centerline', 'centerpoints', 'bankpoints'):
    n = cfg.layer_name('out', key_)
    c = sqlite3.connect(f'file:{cfg.layer("out", key_)}?mode=ro', uri=True); t = c.execute("select table_name from gpkg_contents").fetchone()[0]
    ic = c.execute('pragma integrity_check').fetchone()[0]; nn = c.execute(f'select count(*) from "{t}" where geom is not null').fetchone()[0]
    rt = c.execute(f'select count(*) from "rtree_{t}_geom"').fetchone()[0]; srs = c.execute("select srs_id from gpkg_geometry_columns").fetchone()[0]; gty = c.execute("select geometry_type_name from gpkg_geometry_columns").fetchone()[0]
    out(f'{n}: integrity {ic}, rtree {rt} / geometries {nn}, srs {srs}, type {gty}', ic == 'ok' and srs == cfg['project']['crs'])
# ---- (I) angle rule (same logic as check_angles.py): no NEW angle below rules.min_angle_deg in the derived lines
import check_angles
AR = check_angles.angle_report(cfg)
out(f'angle rule (< {AR["min_deg"]:g} deg): new {len(AR["new"])} {[check_angles.fmt(i) for i in sorted(AR["new"], key=lambda t: t[3])[:20]]}; accepted by exceptions.angle {len(AR["accepted"])}; pre-existing (identical in the originals) {len(AR["pre"])}', not AR['new'])
