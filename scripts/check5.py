# check5.py  (stage 2; independent check of the 5 m rule on a breakline set; previous: fix5.py)
# Purpose: count breakline vertices within (1 mm, 5 m) of every crossing between a section and a breakline. Crossings of the same
#          section with other breaklines (narrow beds) and breaklines lying exactly on a section (1225, 987) are ignored.
# Inputs : (cwd = WD) secs_new.json, and argv[1] = JSON with key 'F' (fid -> list of vertices), normally fix5.json.
# Output : print only: number of crossings, number of violations and the list (section, minimum distance m).
# Run    : cd WD ; python3 check5.py fix5.json      (Anaconda python3; scipy needed)
# Independent 5 m check on a breakline set: vertices within (1 mm, 5 m) of every section/breakline crossing,
# ignoring the crossings of the same section (narrow beds) - those are section nodes, not breakline vertices.
import json, sys, numpy as np, shapely, collections
from shapely.geometry import LineString
from scipy.spatial import cKDTree
# secs = new sections; F = breaklines with >=2 vertices from the file given as argv[1]
secs=json.load(open('secs_new.json')); F={int(k):v for k,v in json.load(open(sys.argv[1]))['F'].items() if len(v)>=2}
# keys = fids; ln = LineStrings; T = spatial index; vt = all vertices stacked; kd = KD-tree on vt
keys=list(F); ln=[LineString(F[k]) for k in keys]; T=shapely.STRtree(ln); vt=np.vstack([np.array(F[k]) for k in keys]); kd=cKDTree(vt)
# viol = violations; n = number of crossings
viol=[]; n=0
# on = breaklines that lie on the section (both ends on it): not crossings
# P = crossing points of the section with the other breaklines
for s in secs:
    l=LineString(s['coords'])
    on=[i for i in T.query(l,predicate='intersects') if l.distance(shapely.Point(F[keys[i]][0]))<1e-6 and l.distance(shapely.Point(F[keys[i]][-1]))<1e-6]
    P=[p for i in T.query(l,predicate='intersects') if i not in on for p in shapely.get_coordinates(l.intersection(ln[i]))]
    # own = other crossings of the same section; d = distances of the vertices within 5 m of p, excluding p itself (<1 mm) and the own crossings
    for p in P:
        n+=1; own=[q for q in P if np.hypot(*(q-p))>1e-6]
        d=[(float(np.hypot(*(vt[j]-p))),j) for j in kd.query_ball_point(p,5.0)]
        d=[x for x,j in d if x>1e-3 and all(np.hypot(*(vt[j]-q))>1e-6 for q in own)]
        if d: viol.append((s['nome'],round(min(d),3)))
# result
print('crossings',n,'violations',len(viol),viol)
