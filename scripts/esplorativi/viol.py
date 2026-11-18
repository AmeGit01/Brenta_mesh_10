# viol.py  (exploratory, NOT needed to produce the layers; stage 2, 2026-11-17)
# Purpose: count the violations of the 5 m rule (a breakline vertex within (1 mm, 5 m) of a section/breakline crossing) on a set of 50 m layers.
# Inputs : (cwd = WD) argv[1] = folder with breaklines_50m.gpkg and boundary_50m.gpkg (default 'in'); optional flag -v lists every violation.
# Output : print: crossings, violations, number of sections involved, violations closer than 0.5 m; with -v each (section, fid, distance, point).
# Run    : python3 viol.py in      (Anaconda python3; add -v for the list)
import geopandas as gpd, shapely, numpy as np, sys, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
from scipy.spatial import cKDTree
# d = folder of the layers
d=sys.argv[1] if len(sys.argv)>1 else 'in'
# bl = breaklines, bd = boundary
bl=gpd.read_file(f'{d}/breaklines_50m.gpkg',fid_as_index=True); bd=gpd.read_file(f'{d}/boundary_50m.gpkg',fid_as_index=True)
# co: coordinates; issec: name of a section (S/V/N/B + 5 digits); sec = section features
co=lambda g: shapely.get_coordinates(g)
issec=lambda n: n[0] in 'SVNB' and n[1:6].isdigit()
sec=bd[[issec(n) for n in bd.nome]]
# F = breakline coordinates; vt = all vertices; kd = KD-tree; ln/T = lines and spatial index
F={k:co(g) for k,g in bl.geometry.items() if g is not None and not g.is_empty}
vt=np.vstack(list(F.values())); kd=cKDTree(vt); keys=list(F); ln=[LineString(F[k]) for k in keys]; T=shapely.STRtree(ln)
# viol = violations (section, fid, distance, crossing point)
viol=[]; n=0
# for each crossing of a section with a breakline, the distances of vertices within 5 m (excluding the crossing itself, <1 mm)
for nm,g in zip(sec.nome,sec.geometry):
    l=LineString(co(g))
    for i in T.query(l,predicate='intersects'):
        for p in co(l.intersection(ln[i])):
            n+=1; v=sorted(float(np.hypot(*(vt[j]-p))) for j in kd.query_ball_point(p,5.0))
            v=[x for x in v if x>1e-3]
            if v: viol.append((nm,keys[i],round(v[0],3),tuple(float(x) for x in np.round(p,2))))
# summary
print('crossings',n,'viol',len(viol),'sections',len({v[0] for v in viol}),'<0.5',sum(v[2]<0.5 for v in viol))
if '-v' in sys.argv:
    for v in viol: print(v)
