# finals.py  (step 15; previous: bank.py, next: regions.py)
# Purpose: build the final cross-sections as straight 2-vertex lines from left bankpoint (sx) to right bankpoint (dx), perpendicular to the
#          centerline, and run geometric sanity checks (printed only) against the widened breaklines, boundary and other sections.
# Inputs : WD/work/sec_in.json, bank_out.json, widen2.pkl (apply_widen: 'newf' = moved breaklines), chains.pkl ('feat' = original breakline coords),
#          bgn.pkl (moved boundary coords), newfaces.pkl (place.py: faces+rows after widening), WD/in/boundary.gpkg.
# Output : WD/work/secs0.pkl = list of shapely LineString (2 vertices), same order as sec_in.json. Everything else is printed:
#          crossings of sections with inner lines / boundary nodestrings / top-of-bank lines, section-section crossings, section length min/median/max.
# Run    : python3 finals.py WD      (Anaconda python3; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
S=json.load(open(f'{SP}/work/sec_in.json')); O=json.load(open(f'{SP}/work/bank_out.json'))
W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb')); Cc=pickle.load(open(f'{SP}/work/chains.pkl','rb')); bgn=pickle.load(open(f'{SP}/work/bgn.pkl','rb')); NF=pickle.load(open(f'{SP}/work/newfaces.pkl','rb'))
# feat[fid] = original breakline vertices; newf[fid] = moved version (only for widened lines); fc,rows = face polygons and per-face names after widening.
feat=Cc['feat']; newf=W2['newf']; fc,rows=NF['fc'],NF['rows']
bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True)
# bgeo[fid] = coordinates of each boundary feature (first part): the moved version from bgn.pkl if the feature was changed, else the original.
bgeo={k:bgn.get(k,shapely.get_coordinates(next(iter(shapely.get_parts(g))))) for k,g in bdf.geometry.items()}
# Section endpoints: p0 = centerpoint + n*t_left_bankpoint (left, sx); p1 = centerpoint - n*t_right_bankpoint (right, dx).
secs=[]
for s,o in zip(S,O):
    p0=np.array([s['x']+s['nx']*o['L']['t'],s['y']+s['ny']*o['L']['t']]); p1=np.array([s['x']-s['nx']*o['R']['t'],s['y']-s['ny']*o['R']['t']])
    secs.append(LineString([p0,p1]))
pickle.dump(secs,open(f'{SP}/work/secs0.pkl','wb'))
# tb = outline of bed faces (bed edges / toe); tc = outline of bed+sponda+muro faces (toe and top-of-bank); tbk,tck = sets of their rounded segment keys.
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(fc,rows,lambda n: cls(n) in('bed','sponda','muro'))
tbk={key(x) for x in tb}; tck={key(x) for x in tc}
# inner = breakline segments (moved version where available) that are neither on a bed edge nor on a top-of-bank edge, i.e. interior lines
# (e.g. 'intermedio'); meta = breakline fid of each segment. tops = top-of-bank segments as LineStrings.
# inner lines
inner=[]; meta=[]
for f,a in feat.items():
    a2=newf.get(f,a)
    for x in np.c_[a2[:-1],a2[1:]]:
        k=key(x)
        if k not in tbk and k not in tck: inner.append(LineString(x.reshape(2,2))); meta.append(f)
tops=[LineString(x.reshape(2,2)) for x in tc]
# Spatial indexes; bnames = boundary feature names aligned with bgeo.
IT=shapely.STRtree(inner); BT=shapely.STRtree([LineString(v) for v in bgeo.values()]); bnames=[bdf.nome[k] for k in bgeo]; TT=shapely.STRtree(tops)
out=collections.defaultdict(list)
# For each section: toe = the two toe points (centerpoint +-n*t); crossings with inner lines are recorded unless the only intersection is
# a single point coinciding (< 1e-4 m) with a toe point. Crossings with boundary nodestrings and with the tc outline are recorded too.
# NOTE: tc contains the bed edges, which every section crosses at its toe, so 'top' appears to list essentially all sections.
for i,l in enumerate(secs):
    s=S[i]; toe=np.array([[s['x']+s['nx']*s['tL'],s['y']+s['ny']*s['tL']],[s['x']-s['nx']*s['tR'],s['y']-s['ny']*s['tR']]])
    for j in IT.query(l,predicate='intersects'):
        p=shapely.get_coordinates(l.intersection(inner[j]))
        if len(p)==1 and np.hypot(*(toe-p[0]).T).min()<1e-4: continue
        out['inner'].append((i,meta[j],p[0].round(2).tolist() if len(p) else None))
    for j in BT.query(l,predicate='intersects'): out['bd'].append((i,bnames[j]))
    if len(TT.query(l,predicate='intersects')): out['top'].append(i)
# Reports (print only): counts and details of the crossings collected above.
print('crossing inner',len(out['inner']),'bd',len(out['bd']),'top',len(out['top']))
print('bd list',[(S[i]['stream'][0],round(S[i]['s']),n) for i,n in out['bd']])
print('inner',collections.Counter(m for i,m,_ in out['inner']).most_common(30)); print('detail',[(S[i]['stream'][0],round(S[i]['s']),m,p) for i,m,p in out['inner']][:40])
print('inner sec ids',sorted(set((S[i]['stream'][0],round(S[i]['s'])) for i,m,_ in out['inner']))[:50])
print('top',[(S[i]['stream'][0],round(S[i]['s'])) for i in out['top']])
# Section-section crossings (pairs i<j that intersect) and length statistics of the sections.
ST=shapely.STRtree(secs); a,b=ST.query(secs,predicate='intersects'); pr=[(int(x),int(y)) for x,y in zip(a,b) if x<y]; print('section-section crossings',len(pr),[(S[x]['stream'][0],round(S[x]['s']),S[y]['stream'][0],round(S[y]['s'])) for x,y in pr][:40])
L=[l.length for l in secs]; print('section length',min(L),np.median(L),max(L))

