# check_near_nodes.py - independent check of the near-node rule on a breakline set
# Purpose: count breakline vertices within (ignore_below, radius) of every crossing between a section and a breakline. Crossings of
#          the same section with other breaklines (narrow beds) and breaklines lying exactly on a section are ignored.
# Inputs : work/secs_new.json (sections), a JSON with key 'F' (fid -> list of vertices): argument, default work/near_nodes.json;
#          cfg['rules']['near_node'] (radius, ignore_below).
# Output : print only: number of crossings, number of violations and the list (section, minimum distance m).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/check_near_nodes.py [-c rcs_config.json] [near_nodes.json]     (scipy needed)
# Independent near-node check on a breakline set: vertices within (ignore_below, radius) of every section/breakline crossing,
# ignoring the crossings of the same section (narrow beds) - those are section nodes, not breakline vertices.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json, numpy as np, shapely, collections
from shapely.geometry import LineString
from scipy.spatial import cKDTree

ap = common.parser('independent check of the near-node rule')
ap.add_argument('fix', nargs='?', help='breakline JSON (key F); default work/near_nodes.json')
args = ap.parse_args()
cfg = common.load(args)
RADIUS = cfg['rules']['near_node']['radius']; IGN = cfg['rules']['near_node']['ignore_below']
# secs = new sections; F = breaklines with >=2 vertices from the fix file
secs = json.load(open(cfg.work('secs_new.json'))); F = {int(k): v for k, v in json.load(open(args.fix or cfg.work('near_nodes.json')))['F'].items() if len(v) >= 2}
# keys = fids; ln = LineStrings; T = spatial index; vt = all vertices stacked; kd = KD-tree on vt
keys = list(F); ln = [LineString(F[k]) for k in keys]; T = shapely.STRtree(ln); vt = np.vstack([np.array(F[k]) for k in keys]); kd = cKDTree(vt)
# viol = violations; n = number of crossings
viol = []; n = 0
# on = breaklines that lie on the section (both ends on it): not crossings
# P = crossing points of the section with the other breaklines
for s in secs:
    l = LineString(s['coords'])
    on = [i for i in T.query(l, predicate='intersects') if l.distance(shapely.Point(F[keys[i]][0])) < 1e-6 and l.distance(shapely.Point(F[keys[i]][-1])) < 1e-6]
    P = [p for i in T.query(l, predicate='intersects') if i not in on for p in shapely.get_coordinates(l.intersection(ln[i]))]
    # own = other crossings of the same section; d = distances of the vertices within the radius of p, excluding p itself and the own crossings
    for p in P:
        n += 1; own = [q for q in P if np.hypot(*(q - p)) > 1e-6]
        d = [(float(np.hypot(*(vt[j] - p))), j) for j in kd.query_ball_point(p, RADIUS)]
        d = [x for x, j in d if x > IGN and all(np.hypot(*(vt[j] - q)) > 1e-6 for q in own)]
        if d: viol.append((s['nome'], round(min(d), 3)))
# result
print('crossings', n, 'violations', len(viol), viol)
