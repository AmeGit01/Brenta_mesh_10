# sync_cp_bp.py - realign centerline, centerpoints and bankpoints to the sections as they are now in the boundary layer
# Purpose: after sections were moved or reshaped by hand, bring the three layers back in line. For every section of every reach:
#            * centre point = intersection of the section with the centre line of its reach; s = chainage of that point within the reach;
#            * a reach with chainage mode 'cut_reference' has its centre line cut again from the reference line, starting at the
#              intersection with its origin section (s0 = chainage of the origin section on the reference line); its sections are
#              intersected with the whole reference line and s = chainage on the reference line - s0;
#              a reach with mode 'own' keeps its centre line and s0 as they are in the layer;
#            * dist_next = s(next) - s (None for the last section of a reach);
#            * bankpoints = the two section vertices (left = first). A vertex that coincides (<= 1e-6 m) with the stored bankpoint keeps
#              kind/rule/prom/z; a vertex that moved becomes kind/rule 'manual' (cfg bankpoint_values.manual), prom None, z None (write3.py
#              reads it from the DTM), except when the section has the same geometry as a non-section nodestring: then
#              kind = 'nodestring' (cfg bankpoint_values.nodestring) and rule = the nodestring name. dist_cp is recomputed for all.
# Inputs : derived layers boundary, centerline, centerpoints, bankpoints (cfg 'outputs'); for 'cut_reference' reaches the file
#          cfg reaches[*].chainage.reference_file (relative to the working folder) with the line named chainage.reference_line;
#          cfg fields, sections, reaches, bankpoint_values. argv: output payload json.
# Output : payload {cl, cp, bp} with logical keys (read by write3.py); prints the centre points / chainages that changed, the bankpoints
#          that changed status and the written counts.
# Run    : cd <working folder> ; ~/anaconda3/bin/python3 <toolkit>/scripts/sync_cp_bp.py [-c rcs_config.json] payload.json
#          then  /usr/bin/python3 <toolkit>/scripts/write3.py payload.json <tag>
import sys, os, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from shapely.geometry import LineString, Point
from shapely.ops import substring
ap = common.parser('realign centerline/centerpoints/bankpoints to the current sections'); ap.add_argument('out')
args = ap.parse_args(); cfg = common.load(args); OUT = args.out
F = cfg.f; BV = cfg['bankpoint_values']
co = lambda g: shapely.get_coordinates(g)
nan = lambda v: v != v
# current layers
b = gpd.read_file(cfg.layer('out', 'boundary')); cl = gpd.read_file(cfg.layer('out', 'centerline'))
cp = gpd.read_file(cfg.layer('out', 'centerpoints')); bp = gpd.read_file(cfg.layer('out', 'bankpoints'))
bn, cn, cr, c0 = F('boundary', 'name'), F('centerline', 'name'), F('centerline', 'reach'), F('centerline', 's0')
cpn, cps, cpr = F('centerpoints', 'name'), F('centerpoints', 's'), F('centerpoints', 'reach')
issec = [cfg.is_section(n) for n in b[bn]]
sec = b[issec]; ns = b[[not x for x in issec]]
CP = {getattr(r, cpn): r for r in cp.itertuples()}; BP = {getattr(r, F('bankpoints', 'name')): r for r in bp.itertuples()}
# nodestrings: name -> coordinates (to recognise a section that is a nodestring)
NS = {n: co(g) for n, g in zip(ns[bn], ns.geometry)}
# centre lines per reach: 'own' reaches keep the layer line; 'cut_reference' reaches are cut from the reference line at the origin section
line = {r[cr]: r.geometry for _, r in cl.iterrows()}
base, off, s0out = {}, {}, {}
for rc in cfg.reaches():
    code, ch = rc['code'], rc['chainage']
    old = cl[cl[cr] == code][c0].iloc[0]
    if ch['mode'] == 'own':
        base[code], off[code] = line[code], 0.0; s0out[code] = None if nan(old) else float(old)
    elif ch['mode'] == 'cut_reference':
        ref = gpd.read_file(cfg.path(ch['reference_file']))
        A = ref[ref[cn] == ch['reference_line']].geometry.iloc[0]
        g0 = LineString(co(sec[sec[bn] == ch['origin_section']].geometry.iloc[0])); x0 = g0.intersection(A)
        assert x0.geom_type == 'Point', x0.geom_type
        s0 = A.project(x0); line[code] = substring(A, s0, A.length)
        # the sections are intersected with the full reference line (the cut line starts exactly on the origin section, which would give a
        # degenerate intersection); the chainage of the reach is the one on the reference minus s0
        base[code], off[code] = A, float(s0); s0out[code] = float(s0)
        print(f"{ch['origin_section']} on the reference line {ch['reference_line']}: s0 {old:.3f} -> {s0:.3f} (shift {s0 - old:+.3f} m)")
    else:
        raise SystemExit('unknown chainage mode: ' + ch['mode'])
# per section: centre point and chainage
rows = {}
for nm, g in zip(sec[bn], sec.geometry):
    rc = cfg.reach_of(nm)
    l = LineString(co(g)); x = l.intersection(base[rc])
    assert x.geom_type == 'Point', (nm, x.geom_type)
    s = float(base[rc].project(x)) - off[rc]
    rows[nm] = dict(name=nm, reach=rc, x=x.x, y=x.y, s=s, coords=co(g))
# report: centre points that moved (> 1 mm) or chainage that changed (> 1 mm)
mv = [(n, round(float(np.hypot(r['x'] - CP[n].geometry.x, r['y'] - CP[n].geometry.y)), 3), round(r['s'] - getattr(CP[n], cps), 3)) for n, r in rows.items()
      if np.hypot(r['x'] - CP[n].geometry.x, r['y'] - CP[n].geometry.y) > 1e-3 or abs(r['s'] - getattr(CP[n], cps)) > 1e-3]
print('centre points moved or s changed (name, move m, delta s):', len(mv)); print(' ', mv[:40])
# dist_next per reach (order of the boundary layer = reach order)
order = list(rows)
for i, n in enumerate(order):
    nx = order[i + 1] if i + 1 < len(order) and rows[order[i + 1]]['reach'] == rows[n]['reach'] else None
    rows[n]['dist_next'] = rows[nx]['s'] - rows[n]['s'] if nx else None
# bankpoints
bpo = []; changed = []
for n, r in rows.items():
    c = r['coords']
    # nodestring with the same geometry as the section (either direction)
    same = [k for k, v in NS.items() if v.shape == c.shape and (np.abs(v - c).max() < 1e-6 or np.abs(v[::-1] - c).max() < 1e-6)]
    for t, p in ((BV['left'], c[0]), (BV['right'], c[-1])):
        q = BP[f'{n}_{t}']; d = float(np.hypot(p[0] - q.geometry.x, p[1] - q.geometry.y))
        e = dict(name=f'{n}_{t}', section=n, s=r['s'], x=float(p[0]), y=float(p[1]), dist_cp=float(np.hypot(p[0] - r['x'], p[1] - r['y'])))
        qk = getattr(q, F('bankpoints', 'kind'))
        if d <= 1e-6:
            pr = getattr(q, F('bankpoints', 'prom'))
            e.update(z=float(getattr(q, F('bankpoints', 'z'))), kind=qk, rule=getattr(q, F('bankpoints', 'rule')), prom=None if nan(pr) else float(pr))
        else:
            e.update(z=None, prom=None, kind=BV['nodestring'] if same else BV['manual'], rule=same[0] if same else BV['manual'])
            changed.append((e['name'], round(d, 2), qk, '->', e['kind']))
        bpo.append(e)
print('bankpoints moved:', len(changed)); print(' ', changed)
# centre lines out
cl_out = [dict(name=r[cn], reach=r[cr], coords=co(line[r[cr]])[:, :2].tolist(), s0=s0out[r[cr]]) for _, r in cl.iterrows()]
cp_out = [dict(name=r['name'], reach=r['reach'], s=r['s'], x=r['x'], y=r['y'], dist_next=r['dist_next']) for r in rows.values()]
json.dump(dict(cl=cl_out, cp=cp_out, bp=bpo), open(OUT, 'w'))
print('written', OUT, 'cl', len(cl_out), 'cp', len(cp_out), 'bp', len(bpo))
