# apply_widen.py - step 8. Applies the result of widen.py to the whole breakline set: propagates the moved end points to the lines
# that touch them, slides ends onto unmoved lines, extends/moves boundary-line ends, and validates the new planar graph (simple lines, faces, region points per face).
# Inputs : WD/work/chains.pkl (chains.py); WD/work/widen.pkl (widen.py); WD/in/boundary.gpkg; WD/in/regioni_ponti.gpkg
# Outputs: WD/work/widen2.pkl (dict newf: fid -> new vertices for ALL changed breaklines, endmap: old end (x,y rounded to mm) -> new end);
#          WD/work/bgn.pkl (dict boundary fid -> new vertices, only changed boundaries); WD/work/widen_faces.pkl (dict fc, A: validation faces and areas); diagnostics on stdout
# Usage  : python3 apply_widen.py WD      (Anaconda python3; core.py in WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from scipy.spatial import cKDTree
from shapely.ops import unary_union, polygonize
# C = chains.pkl; W = widen.pkl
C=pickle.load(open(f'{SP}/work/chains.pkl','rb')); W=pickle.load(open(f'{SP}/work/widen.pkl','rb'))
# feat: original geometry; newf: new geometry of the moved top features; PTS/SH/DN loaded (kd unused afterwards)
feat=C['feat']; newf=dict(W['newf']); PTS,SH,DN=W['PTS'],W['SH'],W['DN']; kd=cKDTree(PTS)
# old/new end map from moved top features
# endmap: old end (x,y rounded to 1 mm) -> new end coordinates, for moved top features
endmap={}
for fid,b in newf.items():
    a=feat[fid]
    for old,new in ((a[0],b[0]),(a[-1],b[-1])):
        endmap[(round(old[0],3),round(old[1],3))]=new
print('moved ends',len(endmap))
# add the forced T points (endT from widen.py)
endmap.update(W['endT'])
# moved = ends displaced by more than 1 mm
moved=[k for k,v in endmap.items() if np.hypot(k[0]-v[0],k[1]-v[1])>1e-3]; print('ends really moved',len(moved))
# other features whose end coincides with a moved end: move the end accordingly
# tk = fids already moved; nfix = counter; lst = (fid, end) list
tk=set(newf); nfix=0; lst=[]
for fid,a in feat.items():
    if fid in tk: continue
    b=a.copy(); ch=False
    for e in (0,-1):
        k=(round(a[e][0],3),round(a[e][1],3))
        if k in endmap and np.hypot(*(endmap[k]-a[e]))>1e-6:
            b[e]=endmap[k]; ch=True; lst.append((fid,e))
    if ch: newf[fid]=b; nfix+=1
print('dependent features moved at ends',nfix,lst[:30])
# old = original LineStrings; to = their STRtree
keys=list(feat); old=[LineString(feat[k]) for k in keys]; to=shapely.STRtree(old)
# ends slid onto unmoved lines: a moved feature whose old end lay on another line that is NOT moved gets its new end projected onto that old line, so it remains connected
slid=[]
for i,k in enumerate(keys):
    if k not in newf: continue
    b=newf[k].copy(); ch=False
    for e in (0,-1):
        if np.hypot(*(b[e]-feat[k][e]))<1e-6: continue
        for j in to.query(Point(feat[k][e]),predicate='dwithin',distance=1e-3):
            k2=keys[j]
            if k2==k: continue
            if k2 not in newf and (np.hypot(*(feat[k2][0]-feat[k][e]))>1e-3 and np.hypot(*(feat[k2][-1]-feat[k][e]))>1e-3 or k2 not in newf):
                l2=old[j]; q=shapely.get_coordinates(l2.interpolate(l2.project(Point(b[e]))))[0]; slid.append((k,e,k2,round(float(np.hypot(*(q-b[e]))),3))); b[e]=q; ch=True; break
    if ch: newf[k]=b
print('ends slid onto unmoved lines',slid)
# save newf (all changed features) and endmap
pickle.dump(dict(newf=newf,endmap=endmap),open(f'{SP}/work/widen2.pkl','wb'))
# ===== validation graph
# bd, bdf = boundary lines; r = region points
bd=gpd.read_file(f'{SP}/in/boundary.gpkg'); r=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True)
# L = new geometry of every breakline
L=[LineString(newf.get(f,a)) for f,a in feat.items()]
# bgn: boundary fid -> new vertices (only for boundaries whose end moved)
bgn={}
bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True)
# moves: (name, end, displacement m) of boundary ends that were extended to the moved top line
moves=[]
# boundary-line ends coupled to a moved top line (tag 'bd')
for tag,new in W['bmove'].items():
    if tag[0]!='bd': continue
    _,k,e=tag
    b=bgn.get(k,W['bgeo'][k].copy()); 
    if np.hypot(*(b[e]-new))>1e-6: moves.append((bdf.nome[k],e,round(float(np.hypot(*(b[e]-new))),2)))
    b[e]=new; bgn[k]=b
print('boundary ends extended',moves)
# save bgn
pickle.dump(bgn,open(f'{SP}/work/bgn.pkl','wb'))
# bg = boundary lines (new where changed)
bg=[LineString(bgn.get(k,W['bgeo'][k])) for k in W['bgeo']]
# checks: number of non-simple (self-intersecting) new lines and, for comparison, in the original
print('simple?',sum(not l.is_simple for l in L),[f for f,l in zip(feat,L) if not l.is_simple][:20])
print('non-simple orig',sum(not LineString(a).is_simple for a in feat.values()))
# new planar graph: union, polygonize; number of faces and of faces <1 m2
u=unary_union(L+bg); fc=list(polygonize(u)); A=np.array([f.area for f in fc]); print('faces',len(fc),'small<1',(A<1).sum())
# region points per face: expect exactly one per named face
t=shapely.STRtree(fc); ix=t.query(r.geometry.values,predicate='within'); pts=np.bincount(ix[1],minlength=len(fc))
print('faces per npoints',dict(zip(*np.unique(pts,return_counts=True))),'pts in face',len(set(ix[0])),'of',len(r))
# faces without region point (area, centroid), top 20 by area
nop=[(round(A[i],2),[int(c) for c in fc[i].centroid.coords[0]]) for i in np.where(pts==0)[0]]; print('no point faces',sorted(nop,key=lambda x:-x[0])[:20])
# faces with >=2 region points (area, ids of the points)
two=[(i,list(ix[0][ix[1]==i])) for i in np.where(pts>=2)[0]]; print('multi',[(round(A[i],1),[int(r.index[p]) for p in ps]) for i,ps in two])
# save validation faces
pickle.dump(dict(fc=fc,A=A),open(f'{SP}/work/widen_faces.pkl','wb'))
