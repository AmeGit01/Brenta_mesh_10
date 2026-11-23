# export_B.py  (stage 2; replaces export_sec.py for the B reach; previous: dpB.py or dpB2.py, next: next_bed.py)
# Purpose: write sec_in.json for the B reach only (same fields as export_sec.py), from the indices chosen by dpB.py / dpB2.py.
# Inputs : WD/work/cands.pkl (place.py; 'main' candidates), WD/work/<pickle> (argv[2], default dpB.pkl; key 'B' and, from dpB2.py,
#          key 'anchor'), WD/work/core.py (SP = argv[1]).
# Output : WD/work/sec_in.json (OVERWRITTEN): list of dicts stream,tag,s,x,y,nx,ny,tL,tR,cL,cR (x,y centre point, nx,ny unit normal,
#          tL/tR toe distances, cL/cR top-of-bank distances, in m); prints the number of sections.
#          With dpB2.pkl the record in the anchor slot keeps the fields of its placeholder candidate (so that the later scripts run
#          unchanged) and gets an extra key 'anchor' with the nodestring geometry; assemble.py then uses the nodestring as the section.
# Run    : python3 export_B.py WD [dpB2.pkl]      (Anaconda python3)
# Write sec_in.json for the B reach (same fields as export_sec.py).
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
# C = main-stream candidate arrays; D = dpB/dpB2 result (key B). One record per chosen candidate j (tag 'B' is used later by assemble.py)
PK=sys.argv[2] if len(sys.argv)>2 else 'dpB.pkl'
C=pickle.load(open(f'{SP}/work/cands.pkl','rb'))['main']; D=pickle.load(open(f'{SP}/work/{PK}','rb'))
out=[dict(stream='main',tag='B',s=float(C['ss'][j]),x=float(C['P'][j,0]),y=float(C['P'][j,1]),nx=float(C['n'][j,0]),ny=float(C['n'][j,1]),tL=float(C['tL'][j]),tR=float(C['tR'][j]),cL=float(C['cL'][j]),cR=float(C['cR'][j])) for j in D['B']]
# anchor slot (dpB2.py only): attach the nodestring data to the placeholder record
if 'anchor' in D: out[D['anchor']['k']]['anchor']=D['anchor']
# write the B-only list (overwrites any previous sec_in.json)
json.dump(out,open(f'{SP}/work/sec_in.json','w')); print('B sections',len(out))
