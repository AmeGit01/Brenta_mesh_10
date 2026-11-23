# dpB.py  (stage 2, 2026-11-17; replaces the B part of dp.py; previous: dp.py/place.py, next: export_B.py)
# Purpose: re-place the B reach (Brenta downstream of Borgo, i.e. the asta principale after the bridge junction) on the main-stream
#          candidates of cands.pkl by dynamic programming: sections ~50 m apart (step 49.5-50.5 m along s and 49.5-50.5 m chord).
#          Constraints: first section (B00000) with s in [S0MIN,S0MAX] on the OLD asta chainage; B00050 at least MARGIN=5 m upstream of
#          Ponte_Bordignon_monte (s=S_BRIDGE=16327.97); penalty for toe crossings < 5 m from a nodestring/breakline crossing point.
#          Final run used S0MIN=16266.
# Inputs : WD/work/cands.pkl (place.py), WD/work/dp.pkl (dp.py; used for the V reach and the N indices), WD/xn_points.json
#          (nodestring x breakline crossing points, list of [x,y]; produced by hand/ad-hoc, no script in the pipeline writes it),
#          WD/work/core.py (imported; SP = sys.argv[1]).
# Output : WD/work/dpB.pkl = dict(N = kept asta indices with s<=16130.5, B = new indices of the B reach, V = first 60 vecchio indices); prints a summary.
# Run    : python3 dpB.py WD      (Anaconda python3; run from anywhere, copy of the script lives in WD/work)
# Units  : metres; ss = chainage along the asta principale, step 0.25 m between candidates.
# Re-place the B reach (Brenta downstream of Borgo) on the main-stream candidates.
# core.py (in WD/work) provides SP (= argv[1]), pickle, numpy as np and the other common imports
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
# C = candidates per stream, D0 = previous dynamic-programming result (index lists per stream)
C=pickle.load(open(f'{SP}/work/cands.pkl','rb')); D0=pickle.load(open(f'{SP}/work/dp.pkl','rb'))
# c = main-stream candidates: ss chainage, P centre points, ok validity flag; N = number of candidates
# S_BRIDGE = chainage of Ponte_Bordignon_monte, MARGIN = minimum distance B00050-bridge, S0MIN/S0MAX = window of the first section
c=C['main']; ss,P,ok=c['ss'],c['P'],c['ok']; N=len(ss)
S_BRIDGE=16327.97; MARGIN=5.0; S0MIN=16266.0; S0MAX=16285.0
# pen = per-candidate penalty: pen5 (toe crossings < 5 m from a toe vertex, 0..2) + 1000 if the approximate section crosses an inner breakline (hitO) + 10000 if it crosses a boundary line/nodestring (hitB); invalid candidates = 1e9
pen=c['pen5'].copy()+1000*c['hitO']+10000*c['hitB']; pen[~ok]=1e9
# extra penalty: a toe crossing closer than 5 m to a point where a nodestring meets a breakline
# XN = crossing points of nodestrings with breaklines (xn_points.json); kx = KD-tree on them
import json
from scipy.spatial import cKDTree
# tk = toe distance key, sg = side sign (+1 left, -1 right); q = toe point of each candidate on that side, dd = distance to nearest crossing point: +50 if closer than 5 m
XN=np.array(json.load(open(f'{SP}/xn_points.json'))); kx=cKDTree(XN)
for tk,sg in (('tL',1),('tR',-1)):
    q=P+sg*c['n']*np.nan_to_num(c[tk])[:,None]; dd,_=kx.query(q); pen+=50*((dd<5.0)&np.isfinite(c[tk]))
# forbid candidates in (S_BRIDGE-MARGIN, S_BRIDGE+20) m, so that no section lies between the B00050 limit and past the bridge
pen[(ss>S_BRIDGE-MARGIN)&(ss<S_BRIDGE+20)]=1e9          # no section between B00050 limit and past the bridge
# cost = best cumulative cost to reach candidate i; prev = predecessor candidate (-1 = none)
cost=np.full(N,np.inf); prev=np.full(N,-1,int)
# i0 = admissible starting candidates (first section window); cost starts at their own penalty
i0=np.where((ss>=S0MIN)&(ss<=S0MAX))[0]
cost[i0]=pen[i0]
# forward DP: from candidate i go to j = i+d with d in 198..202 steps of 0.25 m (49.5-50.5 m along the asta);
# ch = chord length between the two centre points
for i in range(i0[0],N):
    if not np.isfinite(cost[i]) or cost[i]>=1e9: continue
    for d in (198,199,200,201,202):
        j=i+d
        if j>=N: continue
        ch=float(np.hypot(*(P[j]-P[i])))
        # cn = cost via i: penalty of j + small preference for exactly 50 m + 500+100*|ch-50| if the chord is outside 49.5-50.5 m
        cn=cost[i]+pen[j]+0.01*(d*0.25-50)**2+(0 if 49.5<=ch<=50.5 else 500+100*abs(ch-50))
        if cn<cost[j]: cost[j]=cn; prev[j]=i
# L = end of the chainage; the last section must lie 5-50.5 m before L: choose the cheapest such end candidate
L=ss[-1]+0.25
cand=np.where((ss>=L-50.5)&(ss<=L-5)&np.isfinite(cost))[0]; j=cand[np.argmin(cost[cand])]
# backtrack through prev to get the list p of chosen candidate indices (in upstream-to-downstream order)
p=[]
while j>=0: p.append(j); j=prev[j]
# s = chainage of the chosen sections, ch = chord lengths between consecutive ones
p=np.array(p[::-1]); s=ss[p]; ch=np.hypot(*np.diff(P[p],axis=0).T)
# diagnostics: number/first/last sections, step and chord ranges, chords outside 49.5-50.5 m
print('B n',len(p),'first',s[:3],'last',s[-1],'L',L,'cost',round(cost[p[-1]],1))
print('step',np.diff(s).min(),np.diff(s).max(),'chord',ch.min().round(2),ch.max().round(2),'chord out',[(float(a),round(float(b),2)) for a,b in zip(s[:-1],ch) if not 49.5<=b<=50.5])
# diagnostics: obstacle hits and penalties actually accepted (pen>=1e9 must be 0)
print('hitB',int(c['hitB'][p].sum()),'hitO',int(c['hitO'][p].sum()),'pen5 sum',float(c['pen5'][p].sum()),'pen>=1e9',int((pen[p]>=1e9).sum()))
# N reach = previous dp indices on the asta up to s<=16130.5; V reach = first 60 vecchio sections of the old dp; saved with the new B
m=D0['main']; keepN=m[ss[m]<=16130.5]; print('N kept',len(keepN),ss[keepN][-1])
pickle.dump(dict(N=keepN,B=p,V=D0['vecchio'][:60]),open(f'{SP}/work/dpB.pkl','wb'))
