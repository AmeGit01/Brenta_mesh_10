# merge_vb.py  (stage 6, 2026-11-24; uses the river-cross-sections skill scripts; next: write3.py of the skill, then verify)
# Purpose: go from three reaches (N, V, B) to two (V, B).
#   * V: sections unchanged; the nodestring 'divergenza_valle_brenta_vecchio' is renamed V00000 and becomes the first V section
#        (centre point = intersection with the V centerline extended back to it; bankpoints = its two ends, kind 'nodestring').
#        The V centerline is extended back to V00000, so every V chainage grows by that length.
#   * B: one reach from the upstream boundary to the end. The old N sections are moved DOWN the chainage by DELTA (all by the same amount,
#        so every spacing is kept), DELTA chosen so that the old N16050 ends 150 m upstream of the old B00000; two new sections are added
#        in between (spacing exactly 50 m). The old B sections keep their geometry and attributes; only names and chainages change.
#        Names: B00000 = first section, then position x 50 (old B00000 -> B16150).
#   The moved and new sections are recomputed with the method of the skill: centre on the centerline, direction perpendicular to the
#   chord s-1..s+1 m, toe/top distances on the current derived layers, bankpoints by bank.py (first crest, caps by next_bed.py/obst.py).
# Subcommands
#   prep     <layers> <WD>   : writes WD/work/sec_in.json with the new B stations, plus WD/work/check_in.json with the CURRENT N stations
#                              (validation: bank.py on them must give back the delivered N bankpoints).
#   assemble <layers> <WD>   : reads WD/work/bank_out.json (bank.py on sec_in.json), writes WD/work/secs_new.json + near_nodes.json
#                              (for regions2.py) and WD/work/merge_payload.json (for write3.py; regions added later by 'regions').
#   regions  <layers> <WD>   : adds reg_drop / reg_new from WD/work/regions2.json to the payload.
# WD = a working folder of the skill (rcs_config.json + layers/ + work/), see docs/scripts/merge_vb.md.
# Run    : ~/anaconda3/bin/python3 scripts/merge_vb.py prep layers WD   (Anaconda python3; read-only on the layers)
import sys, os, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skills', 'river-cross-sections', 'scripts'))
import common, geom
CMD, L, WD = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = common.Config(os.path.join(WD, 'rcs_config.json'))
rd = lambda n: gpd.read_file(f'{L}/{n}.gpkg', fid_as_index=True)
co = lambda g: shapely.get_coordinates(g)[:, :2]
issec = lambda n: cfg.is_section(n)
DIV = 'divergenza_valle_brenta_vecchio'; DIV_NEW = 'V00000'
SPACING = 50.0
bd, cp, bp = rd('boundary_50m'), rd('centerpoints_50m'), rd('bankpoints_50m')
ref = rd('centerline_50m_backup_20261117'); A = ref[ref.nome == 'asta_principale'].geometry.iloc[0]   # main-stem centerline (s = 0 at BC_caldonazzo)
cl = rd('centerline_50m'); Vline = cl[cl.ramo == 'V'].geometry.iloc[0]
CP = cp.set_index('nome'); s_of = lambda n: float(CP.at[n, 's_m'])
Nn = list(cp[cp.stream == 'N'].sort_values('s_m').nome); Bn = list(cp[cp.stream == 'B'].sort_values('s_m').nome)
Vn = list(cp[cp.stream == 'V'].sort_values('s_m').nome)
sB0 = float(cl[cl.ramo == 'B'].s0_asta.iloc[0])                    # chainage of the old B00000 on the main stem
DELTA = s_of(Nn[-1]) - (sB0 - 3 * SPACING)                         # shift of every old N section
newname = lambda k: cfg.section_name('B', k * int(SPACING))
work = lambda f: os.path.join(WD, 'work', f)

def stations():
    """New B reach before the old B00000: (name, s on the main stem, origin)."""
    out = [(newname(k), s_of(n) - DELTA, n) for k, n in enumerate(Nn)]
    k0 = len(Nn)
    out += [(newname(k0), sB0 - 2 * SPACING, 'new'), (newname(k0 + 1), sB0 - SPACING, 'new')]
    return out

if CMD == 'prep':
    # planar graph of the derived layers WITHOUT sections: toe = outline of the bed faces, top = outline of bed+bank+wall (as place.py)
    bl = rd('breaklines_50m'); bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
    rg = rd('regioni_ponti_50m'); rg = rg[rg.geometry.notna()]
    lines = [LineString(co(g)) for g in bl.geometry] + [LineString(co(g)) for n, g in zip(bd.nome, bd.geometry) if not issec(n)]
    fc = list(polygonize(unary_union(lines))); t = shapely.STRtree(fc); ix = t.query(rg.geometry.values, predicate='within')
    rows = []; seen = set()
    for p, f in zip(*ix):
        if int(f) not in seen: seen.add(int(f)); rows.append(dict(face=int(f), nome=rg.nome.iloc[int(p)]))
    PR = cfg['params']['placement']
    Rb = geom.Rays(geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in set(PR['toe_classes'])))
    Rc = geom.Rays(geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in set(PR['top_classes'])))
    H, RAY = PR['tangent_half'], PR['ray_range']
    def record(name, s):
        """sec_in record at chainage s of the main stem (fields of export_sec.py)."""
        P = co(A.interpolate(s))[0]; a = co(A.interpolate(max(s - H, 0)))[0]; b = co(A.interpolate(min(s + H, A.length)))[0]
        d = (b - a) / np.hypot(*(b - a)); n = np.array([-d[1], d[0]])
        hb = Rb.hits(P, n, RAY); hc = Rc.hits(P, n, RAY)
        if not (hb > 0).any() or not (hb < 0).any(): raise SystemExit(f'{name}: toe not found on both sides at s {s:.2f}')
        tL = hb[hb > 0].min(); tR = -hb[hb < 0].max()
        c1 = hc[hc > tL - 1e-6]; c2 = hc[hc < -tR + 1e-6]
        if not len(c1) or not len(c2): raise SystemExit(f'{name}: top of bank not found at s {s:.2f}')
        return dict(stream='B', tag='B', name=name, s=float(s), x=float(P[0]), y=float(P[1]), nx=float(n[0]), ny=float(n[1]),
                    tL=float(tL), tR=float(tR), cL=float(c1.min()), cR=float(-c2.max()))
    ST = stations()
    json.dump([record(nm, s) for nm, s, _ in ST], open(work('sec_in.json'), 'w'))
    json.dump([record(n, s_of(n)) for n in Nn], open(work('check_in.json'), 'w'))
    print(f'faces {len(fc)}; DELTA {DELTA:.6f} m; first section {ST[0][0]} at s {ST[0][1]:.3f}; last moved {ST[len(Nn)-1][0]} at s {ST[len(Nn)-1][1]:.3f};'
          f' new {ST[-2][0]} {ST[-2][1]:.3f}, {ST[-1][0]} {ST[-1][1]:.3f}; old B00000 at {sB0:.3f}')
    print('written', work('sec_in.json'), len(ST), 'and', work('check_in.json'), len(Nn))

elif CMD == 'assemble':
    S = json.load(open(work('sec_in.json'))); O = json.load(open(work('bank_out.json')))
    assert len(S) == len(O) and [s['name'] for s in S] == [nm for nm, _, _ in stations()]
    secs = []; cpo = []; bpo = []
    BPi = bp.set_index('nome')
    def bp_row(sec, side, x, y, s, z, dcp, kind, rule, prom):
        return dict(name=f'{sec}_{side}', section=sec, s=float(s), x=float(x), y=float(y), z=z, dist_cp=float(dcp), kind=kind, rule=rule, prom=prom)
    # B, part 1: recomputed sections (left = c + n tL, right = c - n tR)
    for s, o in zip(S, O):
        c = np.array([s['x'], s['y']]); n = np.array([s['nx'], s['ny']])
        if o['L']['z'] is None or o['R']['z'] is None: raise SystemExit(f"{s['name']}: bankpoint without DTM value {o['L']['kind']} {o['R']['kind']}")
        p0 = c + n * o['L']['t']; p1 = c - n * o['R']['t']
        secs.append(dict(name=s['name'], coords=[p0.tolist(), p1.tolist()]))
        cpo.append(dict(name=s['name'], reach='B', s=s['s'], x=c[0], y=c[1]))
        for side, p, q in (('sx', p0, o['L']), ('dx', p1, o['R'])):
            bpo.append(bp_row(s['name'], side, p[0], p[1], s['s'], q['z'], q['t'], q['kind'], q['rule'], q['prom']))
    # B, part 2: old B sections, geometry unchanged, renamed; chainage = position on the main stem
    k0 = len(S)
    for j, old in enumerate(Bn):
        nm = newname(k0 + j); g = LineString(co(bd[bd.nome == old].geometry.iloc[0]))
        x = g.intersection(A); assert x.geom_type == 'Point', (old, x.geom_type); sx = float(A.project(x))
        secs.append(dict(name=nm, coords=co(g).tolist())); cpo.append(dict(name=nm, reach='B', s=sx, x=x.x, y=x.y))
        for side in ('sx', 'dx'):
            q = BPi.loc[f'{old}_{side}']; prom = None if q.prom != q.prom else float(q.prom)
            bpo.append(bp_row(nm, side, q.geometry.x, q.geometry.y, sx, float(q.z_dtm), float(q.dist_cp), q.tipo, q.regola, prom))
    # V: centerline extended back to the renamed nodestring; every V chainage + back
    dv = LineString(co(bd[bd.nome == DIV].geometry.iloc[0])); vc = co(Vline)
    u = (vc[0] - vc[1]) / np.hypot(*(vc[0] - vc[1])); X = LineString([vc[0] + u * 50, vc[0]]).intersection(dv)
    assert X.geom_type == 'Point'; back = float(Point(vc[0]).distance(X)); Vnew = LineString(np.vstack([[X.x, X.y], vc]))
    vsec = []; vcp = []; vbp = []
    a, b = co(dv)
    vcp.append(dict(name=DIV_NEW, reach='V', s=0.0, x=X.x, y=X.y))
    for side, p in (('sx', a), ('dx', b)):
        vbp.append(bp_row(DIV_NEW, side, p[0], p[1], 0.0, None, np.hypot(p[0] - X.x, p[1] - X.y), cfg['bankpoint_values']['nodestring'], DIV_NEW, None))
    for n in Vn:
        g = bd[bd.nome == n].geometry.iloc[0]; s = s_of(n) + back; q0 = CP.loc[n]
        vsec.append(dict(name=n, coords=co(g).tolist())); vcp.append(dict(name=n, reach='V', s=s, x=q0.geometry.x, y=q0.geometry.y))
        for side in ('sx', 'dx'):
            q = BPi.loc[f'{n}_{side}']; prom = None if q.prom != q.prom else float(q.prom)
            vbp.append(bp_row(n, side, q.geometry.x, q.geometry.y, s, float(q.z_dtm), float(q.dist_cp), q.tipo, q.regola, prom))
    # dist_next within each reach
    for lst in (vcp, cpo):
        for i, r in enumerate(lst): r['dist_next'] = lst[i + 1]['s'] - r['s'] if i + 1 < len(lst) else None
    clo = [dict(name='V_brenta_vecchio', reach='V', coords=co(Vnew).tolist(), s0=None),
           dict(name='B_caldonazzo_valle', reach='B', coords=co(A).tolist(), s0=0.0)]
    div_fid = int(bd[bd.nome == DIV].index[0])
    payload = dict(secs=vsec + secs, rename={str(div_fid): DIV_NEW}, cl=clo, cp=vcp + cpo, bp=vbp + bpo)
    json.dump(payload, open(work('merge_payload.json'), 'w'))
    # inputs of regions2.py: current breaklines unchanged (F), all the new sections (V00000 is a nodestring of the boundary layer)
    bl = rd('breaklines_50m'); bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
    json.dump(dict(F={str(f): co(g).tolist() for f, g in bl.geometry.items()}), open(work('near_nodes.json'), 'w'))
    json.dump([dict(nome=s['name'], coords=s['coords']) for s in vsec + secs], open(work('secs_new.json'), 'w'))
    sp = np.diff([r['s'] for r in cpo]); spv = np.diff([r['s'] for r in vcp])
    print(f'V: V00000 at {back:.3f} m before the old V start; {len(vcp)} sections, spacing min/max {spv.min():.3f}/{spv.max():.3f}')
    print(f'B: {len(cpo)} sections ({len(S)} recomputed, {len(Bn)} kept), spacing min/max {sp.min():.3f}/{sp.max():.3f};'
          f' out of 50+-0.5: {[(cpo[i]["name"], cpo[i+1]["name"], round(d, 3)) for i, d in enumerate(sp) if abs(d - 50) > 0.5]}')
    print('kinds of the recomputed bankpoints', {k: sum(1 for r in bpo[:2 * len(S)] if r['kind'] == k) for k in set(r['kind'] for r in bpo[:2 * len(S)])})
    print('written', work('merge_payload.json'), 'sections', len(payload['secs']), 'cp', len(payload['cp']), 'bp', len(payload['bp']))

elif CMD == 'regions':
    # Only the region changes CAUSED by the section change are applied: a point is dropped or added only if its face (in the final
    # graph) is bounded by a recomputed section or was bounded by a removed old N section. Other changes proposed by regions2.py
    # (faces changed by the user's own edits) are listed and left alone.
    R = json.load(open(work('regions2.json'))); P = json.load(open(work('merge_payload.json')))
    rg = rd('regioni_ponti_50m'); bl = rd('breaklines_50m'); bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
    recomputed = {nm for nm, _, _ in stations()}
    changed = [LineString(s['coords']) for s in P['secs'] if s['name'] in recomputed] + \
              [LineString(co(g)) for n, g in zip(bd.nome, bd.geometry) if n in set(Nn)]
    CH = unary_union(changed)
    lines = [LineString(co(g)) for g in bl.geometry] + [LineString(co(g)) for n, g in zip(bd.nome, bd.geometry) if not issec(n)] + \
            [LineString(s['coords']) for s in P['secs']]
    fc = list(polygonize(unary_union(lines))); T = shapely.STRtree(fc)
    def caused(x, y):
        """True if the face of (x, y) in the final graph, or its old face, touches a recomputed or removed section."""
        i = T.query(Point(x, y), predicate='within')
        return len(i) > 0 and fc[int(i[0])].exterior.distance(CH) < 1e-6 or Point(x, y).distance(CH) < 60 and \
            any(fc[int(j)].boundary.distance(CH) < 1e-6 for j in i)
    keep_drop = [f for f in R['drop'] if caused(rg.at[f, 'geometry'].x, rg.at[f, 'geometry'].y)]
    keep_new = [p for p in R['new'] if caused(p['x'], p['y'])]
    skipped = [('drop', f, rg.at[f, 'nome']) for f in R['drop'] if f not in keep_drop] + \
              [('new', p['name'], round(p['x'], 1), round(p['y'], 1)) for p in R['new'] if p not in keep_new]
    P['reg_drop'] = keep_drop
    P['reg_new'] = [dict(x=p['x'], y=p['y'], name=p['name'], mat_id=p['mat_id'], max_area=p['max_area'], hole=p['hole']) for p in keep_new]
    json.dump(P, open(work('merge_payload.json'), 'w'))
    print('regions: drop', len(keep_drop), 'new', len(keep_new), '| not caused by the sections, left alone:', skipped)
