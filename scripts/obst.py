# obst.py  (stage 2; rebuilds the cap step of 2026-11-09 that had not been saved; previous: next_bed.py, next: bank.py)
# Purpose: cap the bankpoint search (keys maxL/maxR of sec_in.json) 0.5 m before the first obstacle beyond the toe. Obstacles:
#          non-section nodestrings (bridges etc., from the boundary file), inner breaklines (segments that are neither toe nor top-of-bank)
#          and the toe of another bed. An obstacle counts if it lies in (toe-0.5, top-of-bank) (or beyond the own toe for another bed).
# Inputs : WD/work/newfaces.pkl (place.py), WD/work/sec_in.json (export_B.py, then next_bed.py), boundary file = argv[2] (e.g. WD/in0/boundary.gpkg),
#          WD/work/core.py (SP = argv[1]; cls, boundary_segs, ring_segs, key, Rays, gpd, shapely, np come from it).
# Output : WD/work/sec_in.json OVERWRITTEN with maxL/maxR lowered where a cap applies (a cap is only lowered); prints each cap and the count.
# Run    : python3 obst.py WD /percorso/boundary.gpkg      (Anaconda python3; idempotent)
# Units  : metres along the section normal from the centre point.
# Cap the bankpoint search 0.5 m before the first obstacle beyond the toe:
# non-section nodestrings and inner breaklines (segments that are neither toe nor top-of-bank).
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
# NF: faces (fc) and per-face rows after widening; tb = bed boundary segments (toe lines); tc = bed/sponda/muro boundary segments
import json
NF=pickle.load(open(f'{SP}/work/newfaces.pkl','rb')); fc,rows=NF['fc'],NF['rows']
# skip = segment keys that are toe or top-of-bank lines: they are not 'inner' obstacles
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(fc,rows,lambda n: cls(n) in('bed','sponda','muro'))
skip={key(s) for s in tb}|{key(s) for s in tc}
# inner = unique ring segments of all faces that are not toe/top-of-bank (inner breaklines)
allseg=[]
for f in fc:
    for s in ring_segs(f):
        if key(s) not in skip: allseg.append(s)
seen=set(); inner=[]
for s in allseg:
    k=key(s)
    if k not in seen: seen.add(k); inner.append(s)
# bd = boundary layer (argv[2]); ns = coordinates of the nodestrings that are NOT sections (name not like S/V/N/B + 5 digits)
# nseg = their segments, shape (n,4)
bd=gpd.read_file(sys.argv[2],fid_as_index=True)
ns=[shapely.get_coordinates(g) for n,g in zip(bd.nome,bd.geometry) if not (n[0] in 'SVNB' and n[1:6].isdigit())]
nseg=np.vstack([np.c_[c[:-1],c[1:]] for c in ns])
# R = ray caster against inner breaklines + nodestrings; RB = against toe lines only (to stop before another bed)
R=Rays(np.vstack([np.array(inner),nseg])); RB=Rays(tb)   # RB: toe lines, used to stop before another bed
# S = sections of sec_in.json; n = number of caps applied
S=json.load(open(f'{SP}/work/sec_in.json')); n=0
for s in S:
    # o = origin (centre point), d = unit normal (positive = left); h/hb = signed ray hit distances up to 1500 m
    o=np.array([s['x'],s['y']]); d=np.array([s['nx'],s['ny']]); h=R.hits(o,d,1500); hb=RB.hits(o,d,1500)
    # for each side: sg sign, k = cap key, tk/ck = toe/top-of-bank key
    for sg,k,tk,ck in ((1,'maxL','tL','cL'),(-1,'maxR','tR','cR')):
        # v = obstacle distances on this side between (toe-0.5) and the top of bank
        v=np.sort(h[h*sg>0]*sg); v=v[(v>s[tk]-0.5)&(v<s[ck]-1e-6)]
        # vb = toes of other beds more than 5 cm beyond the own toe
        vb=np.sort(hb[hb*sg>0]*sg); vb=vb[vb>s[tk]+0.05]          # toe of another bed beyond the own toe
        # merge: the nearest obstacle sets the cap
        v=np.sort(np.r_[v,vb])
        if len(v):
            # cap = 0.5 m before the first obstacle; only if it lowers the current cap
            lim=float(v[0]-0.5)
            if lim<s.get(k,1e9): s[k]=lim; n+=1; print(' obstacle cap',s['stream'][0],round(s['s']),k,round(lim,2),'toe',round(s[tk],2))
# write back
json.dump(S,open(f'{SP}/work/sec_in.json','w')); print('obstacle caps',n)
