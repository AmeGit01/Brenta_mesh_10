# dp.py - choose the section stations of every reach by dynamic programming over the candidates of place.py
# Purpose: ONE dynamic programme for all reaches. Along the centerline the sections are sections.spacing +- sections.tol apart (step along
#          the line = hard limit, chord between the two centre points = soft limit). Priorities of the cost, from the strongest:
#          (1) no crossing of a nodestring or an inner breakline by the approximate section, no section of an earlier reach crossed,
#          (2) no near-node violation, no meeting point of nodestring and breakline close to a toe crossing, no crossing angle sharper than
#              rules.min_angle_deg (all with the weights of params.placement.weights), (3) spacing close to the target, perpendicularity
#              (weight perp, 0 = off). Anchors (config 'anchors': a section that must coincide with a nodestring) split a reach in
#              parts with an exact number of sections. Zones where no section may lie (params.placement.keep_clear) are excluded.
# Inputs : work/cands.pkl (place.py); the original boundary layer (nodestrings of the anchors and the keep-clear zones; work/bgn.pkl if present);
#          config: sections {spacing, tol, name_pattern, digits}, reaches[*] {code, source, first_number, start, end, end_rule},
#          anchors [{section, nodestring}], params.placement {weights, extent_beyond_toe, extent_inside_top, end_gap, farthest_back,
#          reachable_below, keep_clear [{nodestring, source, reach (optional list of codes), before, after}]}. Reach order = config order: a reach treats the sections of the earlier reaches as obstacles.
#          start / end of a reach (positions on its source centerline): {"s": metres} | {"nodestring": name} | {"section_of": code};
#          optional "window" (half-width of the start window, default sections.tol) and "prefer_target" (default true: the first section pays step*(distance from start+first_number)^2). end also {"count": n} | {"line_end": true};
#          optional "gap" (minimum distance of the last section from the end, default params.placement.end_gap for the line end, 0 else)
#          and "rule" ("window": cheapest end in [end - spacing - tol, end - gap]; "farthest": farthest reachable end). With "truncate_full": true
#          (together with s, nodestring or count) the chain is solved to the end of the line (rule and gap as for the line end) and only
#          the sections up to s / the first count are kept; the dropped tail still counts as obstacle for reaches on another centerline.
#          The first section is at start + first_number (+- window). With an anchor in the reach the part before the first anchor is
#          counted back from it, so the start window is not applied (a message gives the distance to the nominal start).
# Outputs: work/dp.pkl = dict reach code -> dict(source, idx (candidate indices; an anchor slot holds the nearest candidate), anchors
#          (list of dict k, nodestring, section, s, x, y, nx, ny, tL, tR, coords), names); diagnostics and checks on stdout.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/dp.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import pickle, numpy as np, shapely, geopandas as gpd, warnings
from shapely.geometry import LineString, Point
warnings.filterwarnings('ignore')

cfg = common.load(common.parser('choose the section stations of every reach (dynamic programming)').parse_args())
PR = cfg['params']['placement']; WT = PR['weights']
SC = cfg['sections']; SPC, TOL = SC['spacing'], SC['tol']
INV = WT['invalid']
EB, EI = PR['extent_beyond_toe'], PR['extent_inside_top']
with open(cfg.work('cands.pkl'), 'rb') as f: C = pickle.load(f)

# ---- nodestrings (anchors, keep-clear zones, start/end given as nodestring)
bd = gpd.read_file(cfg.layer('in', 'boundary'), fid_as_index=True)
bgp = cfg.work('bgn.pkl'); bgn = pickle.load(open(bgp, 'rb')) if os.path.exists(bgp) else {}
NS = {n: bgn.get(k, shapely.get_coordinates(next(iter(shapely.get_parts(g))))) for k, (n, g) in zip(bd.index, zip(bd[cfg.f('boundary', 'name')], bd.geometry))}


def nodestring(name):
    if name not in NS: raise SystemExit(f"config error: nodestring '{name}' is not in the boundary layer")
    return NS[name]


def cross(name, c, need_two=False):
    """Intersection of nodestring `name` with the polyline of the candidate centre points: (s, Point xy). It must be a single point."""
    A = nodestring(name)
    if need_two and len(A) != 2: raise SystemExit(f"nodestring '{name}' must have 2 vertices to be an anchor (has {len(A)})")
    cl = LineString(c['P']); x = LineString(A).intersection(cl)
    if x.geom_type != 'Point':
        raise SystemExit(f"nodestring '{name}' meets the centerline in {x.geom_type} (expected one point): give 's' instead")
    return float(c['ss'][0] + cl.project(x)), np.array([x.x, x.y])


def place_spec(spec, c, placed, what):
    """Position s (m) on the centerline c of a start/end specification."""
    if 's' in spec: return float(spec['s'])
    if 'nodestring' in spec: return cross(spec['nodestring'], c)[0]
    if 'section_of' in spec:
        o = placed.get(spec['section_of'])
        if o is None: raise SystemExit(f"config error: reach {what}: section_of '{spec['section_of']}' is not placed before it (reach order)")
        pt = Point(o['x'][-1] if what.endswith('start') else o['x'][0], o['y'][-1] if what.endswith('start') else o['y'][0])
        return float(c['ss'][0] + LineString(c['P']).project(pt))
    raise SystemExit(f"config error: reach {what}: unknown specification {spec}")


STEP = None   # candidate step, set per reach
# ---- anchors per reach code
ANCH = {}
for a in cfg.get('anchors', []):
    code = cfg.reach_of(a['section']); rc = cfg.reach(code); num = int(a['section'][len(code):])
    k, r = divmod(num - rc['first_number'], int(SPC))
    if r: raise SystemExit(f"config error: anchor {a['section']} is not a multiple of the spacing from first_number {rc['first_number']}")
    ANCH.setdefault(code, []).append(dict(k=k, nodestring=a['nodestring'], section=a['section']))
for v in ANCH.values(): v.sort(key=lambda a: a['k'])


def penalties(c, extra, zones, s_zone):
    """Per-candidate penalty (the strongest constraints first); invalid candidates and keep-clear zones = INV."""
    pen = WT['near'] * c['pen_near'] + WT['xn'] * c['pen_xn'] + WT['inner'] * c['hitO'] + WT['boundary'] * c['hitB'] \
        + WT['angle'] * c['pen_angle'] + WT['perp'] * c['perp_dev']
    pen = pen + extra
    pen[~c['ok']] = INV
    for (sz, bef, aft) in zones:
        pen[(c['ss'] > sz - bef) & (c['ss'] < sz + aft)] = INV
    return pen


def trans(ds, ch):
    """Cost of a step: preference for exactly the spacing; chord outside spacing +- tol costs base + factor*|chord - spacing|."""
    return WT['step'] * (ds - SPC) ** 2 + (0 if SPC - TOL <= ch <= SPC + TOL else WT['chord_base'] + WT['chord'] * abs(ch - SPC))


def forward(c, pen, init, DR):
    """Free-count forward pass over the candidates (increasing s). init = {candidate: (cost, previous marker)}. Returns (cost, prev)."""
    ss, P = c['ss'], c['P']; N = len(ss)
    cost = np.full(N, np.inf); prev = np.full(N, -1, int)
    for i, (v, p) in init.items(): cost[i] = v; prev[i] = p
    for i in range(N):
        if not np.isfinite(cost[i]) or cost[i] >= INV: continue
        for d in DR:
            j = i + d
            if j >= N: continue
            ch = float(np.hypot(*(P[j] - P[i])))
            cn = cost[i] + pen[j] + trans(d * STEP, ch)
            if cn < cost[j]: cost[j] = cn; prev[j] = i
    return cost, prev


def walk(prev, j):
    p = []
    while j >= 0: p.append(j); j = prev[j]
    return p[::-1], j       # j = -1 start window, -2 = virtual start (anchor)


def layered(c, pen, start, K, target=None, ref=None, k0=0):
    """Exact number of steps. start = ('virtual', s, P) or ('set', {candidate: cost}); target = None (free end after K steps) or (s, P).
    ref = (targets T per section, weight, window) keeps every section within window m of its target (cost weight x |s - target|);
    k0 = section number (index) of the first layer. Returns (the chosen candidates in order, cost): a start set contributes its node,
    a virtual start and the target do not."""
    ss, P = c['ss'], c['P']
    if start[0] == 'virtual': layer = {-1: 0.0}; sP0 = (start[1], start[2])
    else: layer = dict(start[1]); sP0 = None
    back = []
    for step in range(1, K + 1):
        new = {}; bk = {}; last = target is not None and step == K
        for i, ci in layer.items():
            si, Pi = sP0 if i == -1 else (ss[i], P[i])
            if last:
                ds = target[0] - si
                if SPC - TOL - 1e-6 <= ds <= SPC + TOL + 1e-6:
                    cn = ci + trans(ds, float(np.hypot(*(target[1] - Pi))))
                    if cn < new.get(-2, np.inf): new[-2] = cn; bk[-2] = i
            else:
                a = np.searchsorted(ss, si + SPC - TOL - 1e-6, 'left'); b = np.searchsorted(ss, si + SPC + TOL + 1e-6, 'right')
                for j in range(a, b):
                    if pen[j] >= INV: continue
                    if ref is None: cn = ci + pen[j] + trans(ss[j] - si, float(np.hypot(*(P[j] - Pi))))
                    else:
                        dv = abs(ss[j] - ref[0][k0 + step])
                        if dv > ref[2]: continue
                        cn = (ci + trans(ss[j] - si, float(np.hypot(*(P[j] - Pi))))) + (pen[j] + ref[1] * dv)
                    if cn < new.get(j, np.inf): new[j] = cn; bk[j] = i
        if not new: raise SystemExit(f'no feasible chain at step {step} of {K} (s about {si:.1f}); relax the constraints or add an exception')
        back.append(bk); layer = new
    j = min(layer, key=lambda k: (layer[k], k)); cst = layer[j]; seq = []
    for bk in reversed(back):
        seq.append(j); j = bk[j]
    seq = [j] + seq[::-1] if start[0] == 'set' else seq[::-1]     # j = the start node of a start set (section 0)
    return ([x for x in seq if x >= 0], cst)


# ---- reaches, in config order
res = {}; placed = {}; obst_lines = []; obst_src = []; all_ok = True
for rc in cfg.reaches():
    code, src = rc['code'], rc['source']; c = C[src]; ss, P = c['ss'], c['P']; N = len(ss)
    STEP = float(ss[1] - ss[0]); DR = list(range(int(round((SPC - TOL) / STEP)), int(round((SPC + TOL) / STEP)) + 1))
    L = ss[-1] + STEP
    first = rc['first_number']
    # obstacles: approximate sections of the earlier reaches (1e5 where a candidate section would cross one)
    ex = np.zeros(N)
    OB = [l for l, (sr, kept) in zip(obst_lines, obst_src) if kept or sr != src]   # dropped tail sections only count for other centerlines
    if OB:
        T = shapely.STRtree(OB)
        e0 = np.nan_to_num(np.minimum(c['tL'] + EB, c['cL'] - EI)); e1 = np.nan_to_num(np.minimum(c['tR'] + EB, c['cR'] - EI))
        ln = shapely.linestrings(np.stack([P + c['n'] * e0[:, None], P - c['n'] * e1[:, None]], axis=1))
        a, _ = T.query(ln, predicate='intersects'); ex[np.unique(a)] = WT['obstacle']
        print(f"{code}: candidates crossing sections of earlier reaches {int((ex > 0).sum())} of {N}")
    zones = [(cross(z['nodestring'], c)[0], z['before'], z['after']) for z in PR.get('keep_clear', []) if z.get('source', src) == src and code in z.get('reach', [code])]
    pen = penalties(c, ex, zones, None)
    start = rc.get('start'); end = rc.get('end', {'line_end': True})
    if start is None: raise SystemExit(f"config error: reaches[{code}].start is missing: {{'s': metres}} | {{'nodestring': name}} | {{'section_of': code}}")
    s_start = place_spec(start, c, placed, f'{code} start'); t0 = s_start + first; w0 = start.get('window', TOL)
    wst = WT['step'] if start.get('prefer_target', True) else 0.0     # cost per m^2 of the first section's distance from start + first_number
    anchors = []
    for a in ANCH.get(code, []):
        sa, Pa = cross(a['nodestring'], c, need_two=True); ia = int(np.argmin(np.abs(ss - sa))); A = nodestring(a['nodestring'])
        if np.dot(A[0] - Pa, c['n'][ia]) < np.dot(A[1] - Pa, c['n'][ia]): A = A[::-1]   # left end first
        u = (A[0] - A[1]) / np.linalg.norm(A[0] - A[1])
        anchors.append(dict(a, s=sa, x=float(Pa[0]), y=float(Pa[1]), nx=float(u[0]), ny=float(u[1]), tL=float(np.dot(A[0] - Pa, u)),
                            tR=float(np.dot(Pa - A[1], u)), coords=A.tolist(), ia=ia))
    # ---- end specification
    tr = end.get('truncate_full', False)          # solve to the end of the line, then keep the sections up to the given end / count
    cnt = None if tr else end.get('count'); rule = end.get('rule', 'window')
    if cnt is None:
        if tr or 'line_end' in end or end == {}: E = L; gap = end.get('gap', PR['end_gap'])
        else: E = place_spec(end, c, placed, f'{code} end'); gap = end.get('gap', 0.0)
    # ---- reference placement (re-placing a reach with an anchor): targets = previous stations shifted rigidly so that the anchor matches
    ref = None; RF = rc.get('reference')
    if RF:
        if not anchors: raise SystemExit(f"config error: reaches[{code}].reference needs an anchor of that reach")
        with open(cfg.path(RF['dp']), 'rb') as f: PV = pickle.load(f)
        if code not in PV: raise SystemExit(f"reference {RF['dp']} has no reach {code}")
        s_old = ss[np.array(PV[code]['idx'])]; a0 = anchors[0]
        Dsh = float(s_old[a0['k']] - a0['s']); T_ = s_old - Dsh
        for a in anchors: T_[a['k']] = a['s']
        ref = (T_, RF.get('weight', 0.5), RF.get('window', 5.0)); cnt = len(s_old)
        print(f"{code}: reference placement {RF['dp']}: {cnt} sections shifted by {-Dsh:.2f} m, window {ref[2]:g} m, weight {ref[1]:g}")
    # ---- chain = list of candidate indices (>=0) and anchors ('A', n) in section order
    nodes = []; cost_tot = 0.0
    if anchors:
        a0 = anchors[0]
        if a0['k'] > 0:
            lo = a0['s'] - a0['k'] * (SPC + TOL) - 1e-6; hi = a0['s'] - a0['k'] * (SPC - TOL) + 1e-6
            st = {int(i): float(pen[i]) for i in np.where((ss >= lo) & (ss <= hi) & (pen < INV))[0]}
            if ref: st = {i: v + ref[1] * abs(ss[i] - ref[0][0]) for i, v in st.items() if abs(ss[i] - ref[0][0]) <= ref[2]}
            if not st: raise SystemExit(f'no valid start candidate before anchor {a0["section"]}')
            seq, cst = layered(c, pen, ('set', st), a0['k'], (a0['s'], np.array([a0['x'], a0['y']])), ref, 0); cost_tot += cst
            nodes += seq
            print(f"{code}: start counted back from anchor {a0['section']}: first section s={ss[seq[0]]:.2f}, nominal start {t0:.2f} (window +-{w0:g})")
        nodes.append(('A', 0))
        for m in range(1, len(anchors)):
            a, b = anchors[m - 1], anchors[m]
            seq, cst = layered(c, pen, ('virtual', a['s'], np.array([a['x'], a['y']])), b['k'] - a['k'], (b['s'], np.array([b['x'], b['y']])), ref, a['k'])
            cost_tot += cst; nodes += seq + [('A', m)]
        last = anchors[-1]; kfirst = last['k']
        vs = ('virtual', last['s'], np.array([last['x'], last['y']])); Pv = vs[2]
    else:
        kfirst = -1; vs = None
    if cnt is not None:
        K = cnt - 1 - kfirst
        if K > 0:
            if vs is not None: seq, cst = layered(c, pen, vs, K, None, ref, kfirst)
            else:
                st = {int(i): float(pen[i]) + wst * (ss[i] - t0) ** 2 for i in np.where((ss >= t0 - w0 - 1e-6) & (ss <= t0 + w0 + 1e-6) & (pen < INV))[0]}
                if not st: raise SystemExit(f'reach {code}: no valid start candidate near s={t0:.2f}')
                seq, cst = layered(c, pen, ('set', st), cnt - 1)
            cost_tot += cst; nodes += seq
    else:
        init = {}
        if vs is not None:
            a = np.searchsorted(ss, last['s'] + SPC - TOL - 1e-6, 'left'); b = np.searchsorted(ss, last['s'] + SPC + TOL + 1e-6, 'right')
            for j in range(a, b):
                if pen[j] < INV: init[j] = (pen[j] + trans(ss[j] - last['s'], float(np.hypot(*(P[j] - Pv)))), -2)
        else:
            for i in np.where((ss >= t0 - w0 - 1e-6) & (ss <= t0 + w0 + 1e-6))[0]: init[int(i)] = (pen[i] + wst * (ss[i] - t0) ** 2, -1)
        cost, prev = forward(c, pen, init, DR)
        lo, hi = E - (SPC + TOL), E - gap
        if rule == 'window':
            cand = np.where((ss >= lo) & (ss <= hi) & np.isfinite(cost) & (cost < INV))[0]
            if not len(cand): raise SystemExit(f'reach {code}: no end candidate in [{lo:.1f}, {hi:.1f}]')
            j = cand[np.argmin(cost[cand])]
        elif rule == 'farthest':
            okc = np.where(np.isfinite(cost) & (cost < PR['reachable_below']) & (ss <= hi))[0]
            if not len(okc): raise SystemExit(f'reach {code}: no reachable candidate')
            print(f"{code}: reachable to s {ss[okc].max()} (line length {L})")
            j = okc[np.argmax(ss[okc])]; cand = okc[ss[okc] >= ss[j] - PR['farthest_back']]; j = cand[np.argmin(cost[cand])]
        else: raise SystemExit(f"config error: reaches[{code}].end.rule '{rule}' (use 'window' or 'farthest')")
        seq, _ = walk(prev, j); cost_tot += float(cost[j]); nodes += seq
    nfull = len(nodes); nodes_all = list(nodes)
    if tr:
        sn = [anchors[n[1]]['s'] if isinstance(n, tuple) else float(ss[n]) for n in nodes]
        if 'count' in end: nodes = nodes[:end['count']]
        else:
            E0 = place_spec(end, c, placed, f'{code} end'); nodes = [n for n, v in zip(nodes, sn) if v <= E0 + 1e-9]
        print(f"{code}: chain solved to the end of the line ({nfull} sections), kept {len(nodes)}")
    # ---- the chain as arrays; anchor slots hold the nearest candidate
    idx = np.array([n if not isinstance(n, tuple) else anchors[n[1]]['ia'] for n in nodes]); isA = np.array([isinstance(n, tuple) for n in nodes])
    n_sec = len(idx); numbers = [first + k * int(SPC) for k in range(n_sec)]; names = [cfg.section_name(code, x) for x in numbers]
    # chosen geometry: centre points and s (anchors: exact)
    Pc = P[idx].copy(); sc = ss[idx].copy()
    for m, a in enumerate(anchors):
        k = a['k']
        if not isA[k]: raise SystemExit('internal error: anchor slot')
        Pc[k] = [a['x'], a['y']]; sc[k] = a['s']
    for a in anchors:
        if a['k'] >= n_sec: raise SystemExit(f"reach {code}: anchor {a['section']} lies beyond the last section")
    ch = np.hypot(*np.diff(Pc, axis=0).T); ds = np.diff(sc); bad = (ch < SPC - TOL) | (ch > SPC + TOL)
    ni = ~isA   # real candidates
    print(f"{code}: sections {n_sec} {names[0]}..{names[-1]}  first s {sc[0]:.2f} last s {sc[-1]:.2f} line length {L:.2f} cost {cost_tot:.1f}")
    print(f"  chord {ch.min():.2f}..{ch.max():.2f} violations {int(bad.sum())} at", [(names[i], round(float(ch[i]), 2)) for i in np.where(bad)[0]],
          f"| step along the line {ds.min():.2f}..{ds.max():.2f} uniform {float(np.mean(np.abs(ds - SPC) < 1e-9)):.3f}")
    q = idx[ni]
    cnt_near = int((c['pen_near'][q] > 0).sum()); cnt_xn = int((c['pen_xn'][q] > 0).sum()); cnt_ang = int((c['pen_angle'][q] > 0).sum())
    print(f"  crossings of nodestrings {int(c['hitB'][q].sum())}, of inner breaklines {int(c['hitO'][q].sum())}, near-node violations {cnt_near} "
          f"(sections), meeting-point violations {cnt_xn}, angle < {cfg['rules']['min_angle_deg']:g} deg {cnt_ang}, "
          f"perpendicularity deviation max {float(c['perp_dev'][q].max()):.2f} deg, crossing earlier reaches {int((ex[q] > 0).sum())}, "
          f"invalid or forbidden {int((pen[q] >= INV).sum())}")
    for a in anchors: print(f"  anchor {a['section']} = nodestring {a['nodestring']} at s {a['s']:.2f}, length {a['tL'] + a['tR']:.2f}")
    ok = not bad.any() and c['hitB'][q].sum() == 0 and c['hitO'][q].sum() == 0 and (pen[q] < INV).all() and (ex[q] == 0).all()
    all_ok &= bool(ok)
    print('  OK' if ok else '  **CHECK** spacing/obstacle violations above (accept them with an exception or change the constraints)')
    # approximate lines of this reach = obstacles of the next reaches
    e0 = np.minimum(c['tL'][idx] + EB, c['cL'][idx] - EI); e1 = np.minimum(c['tR'][idx] + EB, c['cR'][idx] - EI)
    lines = [LineString([Pc[i] + c['n'][idx[i]] * e0[i], Pc[i] - c['n'][idx[i]] * e1[i]]) for i in range(n_sec)]
    for a in anchors: lines[a['k']] = LineString(a['coords'])
    obst_lines += lines; obst_src += [(src, True)] * n_sec
    for n in nodes_all[len(nodes):]:            # dropped tail of a truncated chain (real candidates only)
        if isinstance(n, tuple): continue
        t0_, t1_ = min(c['tL'][n] + EB, c['cL'][n] - EI), min(c['tR'][n] + EB, c['cR'][n] - EI)
        if np.isfinite(t0_) and np.isfinite(t1_):
            obst_lines.append(LineString([P[n] + c['n'][n] * t0_, P[n] - c['n'][n] * t1_])); obst_src.append((src, False))
    placed[code] = dict(x=[float(Pc[0][0]), float(Pc[-1][0])], y=[float(Pc[0][1]), float(Pc[-1][1])])
    res[code] = dict(source=src, idx=idx, anchors=[{k: v for k, v in a.items() if k != 'ia'} for a in anchors], names=names)
with open(cfg.work('dp.pkl'), 'wb') as f: pickle.dump(res, f)
print('OK' if all_ok else '**CHECK**')
