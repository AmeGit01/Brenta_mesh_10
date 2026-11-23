# export_sec.py  (step 12 of the section pipeline; previous: dp.py, next: next_bed.py)
# Purpose: turn the section positions chosen by the dynamic programming (dp.py) into a flat JSON list,
#          one record per 50 m cross-section, which is the input of the bankpoint computation (bank.py).
# Inputs : WD/work/cands.pkl (place.py: candidate sections per stream) and WD/work/dp.pkl (dp.py: chosen candidate indices).
# Output : WD/work/sec_in.json (list of dicts, see below); prints the number of sections.
# Run    : python3 export_sec.py WD      (Anaconda python3; imports core.py from WD/work)
# Units  : metres, EPSG:25832. Left/right = side of the unit normal n (+n = left, -n = right).
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
# C[name]: dict of candidate arrays for stream 'main' (asta) or 'vecchio' (Brenta vecchio):
#   ss = progressive abscissa along the centerline, P = centerline points (x,y), n = unit normals,
#   tL/tR = distance centerpoint -> bed toe (left/right), cL/cR = distance centerpoint -> top-of-bank line (left/right).
# D[name]: array of indices j into the candidates, i.e. the sections selected by the DP (ordered along the stream).
C=pickle.load(open(f'{SP}/work/cands.pkl','rb')); D=pickle.load(open(f'{SP}/work/dp.pkl','rb'))
# one record per selected section; keys: stream, s (m along centerline), x,y (centerpoint), nx,ny (unit normal), tL,tR (toe), cL,cR (top of bank)
out=[]
for name in('main','vecchio'):
    c=C[name]; p=D[name]
    for j in p:
        out.append(dict(stream=name,s=float(c['ss'][j]),x=float(c['P'][j,0]),y=float(c['P'][j,1]),nx=float(c['n'][j,0]),ny=float(c['n'][j,1]),tL=float(c['tL'][j]),tR=float(c['tR'][j]),cL=float(c['cL'][j]),cR=float(c['cR'][j])))
json.dump(out,open(f'{SP}/work/sec_in.json','w')); print(len(out))
