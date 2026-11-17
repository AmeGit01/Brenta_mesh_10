# graph.py - step 1 of the pipeline. Builds the planar graph of the breaklines + boundary lines and the faces it encloses,
# assigns to each face the name/material of the region point (regioni_ponti) lying inside it, and prints diagnostics.
# Inputs : WD/in/breaklines.gpkg, WD/in/boundary.gpkg, WD/in/regioni_ponti.gpkg
# Outputs: WD/work/graph.pkl  (dict faces, fr, rows); diagnostics are printed on stdout
# Usage  : python3 graph.py WD      (Anaconda python3; geopandas, shapely, numpy)
import geopandas as gpd, numpy as np, shapely, pickle, sys
from shapely.ops import polygonize, unary_union
from shapely.geometry import LineString
# SP = working directory WD
SP=sys.argv[1]
# b = breaklines, bd = boundary lines, r = region points (fid_as_index keeps the GPKG fid as the DataFrame index)
b=gpd.read_file(f'{SP}/in/breaklines.gpkg',fid_as_index=True); bd=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True); r=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True)
# diagnostic: number of breaklines, empty/null geometries, histogram of number of parts per geometry
print('bl',len(b),'empty',int((b.geometry.is_empty|b.geometry.isna()).sum()),'parts',b.geometry.dropna().apply(lambda g: len(g.geoms) if g.geom_type.startswith('Multi') else 1).value_counts().to_dict())
# drop empty/null breaklines
b=b[~(b.geometry.is_empty|b.geometry.isna())]
# lines(s): explode every (multi)geometry of GeoSeries s into plain 2D LineStrings (drops Z/M)
def lines(s):
    out=[]
    for g in s.geometry:
        out+=[LineString(np.asarray(shapely.get_coordinates(p))) for p in shapely.get_parts(g)]
    return out
# the loop over tolerances has a single entry (0,'exact'): the tolerance value is unused, lines are noded exactly
for tol,name in [(0,'exact')]:
    # all breaklines + boundary lines
    L=lines(b)+lines(bd)
    # unary_union nodes the lines at their intersections; polygonize then builds the faces enclosed by the noded line network
    u=unary_union(L)
    faces=list(polygonize(u)); 
    print(name,'faces',len(faces))
# A = face areas (m2); prints number of faces with area <1e-3 m2 and <1 m2, and total area in km2 (A.sum()/1e6)
A=np.array([f.area for f in faces]); print('area small',(A<1e-3).sum(),(A<1).sum(), A.sum()/1e6)
# spatial index of the faces; assign each region point to the face that contains it
t=shapely.STRtree(faces)
ix=t.query(r.geometry.values,predicate='within')
# ix[0] = point index, ix[1] = face index; check how many region points fall inside a face
print('points in faces',len(set(ix[0])),'of',len(r))
# pts = number of region points per face; prints how many faces have 0,1,2.. points
pts=np.bincount(ix[1],minlength=len(faces)); print('faces per npoints',np.unique(pts,return_counts=True))
# faces larger than 1 m2 with no region point (face index, area), 15 largest printed
big0=[(i,A[i]) for i in np.where(pts==0)[0] if A[i]>1]
print('faces>1m2 w/o point',len(big0),sorted(big0,key=lambda x:-x[1])[:15])
# indices (fid) of region points lying in no face
pts_out=[int(f) for k,f in enumerate(r.index) if k not in set(ix[0])]; print('pts outside',pts_out)
# fr: face index -> list of region-point positions inside it
fr={}
for p,f in zip(*ix):
    fr.setdefault(int(f),[]).append(int(p))
# cols: region table with fid as a column; rows: one dict per face that has a point: fid list of its points, nome and mat_id of the FIRST point, area (m2)
cols=r.reset_index()
rows=[]
for f,ps in fr.items():
    rows.append(dict(face=f,fid=[int(cols.fid[p]) for p in ps],nome=cols.nome[ps[0]],mat=int(cols.mat_id[ps[0]]),area=A[f]))
# write graph.pkl: faces (list of Polygons), fr (face -> point positions), rows
pickle.dump(dict(faces=faces,fr=fr,rows=rows),open(f'{SP}/work/graph.pkl','wb'))
import collections
# summary: for each region name, number of faces and total area in hectares (sorted by area, descending)
agg=collections.defaultdict(lambda:[0,0.0])
for x in rows:
    agg[x['nome']][0]+=1; agg[x['nome']][1]+=x['area']
for k,v in sorted(agg.items(),key=lambda kv:-kv[1][1]): print(f'{k:35s} {v[0]:4d} {v[1]/1e4:10.1f} ha')
