# gaps.py - step 9. Print-only check of connectivity: finds line ends that touched another breakline in the original data (within 1 mm)
# but touch nothing in the widened geometry. Boundary lines are not considered.
# Inputs : WD/work/chains.pkl (chains.py); WD/work/widen2.pkl (apply_widen.py)
# Outputs: none (stdout): the number of broken ends, then up to 60 tuples (fid, end 0=first/-1=last, new end xy, original neighbour fids (max 4), original end xy)
# Usage  : python3 gaps.py WD      (Anaconda python3; core.py in WD/work)
# Interpretation: 0 = no gaps. Otherwise the listed ends should be inspected/fixed.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
C=pickle.load(open(f'{SP}/work/chains.pkl','rb')); W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb'))
# feat: original geometries; newf: widened geometries (only changed features); keys: fid list (index i = position in keys)
feat=C['feat']; newf=W2['newf']; endmap=W2['endmap']
keys=list(feat)
# lines(F): LineString for every fid using F[fid] if present else the original
def lines(F): return [LineString(F.get(k,feat[k])) for k in keys]
# old/new geometries with STRtrees
old=lines({}); new=lines(newf)
to=shapely.STRtree(old); tn=shapely.STRtree(new)
# conn(tree,ls,p,me): fids of lines (other than index me) within 1 mm of point p
def conn(tree,ls,p,me):
    idx=tree.query(Point(p),predicate='dwithin',distance=1e-3); return [keys[i] for i in idx if i!=me]
# bad: ends that had a neighbour in the original geometry but none in the new one
bad=[]
for i,k in enumerate(keys):
    a=feat[k]; b=newf.get(k,a)
    for e in (0,-1):
        oc=conn(to,old,a[e],i); nc=conn(tn,new,b[e],i)
        if oc and not nc: bad.append((k,e,[round(float(x),1) for x in b[e]],oc[:4],[round(float(x),1) for x in a[e]]))
print(len(bad)); 
for b in bad[:60]: print(b)
