# regions2.py  (stage 2, 2026-11-17; previous: check_geom.py, next: prep_write.py)
# Purpose: choose ONE region point per face of the final planar graph (breaklines + nodestrings + sections). Rules: a face already holding
#          the pair 57/58 is left as it is (pre-existing pair); otherwise keep the first point (originals fid<=176 first) that is >= 1 m from every
#          line; in narrow faces an original point (fid<=176) is never replaced (the one with the largest clearance is kept); otherwise a new point
#          at the pole of inaccessibility (polylabel) with the attributes (nome, mat_id, max_area, buco) of the original region the face comes from.
# Inputs : (cwd = WD) fix5.json, secs_new.json, in/boundary_50m.gpkg, in/regioni_ponti_50m.gpkg, in0/regioni_ponti.gpkg (original points),
#          work/newfaces.pkl (place.py; 'fc' = faces before the stage-2 edits, used to find the original region of a face).
# Output : WD/regions2.json = dict(keep = fids kept, drop = fids to delete, new = new points (face,x,y,nome,mat_id,max_area,buco,clear), nfaces);
#          prints counts, dropped/new lists, kept points with clearance < 1 m and the status of points 485, 504, 568.
# Run    : cd WD ; python3 regions2.py      (Anaconda python3; relative paths: the working directory MUST be WD)
# One region point per face of the final planar graph (breaklines + nodestrings + sections).
# Keep: original point (fid<=176) if >= 1 m from every line, else the lowest-fid point >= 1 m; otherwise a new point
# at the pole of inaccessibility with the attributes of the original region the face comes from.
import json, pickle, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union, polylabel
# F = new breaklines (>=2 vertices), secs = new sections, bd = boundary
F={int(k):v for k,v in json.load(open('fix5.json'))['F'].items() if len(v)>=2}
secs=json.load(open('secs_new.json')); bd=gpd.read_file('in/boundary_50m.gpkg',fid_as_index=True)
# NS = non-section nodestrings (old-style names S/V + 5 digits excluded)
NS=[LineString(shapely.get_coordinates(g)) for n,g in zip(bd.nome,bd.geometry) if not(n[0] in 'SV' and n[1:6].isdigit())]
# L = all lines; U = their union; fc = faces of the planar graph (polygonize); A = areas
L=[LineString(c) for c in F.values()]+NS+[LineString(s['coords']) for s in secs]
U=unary_union(L); fc=list(polygonize(U)); A=np.array([f.area for f in fc]); print('faces',len(fc),'area<1 m2',int((A<1).sum()),sorted(A)[:5])
# r = current region points (in/), r0 = original ones (in0/)
r=gpd.read_file('in/regioni_ponti_50m.gpkg',fid_as_index=True); r0=gpd.read_file('in0/regioni_ponti.gpkg',fid_as_index=True)
# NF['fc'] = base faces; b0[face] = original region points (r0) lying in each base face
NF=pickle.load(open('work/newfaces.pkl','rb')); base=NF['fc']; TB=shapely.STRtree(base)
b0=collections.defaultdict(list)
for p,f in zip(*TB.query(r0.geometry.values,predicate='within')): b0[int(f)].append(int(r0.index[p]))
# rg = region points with a geometry; infc[face] = region points inside each new face
rg=r[r.geometry.notna()]; T=shapely.STRtree(fc); infc=collections.defaultdict(list)
for p,f in zip(*T.query(rg.geometry.values,predicate='within')): infc[int(f)].append(int(rg.index[p]))
# clear[fid] = distance of the region point from the nearest line
clear=dict(zip(rg.index,shapely.distance(U,rg.geometry.values)))
# keep/drop/new = result lists; errs = faces for which no source region was found
keep=[]; drop=[]; new=[]; errs=[]
# loop over the faces; ps = points inside, originals (<=176) first
for i,f in enumerate(fc):
    ps=sorted(infc.get(i,[]),key=lambda q:(q>176,q))
    # face with 57 and 58: kept as it is
    if set(ps)>={57,58}:            # face with two points already in the original data: left as it is
        keep+=[q for q in ps if q in (57,58)]; drop+=[q for q in ps if q not in (57,58)]; continue
    # good = points at >= 1 m from every line: keep the first, drop the others
    good=[q for q in ps if clear[q]>=1.0]
    if good:
        keep.append(good[0]); drop+=[q for q in ps if q!=good[0]]; continue
    # narrow face: never replace an original point; keep the one with the largest clearance
    orig_in=[q for q in ps if q<=176]
    if orig_in:                     # narrow face: an original point is never replaced
        best=max(orig_in,key=lambda q:clear[q]); keep.append(best); drop+=[q for q in ps if q!=best]; continue
    # new point at the pole of inaccessibility; c = its clearance; if an existing point is at least as clear, keep that one
    pt=polylabel(f,tolerance=0.02); c=float(pt.distance(U))
    if ps and max(clear[q] for q in ps)>=c-1e-6:
        best=max(ps,key=lambda q:clear[q]); keep.append(best); drop+=[q for q in ps if q!=best]; continue
    # src = region the attributes are copied from: the original region of the base face containing pt, else the first point inside
    src=None
    idx=TB.query(pt,predicate='within')
    if len(idx) and b0.get(int(idx[0])): src=r0.loc[b0[int(idx[0])][0]]
    elif ps: src=r.loc[ps[0]]
    if src is None: errs.append((i,round(A[i],2))); continue
    # no suitable existing point: drop the ones inside and create the new one
    drop+=ps
    new.append(dict(face=i,x=pt.x,y=pt.y,nome=src.nome,mat_id=int(src.mat_id),max_area=float(src.max_area),buco=None if src.buco!=src.buco or src.buco is None else int(src.buco),clear=c))
# reports
print('kept',len(keep),'dropped',len(drop),'new',len(new),'errors',errs)
print('dropped list',sorted(drop)); print('new clearance <1 m',[(round(p['clear'],2),p['nome']) for p in new if p['clear']<1])
print('kept with clearance <1 m',[(q,r.at[q,'nome'],round(clear[q],2)) for q in keep if clear[q]<1])
print('new by name',collections.Counter(p['nome'] for p in new))
print('dropped detail',[(q,r.at[q,'nome'],round(clear[q],2)) for q in sorted(drop)])
for q in (485,504,568): print(q,'kept' if q in keep else ('dropped' if q in drop else 'n/a'), round(clear[q],2))
# save
json.dump(dict(keep=keep,drop=sorted(drop),new=new,nfaces=len(fc)),open('regions2.json','w'))
