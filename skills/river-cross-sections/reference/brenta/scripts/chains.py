# chains.py - step 6. Classifies every segment of every breakline by the face classes on its left and right, to find which breaklines are
# 'top of bank' lines (cigli) that widen.py may move.
# Inputs : WD/work/graph.pkl (core.load_graph); WD/in/breaklines.gpkg
# Outputs: WD/work/chains.pkl (dict feat, S, meta, L, R, Lc, Rc, istop) read by widen.py, apply_widen.py, gaps.py, place.py (and later scripts); diagnostics on stdout
# Usage  : python3 chains.py WD      (Anaconda python3; core.py in WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
# faces and rows (faces with a region point) from graph.pkl
faces,rows=load_graph()
# fname: face index -> region name
fname={r['face']:r['nome'] for r in rows}
# tree = spatial index of the faces (for point-in-face tests)
tree=shapely.STRtree(faces)
# breaklines (fid = GPKG feature id), empty geometries removed
bl=gpd.read_file(f'{SP}/in/breaklines.gpkg',fid_as_index=True); bl=bl[~(bl.geometry.is_empty|bl.geometry.isna())]
# feat: fid -> vertex array (first part only); segs/meta: all non-degenerate segments (>1e-6 m) as [x0,y0,x1,y1] with (fid, segment index)
feat={}; segs=[]; meta=[]
for fid,g in bl.geometry.items():
    a=shapely.get_coordinates(next(iter(shapely.get_parts(g))))
    feat[fid]=a
    for i in range(len(a)-1):
        if np.hypot(*(a[i+1]-a[i]))>1e-6: segs.append(np.r_[a[i],a[i+1]]); meta.append((fid,i))
# S = segments (N,4); M = segment midpoints (computed here but not used afterwards, mid below is the one used)
S=np.array(segs); M=np.array([(a[0]+a[2])/2 for a in S.reshape(-1,4) for a in [[a[0],a[1],a[2],a[3]]]])
# d = segment vector; n = unit LEFT normal of each segment (relative to the vertex order of the line); mid = midpoints
d=S[:,2:]-S[:,:2]; n=np.c_[-d[:,1],d[:,0]]/np.hypot(*d.T)[:,None]
mid=(S[:,:2]+S[:,2:])/2
# loc(pts): name of the face containing each point; 'outside' if in no face, 'noname' if the face has no region point
def loc(pts):
    idx=tree.query(shapely.points(pts),predicate='within'); out=np.array(['outside']*len(pts),dtype=object)
    for p,f in zip(*idx): out[p]=fname.get(int(f),'noname')
    return out
# L / R = name of the face 2 cm to the left / right of each segment (midpoint +-0.02 m * normal)
L=loc(mid+n*0.02); R=loc(mid-n*0.02)
# cl: map names to classes (cls from core); Lc/Rc = class of left/right face (or 'outside'/'noname')
cl=lambda a:np.array([cls(x) if x not in('outside','noname') else x for x in a],dtype=object)
Lc,Rc=cl(L),cl(R)
# histogram of (class,class) pairs across segments, most common first
T=collections.Counter(tuple(sorted((a,b))) for a,b in zip(Lc,Rc)); print(T.most_common())
# istop[k] = True when the segment separates a bank face from an intermedio or flood face: it is a top-of-bank line
istop=np.array([ {a,b} in ({'sponda','inter'},{'sponda','flood'}) for a,b in zip(Lc,Rc)])
# tm: fid -> list of istop flags of its segments
tm={}
for (fid,i),t in zip(meta,istop): tm.setdefault(fid,[]).append(t)
# counts features entirely made of top segments / only partly (mixed); widen.py skips the mixed ones
print('feat all top',sum(all(v) for v in tm.values()),'some',sum(any(v) and not all(v) for v in tm.values()))
# list (max 20) of mixed features
print('mixed feats sample',[k for k,v in tm.items() if any(v) and not all(v)][:20])
# features touching a 'sponda_antro' (urban/anthropic bank) face: these are not moved by widen.py
antro=[fid for (fid,i),a,b in zip(meta,L,R) if (a=='sponda_antro' or b=='sponda_antro')]
# number of features touching sponda_antro
print('touching sponda_antro feats',len(set(antro)))
# save: feat (fid->xy), S (segments), meta ((fid,i) per segment), L/R names, Lc/Rc classes, istop flags (aligned with S/meta)
pickle.dump(dict(feat=feat,S=S,meta=meta,L=L,R=R,Lc=Lc,Rc=Rc,istop=istop),open(f'{SP}/work/chains.pkl','wb'))
