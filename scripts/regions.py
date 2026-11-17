# regions.py  (step 16; previous: finals.py, next: dump.py)
# Purpose: make sure that every face of the final planar graph (widened breaklines + boundary + new sections) has a region point
#          (one per face, >= 1 m from every line when possible). Old region points that fall too close to lines are dropped,
#          and faces left without a point get a new one (pole of inaccessibility) copying the attributes of the old point of the parent face.
# Inputs : WD/work/sec_in.json, bank_out.json (loaded, not really used here), secs0.pkl (finals.py), widen2.pkl, chains.pkl, bgn.pkl, newfaces.pkl,
#          WD/in/regioni_ponti.gpkg (region points: nome, mat_id, max_area, buco) and WD/in/boundary.gpkg.
# Outputs: WD/work/regions.json {new:[{face,x,y,nome,mat_id,max_area,buco,clear}], dropped:[fid of old points], kept:[fid of old points kept]};
#          WD/work/finalfaces.pkl {fc: list of final face polygons}. Statistics are printed.
# Run    : python3 regions.py WD      (Anaconda python3; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
from shapely.ops import unary_union, polygonize, polylabel
S=json.load(open(f'{SP}/work/sec_in.json')); O=json.load(open(f'{SP}/work/bank_out.json')); secs=pickle.load(open(f'{SP}/work/secs0.pkl','rb'))
W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb')); Cc=pickle.load(open(f'{SP}/work/chains.pkl','rb')); bgn=pickle.load(open(f'{SP}/work/bgn.pkl','rb')); NF=pickle.load(open(f'{SP}/work/newfaces.pkl','rb'))
# base/baserows: faces and (face,nome) rows BEFORE adding the sections (newfaces.pkl); feat/newf as in finals.py.
feat=Cc['feat']; newf=W2['newf']; base=NF['fc']; baserows=NF['rows']
r=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True); bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True)
bgeo={k:bgn.get(k,shapely.get_coordinates(next(iter(shapely.get_parts(g))))) for k,g in bdf.geometry.items()}
# L = all lines of the final graph: breaklines (moved where applicable) + boundary features (moved where applicable) + new sections.
# polygonize(unary_union(L)) -> fc = final faces; A = their areas (small faces are counted for information).
L=[LineString(newf.get(f,a)) for f,a in feat.items()]+[LineString(a) for a in bgeo.values()]+list(secs)
u=unary_union(L); fc=list(polygonize(u)); A=np.array([f.area for f in fc]); print('faces with sections',len(fc),'small<0.5',(A<0.5).sum(), 'small<5',(A<5).sum())
# ix = pairs (point index, face index) of region points lying within a final face; fac[face] = list of point indices (positional) in that face.
t=shapely.STRtree(fc); ix=t.query(r.geometry.values,predicate='within')
fac=collections.defaultdict(list)
for p,f in zip(*ix): fac[int(f)].append(int(p))
print('faces w points',len(fac),'points in faces',len(ix[0]),'of',len(r))
# attr[i] = index of the base face (before sections) that contains the representative point of final face i.
tb=shapely.STRtree(base); attr={}
for i,f in enumerate(fc):
    idx=tb.query(f.representative_point(),predicate='within'); 
    if len(idx): attr[i]=int(idx[0])
# bfp[base face] = positional indices of the original region points in that base face (used as attribute source for new points).
bx=shapely.STRtree(base); bxr={x['face']:x['nome'] for x in baserows}
# point attributes per base face: from the original points
bpix=bx.query(r.geometry.values,predicate='within'); bfp=collections.defaultdict(list)
for p,f in zip(*bpix): bfp[int(f)].append(int(p))
# d_old = distance of every region point from the ORIGINAL lines (original breaklines + original boundary); d (below) = distance from the new lines.
allline=unary_union(L)
d_old=shapely.distance(unary_union([LineString(a) for a in feat.values()]+[LineString(next(iter(shapely.get_parts(g))).coords) for g in bdf.geometry]),r.geometry.values)
# rid = fid of each region point (GPKG index), nome = its name. keep = set of positional indices of points kept; newpts/dropped = results.
rid=r.index.to_numpy(); nome=r.nome.values
keep=set(); newpts=[]; dropped=[]; d=shapely.distance(allline,r.geometry.values)
print('points dist<1 m',int((d<1).sum()),[(int(rid[i]),nome[i],round(float(d[i]),2)) for i in np.where(d<1)[0]][:30])
# points outside any face (keep), others
# Points that are in no final face are always kept. In each face, a point is acceptable if it is >= 1 m from all lines or no closer than it was
# to the original lines; if the face has at least one acceptable point, those are kept (others are left out of `keep`),
# otherwise all its points are dropped (to be replaced by a new point).
in_face=set(int(p) for p in ix[0]); keep|=set(range(len(r)))-in_face
for f,ps in fac.items():
    ok=[p for p in ps if d[p]>=1.0 or d[p]>=d_old[p]-1e-6]
    if ok:
        keep|=set(ok)      # keep all (pre-existing duplicates are left as is)
    else:
        dropped+=[int(rid[p]) for p in ps]
# New points: for each final face with no kept point, take the attributes of the first original point of its parent base face and place the
# point at polylabel(face, tolerance 0.05 m); 'clear' = distance to the nearest line. Faces without a parent point are listed in errs.
kept=sorted(keep)
# new points for faces without a kept point
facekept=set()
for f,ps in fac.items():
    if any(p in keep for p in ps): facekept.add(f)
errs=[]
for i,f in enumerate(fc):
    if i in facekept: continue
    b=attr.get(i)
    if b is None or b not in bfp: errs.append((i,round(A[i],2))); continue
    p0=r.iloc[bfp[b][0]]
    pt=polylabel(f,tolerance=0.05); newpts.append(dict(face=i,x=pt.x,y=pt.y,nome=p0.nome,mat_id=int(p0.mat_id),max_area=float(p0.max_area),buco=None if p0.buco is None or str(p0.buco)=='nan' or p0.buco!=p0.buco else int(p0.buco),clear=float(pt.distance(allline))))
# Summary: counts, clearance of the new points (min/median, how many < 1 m) and breakdown by nome.
print('kept',len(kept),'dropped',len(dropped),dropped[:30],'new',len(newpts),'errs',errs[:10])
c=np.array([p['clear'] for p in newpts]); print('new clear min/med',c.min().round(2),np.median(c).round(2),'<1 m',int((c<1).sum()))
print(collections.Counter(p['nome'] for p in newpts))
# Save results for dump.py (JSON: fids of old points are the GPKG indices, not positions).
json.dump(dict(new=newpts,dropped=dropped,kept=[int(rid[i]) for i in kept]),open(f'{SP}/work/regions.json','w'))
pickle.dump(dict(fc=fc),open(f'{SP}/work/finalfaces.pkl','wb'))
