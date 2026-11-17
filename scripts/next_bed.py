# next_bed.py  (step 13; previous: export_sec.py, next: bank.py)
# Purpose: for each section, if a DIFFERENT bed polygon (another channel, e.g. Brenta vecchio / a bed branch) lies just beyond the
#          bank on one side, cap the bankpoint search distance (keys maxL / maxR) so that the search stops 0.5 m before that bed edge.
# Inputs : WD/work/newfaces.pkl (place.py: faces 'fc' and per-face rows after the widening) and WD/work/sec_in.json (export_sec.py).
# Output : WD/work/sec_in.json is OVERWRITTEN in place, adding maxL/maxR where a cap applies; prints each cap and the total count.
# Run    : python3 next_bed.py WD      (Anaconda python3; imports core.py from WD/work). Idempotent (a cap is only lowered).
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
NF=pickle.load(open(f'{SP}/work/newfaces.pkl','rb')); fc,rows=NF['fc'],NF['rows']
# tb: outline segments (x0,y0,x1,y1) of the union of all faces of class 'bed'; Rb answers ray-vs-segment first-hit queries.
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); Rb=Rays(tb)
S=json.load(open(f'{SP}/work/sec_in.json')); n=0
# For each section: ray from the centerpoint o along the normal d (both directions, up to 1500 m); h = signed distances of all hits with bed edges.
for s in S:
    o=np.array([s['x'],s['y']]); d=np.array([s['nx'],s['ny']]); h=Rb.hits(o,d,1500)
    # sg=+1 left side (key maxL, toe distance tL), sg=-1 right side (key maxR, toe tR); v = ascending distances of hits on this side
    # lying beyond the own toe (+5 cm, to skip the section's own bed edge).
    for sg,k,tk in ((1,'maxL','tL'),(-1,'maxR','tR')):
        v=np.sort(h[h*sg>0]*sg); v=v[v>s[tk]+0.05]
        # The bankpoint search extends at most 15 m past the toe (bank.py) plus a 2 m margin: only a bed edge inside that window matters.
        if len(v) and v[0]-0.5<s[tk]+15+2:
            # lim = maximum distance from the centerpoint allowed for the bankpoint: 0.5 m before the other bed.
            lim=float(v[0]-0.5)
            if lim<s.get(k,1e9): s[k]=lim; n+=1; print(' next-bed cap',s['stream'][0],round(s['s']),k,round(lim,2),'toe',round(s[tk],2))
json.dump(S,open(f'{SP}/work/sec_in.json','w')); print('caps',n)
