# check_geom.py - geometric check of the fixed breaklines (near_nodes.json)
# Purpose: compare the fixed breaklines with the current ones: (1) the section/nodestring crossing points must not move,
#          (2) the deviation of every changed breakline (Hausdorff distance) must be small, (3) no new line-line crossings.
#          Breaklines listed in params.check_geom.special_breaklines (laid on a section / slid by hand in fix_near_nodes.py) are excluded from
#          the crossing comparison.
# Inputs : cfg layers ('out', breaklines|boundary) = current derived layers, work/near_nodes.json, work/secs_new.json,
#          cfg['params']['check_geom'].
# Output : print only (crossing points lost, new crossing points, changed breaklines with Hausdorff distances, line-line crossings before/after).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/check_geom.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString

cfg = common.load(common.parser('geometric check of the fixed breaklines').parse_args())
# bl/bd = current breaklines and boundary
bl = gpd.read_file(cfg.layer('out', 'breaklines'), fid_as_index=True); bd = gpd.read_file(cfg.layer('out', 'boundary'), fid_as_index=True)
# O = old breakline coordinates, N = new ones (near_nodes.json, only >=2 vertices), secs = new sections
O = {int(f): shapely.get_coordinates(g) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
N = {int(k): np.array(v) for k, v in json.load(open(cfg.work('near_nodes.json')))['F'].items() if len(v) >= 2}
secs = json.load(open(cfg.work('secs_new.json')))
# special = breaklines excluded from the crossing comparison
special = set(cfg['params']['check_geom']['special_breaklines'])
# lines = every section and every non-section nodestring (name, LineString)
lines = [(s['nome'], LineString(s['coords'])) for s in secs] + [(n, LineString(shapely.get_coordinates(g))) for n, g in zip(bd[cfg.f('boundary', 'name')], bd.geometry) if not cfg.is_section(n)]
# X: Counter of crossing points (line name, rounded x, y) between those lines and the breaklines in D
def X(D):
    keys = list(D); ln = [LineString(D[k]) for k in keys]; T = shapely.STRtree(ln); out = collections.Counter()
    for nm, l in lines:
        for i in T.query(l, predicate='intersects'):
            if keys[i] in special: continue
            for p in shapely.get_coordinates(l.intersection(ln[i])): out[(nm, round(p[0], 5), round(p[1], 5))] += 1
    return out
# a = crossings of the old set; NU = union of the new breaklines: old crossing points must still lie on it (lost must be 0)
a = X(O); NU = shapely.union_all([LineString(c) for f, c in N.items() if f not in special])
lost = [k for k in a if NU.distance(shapely.Point(k[1], k[2])) > 1e-4]
print('crossing points before', len(a), 'no longer on the new network', len(lost), lost[:8])
# moved crossings for sections: the section must meet the new network at the same points
# b = crossings of the new set; OU = union of old breaklines: every new crossing point must already lie on the old network
b = X(N); OU = shapely.union_all([LineString(c) for f, c in O.items() if f not in special])
newp = [k for k in b if OU.distance(shapely.Point(k[1], k[2])) > 1e-4]
print('crossing points after that were not on the old network', len(newp), newp[:8])
# dev = (Hausdorff distance new vs old, fid) for every changed breakline; sorted descending
dev = []
for f in N:
    if f in O and (len(N[f]) != len(O[f]) or np.abs(N[f] - O[f]).max() > 1e-9):
        dev.append((float(LineString(N[f]).hausdorff_distance(LineString(O[f]))), f))
dev.sort(reverse=True); d = np.array([x for x, _ in dev])
print('changed', len(dev), 'hausdorff max', dev[:8], 'median', np.median(d).round(3), '>0.5 m', int((d > 0.5).sum()), '>1 m', int((d > 1).sum()))
# bad(D): pairs of breaklines that properly cross each other (not at shared vertices)
def bad(D):
    keys = list(D); ln = [LineString(D[k]) for k in keys]; T = shapely.STRtree(ln); n = set()
    a, b = T.query(ln, predicate='crosses')
    for i, j in zip(a, b):
        if i < j: n.add((keys[i], keys[j]))
    return n
# before / after comparison; 'new' must be empty
bo = bad(O); bn = bad(N); print('line-line crossings before', len(bo), 'after', len(bn), 'new', sorted(bn - bo))
