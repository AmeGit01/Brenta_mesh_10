# dump.py  (step 17; previous: regions.py, next: write.py)
# Purpose: collect everything that write.py must put into the new GeoPackages into one JSON file (no GDAL needed here):
#          the sections (as boundary nodestrings S#####/V#####), bankpoints, centerpoints, centerlines, moved boundary/breaklines, region changes.
# Inputs : WD/work/sec_in.json, bank_out.json, secs0.pkl, widen2.pkl ('newf'), bgn.pkl, cltab.pkl (cl2.py: smoothed centerlines 'q'), regions.json,
#          WD/in/boundary.gpkg (to know the next free fid/id) and WD/in/regioni_ponti.gpkg (next free fid).
# Output : WD/work/write.json with keys secs, bp, cp, cl, bgn, bl, reg (see the .md doc). Prints the changed boundary names, uniqueness check and counts.
# Run    : python3 dump.py WD      (Anaconda python3; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import json
S=json.load(open(f'{SP}/work/sec_in.json')); O=json.load(open(f'{SP}/work/bank_out.json')); secs=pickle.load(open(f'{SP}/work/secs0.pkl','rb'))
W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb')); bgn=pickle.load(open(f'{SP}/work/bgn.pkl','rb')); T0=pickle.load(open(f'{SP}/work/cltab.pkl','rb')); R=json.load(open(f'{SP}/work/regions.json'))
# fid0/id0 = first free feature id (GPKG fid) and first free 'id' field value for the new boundary features (sections).
bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True); fid0=int(bdf.index.max())+1; id0=int(bdf.id.max())+1
# Keep only boundary features whose coordinates really changed (> 1e-6 m) with respect to the input boundary.gpkg.
bgn={k:v for k,v in bgn.items() if np.abs(v-shapely.get_coordinates(next(iter(shapely.get_parts(bdf.geometry[k]))))).max()>1e-6}; print('boundary changed',[bdf.nome[k] for k in bgn])
# secout = section features; bp = bankpoints (2 per section); cp = centerpoints (1 per section); prev[stream] = index of the previous centerpoint.
secout=[]; bp=[]; cp=[]; prev={}
for i,(s,o,l) in enumerate(zip(S,O,secs)):
    # Section name: 'S' (main stream) or 'V' (vecchio) + progressive abscissa rounded to metres on 5 digits, e.g. S00050 (s=50 m).
    pre='S' if s['stream']=='main' else 'V'; nm=f"{pre}{int(round(s['s'])):05d}"
    secout.append(dict(fid=fid0+i,id=id0+i,nome=nm,coords=shapely.get_coordinates(l).tolist()))
    # Bankpoints = the two end vertices of the section: _sx = left (first vertex), _dx = right (last vertex). dist_cp = t from centerpoint; z_dtm = DTM height.
    a,b=shapely.get_coordinates(l)
    for side,x,y,tag in (('L',a[0],a[1],'sx'),('R',b[0],b[1],'dx')):
        q=o[side]; bp.append(dict(nome=f'{nm}_{tag}',sezione=nm,s_m=s['s'],z_dtm=q['z'],dist_cp=q['t'],tipo=q['kind'],regola=q['rule'],prom=q['prom'],x=float(x),y=float(y)))
    cp.append(dict(nome=nm,s_m=s['s'],x=s['x'],y=s['y'],stream=s['stream']))
    # dist_next of the previous centerpoint of the same stream = difference of progressive abscissae (m) between consecutive sections.
    k=s['stream']
    if k in prev: cp[prev[k]]['dist_next']=float(s['s']-S[prev[k]]['s'])
    prev[k]=i
print('names unique',len({s['nome'] for s in secout})==len(secout),secout[0]['nome'],secout[-1]['nome'])
# New region points get consecutive fids after the largest existing region fid.
newp=R['new']; 
reg=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True); pid0=int(reg.index.max())+1
for i,p in enumerate(newp): p['fid']=pid0+i
# cl = centerline vertices (1 m resampled, smoothed) of both streams.
cl={k:T0[k]['q'].tolist() for k in('main','vecchio')}
# write.json: bgn/bl keyed by the original fid (as string) -> new coordinate list; reg.drop = fids of old region points to delete; reg.new = new region points.
json.dump(dict(secs=secout,bp=bp,cp=cp,cl=cl,bgn={str(k):v.tolist() for k,v in bgn.items()},bl={str(k):v.tolist() for k,v in W2['newf'].items()},reg=dict(drop=R['dropped'],new=newp)),open(f'{SP}/work/write.json','w'))
print(len(secout),len(bp),len(cp),len(W2['newf']),len(newp))
