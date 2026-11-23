# dp.py - step 11. Dynamic programming over the 0.25 m candidates of place.py to choose the section stations: first section at s in [49.5,50.5] m,
# then consecutive stations 49.5-50.5 m apart (chord between points), each candidate penalized by the constraints. The Brenta vecchio is solved after the main stem
# and is penalized where its candidate section would cross a main-stem section.
# Inputs : WD/work/cands.pkl (place.py)
# Outputs: WD/work/dp.pkl (dict 'main' and 'vecchio' -> int array of candidate indices into cands[name]; s = 0.25*index); diagnostics on stdout
# Usage  : python3 dp.py WD      (Anaconda python3; core.py in WD/work)
# Costs: pen = pen5 + 1000*hitO + 10000*hitB (+extra); invalid candidate = 1e9; a transition adds 0.01*(ds-50)^2 and, if the chord is outside 49.5-50.5 m, 500+100*|chord-50|.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
# C = candidates (cands.pkl)
C=pickle.load(open(f'{SP}/work/cands.pkl','rb'))
# dp(c,name,extra=None): c = candidates of one centerline ('name' is unused). Returns (cost, prev): minimal cost of a chain ending at each candidate and predecessor index (-1 = start)
def dp(c,name,extra=None):
    # pen = per-candidate penalty; weights: pen5 x1, hitO x1000, hitB x10000 (hard constraints in practice)
    ss,P,ok=c['ss'],c['P'],c['ok']; N=len(ss); pen=c['pen5'].copy()+1000*c['hitO']+10000*c['hitB']
    # extra: additional penalty array (used for the Brenta vecchio crossing the main stem)
    if extra is not None: pen+=extra
    # invalid candidates are practically forbidden
    pen[~ok]=1e9
    # cost[j] = best cost of a chain ending at candidate j; prev[j] = its predecessor
    cost=np.full(N,np.inf); prev=np.full(N,-1,int)
    # start: candidates with s in [49.5,50.5] m (first section at ~50 m); small penalty for deviation from 50
    i0=[i for i in range(N) if 49.5<=ss[i]<=50.5]
    for i in i0: cost[i]=pen[i]+0.01*(ss[i]-50)**2
    # D: allowed index steps 198..202 (= 49.5..50.5 m of centerline at 0.25 m per index)
    D=[198,199,200,201,202]
    # forward pass in increasing s
    for i in range(N):
        if not np.isfinite(cost[i]) : continue
        for d in D:
            # j = candidate d steps ahead
            j=i+d
            if j>=N: continue
            # ch = straight chord (m) between the two section points
            ch=float(np.hypot(*(P[j]-P[i]))); 
            # transition cost = pen[j] + 0.01*(ds-50)^2 + (0 if chord in [49.5,50.5] else 500+100*|ch-50|)
            cn=cost[i]+pen[j]+0.01*(d*0.25-50)**2+(0 if 49.5<=ch<=50.5 else 500+100*abs(ch-50))
            # keep the best predecessor
            if cn<cost[j]: cost[j]=cn; prev[j]=i
    return cost,prev
# walk(prev,j): list of candidates from the start to j following prev
def walk(prev,j):
    p=[]
    while j>=0: p.append(j); j=prev[j]
    return p[::-1]
# res: results by name
res={}
# main stem first; L = total length (m) of the main centerline (last candidate + 0.25)
c=C['main']; L=c['ss'][-1]+0.25
cost,prev=dp(c,'main')
# best end: lowest cost among candidates with s in [L-50.5, L-5]
cand=np.where((c['ss']>=L-50.5)&(c['ss']<=L-5)&np.isfinite(cost))[0]; j=cand[np.argmin(cost[cand])]
# p = chain of candidate indices
p=walk(prev,j); res['main']=np.array(p); 
# prints number of sections, first/last s, length, cost
ps=np.array(p); ss=c['ss'][ps]; print('main n',len(p),'first',ss[0],'last',ss[-1],'L',L,'cost',round(cost[j],1))
# checks: chord min/max, number of chord violations and where; counts of boundary/inner-line hits, 5 m violations; ds range and fraction of exactly 50 m steps
ch=np.hypot(*np.diff(c['P'][ps],axis=0).T); print(' chord',ch.min().round(2),ch.max().round(2),'viol',int(((ch<49.5)|(ch>50.5)).sum()),' at s',ss[:-1][(ch<49.5)|(ch>50.5)].tolist(),ch[(ch<49.5)|(ch>50.5)].round(2).tolist());print(' hitB',int(c['hitB'][ps].sum()),'hitO',int(c['hitO'][ps].sum()),'pen5',int(c['pen5'][ps].sum()),'ds',np.diff(ss).min(),np.diff(ss).max(),'uniform',round(float(np.mean(np.diff(ss)==50)),3))
# main section extents as obstacles for Vecchio
# main section extents as obstacles for Vecchio: n,Pm = normals/points of the chosen main stations
n=c['n'][ps]; Pm=c['P'][ps]; tL,tR,cL,cR=[c[k][ps] for k in('tL','tR','cL','cR')]
# ml = approximate main sections (toe+15 m, but not beyond 5 m inside the top)
ml=shapely.linestrings(np.stack([Pm+n*np.minimum(tL+15,cL-5)[:,None],Pm-n*np.minimum(tR+15,cR-5)[:,None]],axis=1))
# T = their STRtree
T=shapely.STRtree(ml)
# Brenta vecchio candidates: all of them considered
c=C['vecchio']; ps0=np.arange(len(c['ss']))
tL,tR,cL,cR=c['tL'],c['tR'],c['cL'],c['cR']
# approximate extents of each vecchio candidate section
ext=np.minimum(tL+15,cL-5); exr=np.minimum(tR+15,cR-5)
# ln = approximate vecchio candidate sections
ln=shapely.linestrings(np.stack([c['P']+c['n']*np.nan_to_num(ext)[:,None],c['P']-c['n']*np.nan_to_num(exr)[:,None]],axis=1))
# ex = 1e5 (practically forbidden) where the vecchio candidate crosses a main section
a,b=T.query(ln,predicate='intersects'); ex=np.zeros(len(c['ss'])); ex[np.unique(a)]=1e5
# prints how many vecchio candidates cross main sections, and the first/last s of them
print('vecchio cand crossing main sections',int((ex>0).sum()),'of',len(ex),' first/last s crossing',c['ss'][ex>0][[0,-1]] if (ex>0).any() else '')
# solve the vecchio with that extra penalty; L2 = its length
cost,prev=dp(c,'vecchio',ex); L2=c['ss'][-1]+0.25
# reachable candidates (finite cost < 1e4, i.e. no forbidden crossing)
ok=np.where(np.isfinite(cost)&(cost<1e4))[0]; print('reachable to s',c['ss'][ok].max(),'L',L2)
# j = farthest reachable candidate
j=ok[np.argmax(c['ss'][ok])]
# best end close to last reachable
cand=ok[c['ss'][ok]>=c['ss'][j]-0.75]; j=cand[np.argmin(cost[cand])]
# chain for the vecchio; prints chord stats, violations, number of sections, first/last s, hit counts
p=np.array(walk(prev,j)); res['vecchio']=p; ch=np.hypot(*np.diff(c['P'][p],axis=0).T); print('vecchio chord',ch.min().round(2),ch.max().round(2),'viol',int(((ch<49.5)|(ch>50.5)).sum()),c['ss'][p][:-1][(ch<49.5)|(ch>50.5)].tolist()); ss=c['ss'][p]; print('vecchio n',len(p),ss[0],ss[-1],'hitB',int(c['hitB'][p].sum()),'hitO',int(c['hitO'][p].sum()),'pen5',int(c['pen5'][p].sum()),'ex',int((ex[p]>0).sum()))
# save: indices of the chosen candidates
pickle.dump(res,open(f'{SP}/work/dp.pkl','wb'))
