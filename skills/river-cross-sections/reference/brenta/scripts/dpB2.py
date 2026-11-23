# dpB2.py  (stage 3, 2026-11-18; previous: dpB.py, next: export_B.py WD dpB2.pkl)
# Purpose: shift the B reach (Brenta downstream of Borgo) upstream so that section number ANCHOR_K (B00400) coincides exactly with the
#          nodestring ANCHOR_NAME (idrometro_Borgo). The shift D = s(old B00400) - s(anchor) (about 16.6 m) is applied to every B section:
#          section k gets the target chainage t_k = s_old_k - D and is chosen among the main-stream candidates of cands.pkl within
#          +-WIN m of the target by a layered dynamic programming (one layer per section), with the same rules as dpB.py:
#          consecutive sections 49.5-50.5 m apart along the chainage s (hard) and as chord between centre points (soft, 500+100*|ch-50|), candidate penalties
#          pen5/hitO/hitB, +50 for a toe crossing < 5 m from a nodestring/breakline crossing point, no section in (S_BRIDGE-MARGIN, S_BRIDGE+20) m
#          (Ponte_Bordignon_monte), plus W_DEV per metre of distance from the target. The number of sections does not change: with ADD_END=True
#          one section would be added at the end when the last one is more than 50.5 m from the end of the chainage (not used: on the Brenta
#          that section falls 12 m from BC_brenta_valle, rotated, with the right bankpoint on the domain boundary).
# Inputs : WD/work/cands.pkl (place.py), WD/work/dpB.pkl (dpB.py; old placement, key B, and N/V indices copied unchanged), WD/xn_points.json
#          (prep_inputs_nvb.py), boundary file with the anchor nodestring = argv[2] (e.g. WD/in/boundary_50m.gpkg), WD/work/core.py (SP = argv[1]).
# Output : WD/work/dpB2.pkl = dict(N, B, V, anchor). B = candidate indices of the B reach (the anchor slot holds the nearest candidate,
#          only as a placeholder); anchor = dict(k, nome, s, x, y, nx, ny, tL, tR, coords): position k in B, nodestring name, chainage and
#          centre point (intersection with the polyline of the candidate centre points), unit normal towards the left end, distances of the
#          two ends from the centre and the nodestring vertices (left end first). Prints a summary.
# Run    : python3 dpB2.py WD WD/in/boundary_50m.gpkg      (Anaconda python3)
# Units  : metres; ss = chainage along the asta principale, step 0.25 m between candidates.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json, geopandas as gpd, shapely
from shapely.geometry import LineString
from scipy.spatial import cKDTree
# C = candidates per stream; D0 = old dpB result
C=pickle.load(open(f'{SP}/work/cands.pkl','rb')); D0=pickle.load(open(f'{SP}/work/dpB.pkl','rb'))
c=C['main']; ss,P,ok=c['ss'],c['P'],c['ok']; N=len(ss)
# S_BRIDGE/MARGIN as in dpB.py; ANCHOR_K = index of the forced section (B00400); WIN = search window around each target; W_DEV = cost per metre off target
S_BRIDGE=16327.97; MARGIN=5.0; ANCHOR_K=8; ANCHOR_NAME='idrometro_Borgo'; WIN=5.0; W_DEV=0.5; ADD_END=False
# candidate penalty, as in dpB.py
pen=c['pen5'].copy()+1000*c['hitO']+10000*c['hitB']; pen[~ok]=1e9
XN=np.array(json.load(open(f'{SP}/xn_points.json'))); kx=cKDTree(XN)
for tk,sg in (('tL',1),('tR',-1)):
    q=P+sg*c['n']*np.nan_to_num(c[tk])[:,None]; dd,_=kx.query(q); pen+=50*((dd<5.0)&np.isfinite(c[tk]))
pen[(ss>S_BRIDGE-MARGIN)&(ss<S_BRIDGE+20)]=1e9
# anchor: the nodestring (2 vertices); its intersection with the polyline of the candidate centre points gives s_a and the centre point Pa
b=gpd.read_file(sys.argv[2]); g=b[b.nome==ANCHOR_NAME].geometry.iloc[0]; A=shapely.get_coordinates(g)
assert len(A)==2, 'anchor nodestring must have 2 vertices'
cl=LineString(P); x=g.intersection(cl); assert x.geom_type=='Point', x.geom_type
s_a=float(ss[0]+cl.project(x)); Pa=np.array([x.x,x.y])
# left end first: the candidate normal n points to the left bank
ia=int(np.argmin(np.abs(ss-s_a))); na=c['n'][ia]
if np.dot(A[0]-Pa,na)<np.dot(A[1]-Pa,na): A=A[::-1]
u=(A[0]-A[1])/np.linalg.norm(A[0]-A[1])
tL=float(np.dot(A[0]-Pa,u)); tR=float(np.dot(Pa-A[1],u))
# targets: old chainages minus the shift D; optionally add one section at the end if the last one is now too far from the end
s_old=ss[np.array(D0['B'])]; D=float(s_old[ANCHOR_K]-s_a); T=list(s_old-D); T[ANCHOR_K]=s_a
Lend=ss[-1]+0.25
if ADD_END and Lend-T[-1]>50.5: T.append(T[-1]+50.0)
K=len(T)
# layer k: candidate list (the anchor layer has only the virtual node -1); node chainage/point helpers
def sP(i): return (s_a,Pa) if i==-1 else (ss[i],P[i])
layers=[]
for k,t in enumerate(T):
    if k==ANCHOR_K: layers.append([-1]); continue
    j=np.where((np.abs(ss-t)<=WIN)&(pen<1e9))[0]
    if ADD_END and k==K-1: j=j[(ss[j]>=Lend-50.5)&(ss[j]<=Lend-5)]
    assert len(j), f'no candidate for section {k}'
    layers.append([int(i) for i in j])
# node cost and step cost (as dpB.py: the 49.5-50.5 m chainage window is a hard limit; a chord outside 49.5-50.5 m costs 500+100*|ch-50|,
# because the rule is 50 +- 0.5 m along the centre line and in tight bends the straight-line distance can be shorter)
def ncost(k,i): return 0.0 if i==-1 else pen[i]+W_DEV*abs(ss[i]-T[k])
def scost(i,j):
    (s0,p0),(s1,p1)=sP(i),sP(j); ds=s1-s0; ch=float(np.hypot(*(p1-p0)))
    if not (49.5-1e-6<=ds<=50.5+1e-6): return np.inf
    return 0.01*(ds-50)**2+(0 if 49.5<=ch<=50.5 else 500+100*abs(ch-50))
# forward layered DP
cost=[{i:ncost(0,i) for i in layers[0]}]; back=[{}]
for k in range(1,K):
    cc={}; bb={}
    for j in layers[k]:
        best=np.inf; arg=None
        for i,ci in cost[-1].items():
            v=ci+scost(i,j)
            if v<best: best=v; arg=i
        if np.isfinite(best): cc[j]=best+ncost(k,j); bb[j]=arg
    assert cc, f'no feasible path at section {k}'
    cost.append(cc); back.append(bb)
j=min(cost[-1],key=cost[-1].get); p=[j]
for k in range(K-1,0,-1): j=back[k][j]; p.append(j)
p=p[::-1]; p[ANCHOR_K]=ia; p=np.array(p)
s=ss[p].copy(); s[ANCHOR_K]=s_a; Pc=P[p].copy(); Pc[ANCHOR_K]=Pa
ch=np.hypot(*np.diff(Pc,axis=0).T); ds=np.diff(s); dev=s-np.array(T)
print('anchor',ANCHOR_NAME,'end distance',round(Lend-T[-1],2),'s',round(s_a,2),'shift D',round(D,2),'length',round(tL+tR,2),'B n',K,'(old',len(s_old),') first',s[:3].round(2),'last',s[-1],'L',Lend)
print('step',ds.min().round(2),ds.max().round(2),'chord',ch.min().round(2),ch.max().round(2),'deviation from target',dev.min().round(2),dev.max().round(2),'n off target',int((np.abs(dev)>0.13).sum()))
print('chord outside 49.5-50.5 (section, chord)',[(f'B{k*50:05d}',round(float(e),2)) for k,e in enumerate(ch) if not 49.5<=e<=50.5])
print('off target > 0.13 m (section, deviation)',[(f'B{k*50:05d}',round(float(e),2)) for k,e in enumerate(dev) if abs(e)>0.13])
q=np.delete(p,ANCHOR_K)
print('hitB',int(c['hitB'][q].sum()),'hitO',int(c['hitO'][q].sum()),'pen5 sum',float(c['pen5'][q].sum()),'pen>=1e9',int((pen[q]>=1e9).sum()))
anchor=dict(k=ANCHOR_K,nome=ANCHOR_NAME,s=s_a,x=float(Pa[0]),y=float(Pa[1]),nx=float(u[0]),ny=float(u[1]),tL=tL,tR=tR,coords=A.tolist())
pickle.dump(dict(N=D0['N'],B=p,V=D0['V'],anchor=anchor),open(f'{SP}/work/dpB2.pkl','wb'))
