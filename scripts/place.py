# place.py - step 10. Generates candidate section positions every 0.25 m along the two centerlines and evaluates them: toe/top distances, 5 m rule on toe vertices,
# crossings with boundary lines and with inner breaklines. The choice of the 50 m stations is made by dp.py.
# Inputs : WD/work/cltab.pkl (cl2.py, centerline q), WD/work/widen2.pkl (apply_widen.py), WD/work/chains.pkl (chains.py), WD/work/bgn.pkl (apply_widen.py);
#          WD/in/boundary.gpkg, WD/in/regioni_ponti.gpkg
# Outputs: WD/work/newfaces.pkl (dict fc: faces of the widened planar graph, rows: [{face, nome}]); WD/work/cands.pkl (dict main/vecchio -> candidate arrays, see below); diagnostics on stdout
# Usage  : python3 place.py WD      (Anaconda python3; core.py in WD/work)
# cands.pkl[name] keys, all arrays aligned per candidate: ss (s in m, step 0.25), P (xy on centerline), n (left unit normal), tL,tR (centerline->toe, + and - side, m),
# cL,cR (centerline->top, m), pen5 (0..2: toe crossings closer than 5 m to a toe vertex), hitB (1 if the approximate section crosses a boundary line),
# hitO (1 if it crosses an inner breakline), ok (valid: toe and top found on both sides).
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from scipy.spatial import cKDTree
from shapely.ops import unary_union, polygonize
# T0 cltab; W2 widen2; C chains; bgn new boundary geometries (changed ones)
T0=pickle.load(open(f'{SP}/work/cltab.pkl','rb')); W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb')); C=pickle.load(open(f'{SP}/work/chains.pkl','rb')); bgn=pickle.load(open(f'{SP}/work/bgn.pkl','rb'))
# feat: original breaklines; newf: widened ones
feat=C['feat']; newf=W2['newf']
bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True); r=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True)
# bgeo: boundary fid -> vertices (new if changed in bgn, else original)
bgeo={k:bgn.get(k,shapely.get_coordinates(next(iter(shapely.get_parts(g))))) for k,g in bdf.geometry.items()}
# new planar graph (breaklines new + boundary new): faces carrying class
# L = all lines; u = union; fc = faces; t = STRtree; ix = region points inside faces
L=[LineString(newf.get(f,a)) for f,a in feat.items()]+[LineString(a) for a in bgeo.values()]
u=unary_union(L); fc=list(polygonize(u)); t=shapely.STRtree(fc); ix=t.query(r.geometry.values,predicate='within')
# rows: one per face containing region points; later points on the same face are discarded (the first one gives the name)
rows=[]
for p,f in zip(*ix): rows.append(dict(face=int(f),nome=r.nome.iloc[int(p)]))
seen=set(); rows=[x for x in rows if not (x['face'] in seen or seen.add(x['face']))]; print('faces',len(fc),'named',len(rows))
# save new faces for later scripts
pickle.dump(dict(fc=fc,rows=rows),open(f'{SP}/work/newfaces.pkl','wb'))
# tb = toe segments, tc = top segments of the NEW graph; ray objects Rb/Rc
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(fc,rows,lambda n: cls(n) in('bed','sponda','muro'))
Rb,Rc=Rays(tb),Rays(tc)
# vertices on toe lines for 5 m rule
# tb_keys: canonical keys of toe segments
tb_keys={key(s) for s in tb}
# toev: dead code (evaluates to None)
toev=np.array(sorted({tuple(p) for f,a in feat.items() for p in newf.get(f,a).round(4) if False})) if False else None
# vtx: vertices of every breakline that contains at least one toe segment; vk = KD-tree. Used for the '5 m' rule: the section must cross the toe >=5 m from a vertex of the toe line
vtx=[]
for f,a in feat.items():
    a2=newf.get(f,a)
    S=np.c_[a2[:-1],a2[1:]]
    if any(key(s) in tb_keys for s in S): vtx.append(a2)
vtx=np.vstack(vtx); vk=cKDTree(vtx); print('toe vertices',len(vtx))
# obstacle lines: everything except toe & top lines → cross-lines, nodestrings, buildings
# obs: built but not used afterwards
obs=[]
for f,a in feat.items():
    a2=newf.get(f,a); S=np.c_[a2[:-1],a2[1:]]
    keep=[s for s in S if key(s) not in tb_keys]
    if keep: obs.append(LineString(a2))
# oblines: boundary lines (nodestrings) as obstacles; OT = their STRtree
oblines=[LineString(a) for a in bgeo.values()]
OT=shapely.STRtree(oblines)
# tops: canonical keys of top-of-bank segments (tc)
tops={key(s) for s in tc}
# OT2: single segments of breaklines that are neither toe nor top (inner breaklines: cross-lines, buildings); OTB = STRtree
OT2=[]
for f,a in feat.items():
    a2=newf.get(f,a)
    for s in np.c_[a2[:-1],a2[1:]]:
        k=key(s)
        if k not in tb_keys and k not in tops: OT2.append(LineString(s.reshape(2,2)))
OTB=shapely.STRtree(OT2); print('obstacles: boundary',len(oblines),'inner bl',len(OT2))
# GR = candidate spacing along the centerline (m): 0.25 m
GR=0.25
# cand(q,step): chainages ss (every 0.25 m), points P, and left normals n computed from the chord s-1..s+1 m
def cand(q,step=GR):
    l=LineString(q); ss=np.arange(0,l.length,step); P=shapely.get_coordinates(shapely.line_interpolate_point(l,ss))
    A=shapely.get_coordinates(shapely.line_interpolate_point(l,np.maximum(ss-1,0))); B=shapely.get_coordinates(shapely.line_interpolate_point(l,np.minimum(ss+1,l.length)))
    d=(B-A)/np.hypot(*(B-A).T)[:,None]; n=np.c_[-d[:,1],d[:,0]]
    return ss,P,n
# eval_cand(ss,P,n): for each candidate, distances to toe (tL,tR) and to the first top line beyond the toe (cL,cR) on each side, from ray hits +-1500 m; NaN if absent. Columns 4,5 unused
def eval_cand(ss,P,n):
    N=len(ss); res=np.full((N,6),np.nan); 
    for i in range(N):
        hb=Rb.hits(P[i],n[i],1500); hc=Rc.hits(P[i],n[i],1500)
        if len(hb)==0 or not(hb>0).any() or not(hb<0).any(): continue
        tL=hb[hb>0].min(); tR=-hb[hb<0].max()
        cc1=hc[hc>tL-1e-6]; cc2=hc[hc<-tR+1e-6]
        if not len(cc1) or not len(cc2): continue
        res[i]=[tL,tR,cc1.min(),-cc2.max(),0,0]
    return res
# per centerline ('main' and 'vecchio')
out={}
for name in('main','vecchio'):
    # q = centerline (1 m step); candidates every 0.25 m
    q=T0[name]['q']; ss,P,n=cand(q); res=eval_cand(ss,P,n)
    # ok = candidates with finite tL (valid: toe and top found on both sides)
    tL,tR,cL,cR=res[:,:4].T; ok=np.isfinite(tL)
    # 5 m rule: 2 toe crossings
    pen5=np.zeros(len(ss))
    # for each side the crossing point on the toe line; d = distances to its 2 nearest toe vertices;
    # v = True if the crossing is within 5 m of a vertex (if a vertex coincides with it, d<=1 mm, the next vertex is used); pen5 = number of sides violating (0..2)
    for sgn,tt in ((1,tL),(-1,tR)):
        p=P+n*(sgn*tt[:,None]); m=np.isfinite(p[:,0])
        d,_=vk.query(p[m],k=2)
        v=((d[:,0]>1e-3)&(d[:,0]<5))|((d[:,0]<=1e-3)&(d[:,1]<5)); a=np.zeros(len(ss)); a[m]=v.astype(float); pen5+=a
    # approximate section extents for crossing test
    # ext(c,t): half-extent of the section: toe + 15 m, but not beyond 5 m inside the top line
    ext=lambda c,t: np.minimum(t+15,c-5)
    # eL/eR: when the section is wide (>30 m) use ext; otherwise cap at toe+0.5 m at least (top-5 m). Note: eL tests tL+cR>30 while eR tests tL+tR>30 (asymmetric as written)
    eL=np.where(tL+cR>30,ext(cL,tL),np.minimum(ext(cL,tL),np.maximum(tL+0.5,cL-5)))
    eR=np.where(tL+tR>30,ext(cR,tR),np.minimum(ext(cR,tR),np.maximum(tR+0.5,cR-5)))
    # pts0/pts1 = approximate section end points; ln = the approximate section segments
    pts0=P+n*np.nan_to_num(eL,0)[:,None]; pts1=P-n*np.nan_to_num(eR,0)[:,None]
    # ln = approximate section segments (centre-eL .. centre+eR)
    ln=shapely.linestrings(np.stack([pts0,pts1],axis=1))
    # hitB = 1 if the approximate section intersects a boundary line (nodestring)
    i0,i1=OT.query(ln,predicate='intersects'); hitB=np.zeros(len(ss)); hitB[np.unique(i0)]=1
    # hitO = 1 if it intersects an inner breakline
    j0,j1=OTB.query(ln,predicate='intersects'); hitO=np.zeros(len(ss)); hitO[np.unique(j0)]=1
    # prints number of candidates, valid ones, and counts of those hitting boundary / inner lines / violating the 5 m rule
    print(name,'cands',len(ss),'valid',int(ok.sum()),'hit bd',int(hitB[ok].sum()),'hit inner',int(hitO[ok].sum()),'pen5>0',int((pen5[ok]>0).sum()))
    # store arrays for the DP
    out[name]=dict(ss=ss,P=P,n=n,tL=tL,tR=tR,cL=cL,cR=cR,pen5=pen5,hitB=hitB,hitO=hitO,ok=ok)
# save candidates
pickle.dump(out,open(f'{SP}/work/cands.pkl','wb'))
