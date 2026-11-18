# prep_write.py  (stage 2, 2026-11-17; previous: regions2.py, next: write2.py)
# Purpose: collect everything to write into WD/write2.json (the layers are written by write2.py with system python/OGR):
#          changed breaklines, new sections (fid = 64+k, id = 60+k), the three centerlines (N, V, B), centerpoints, bankpoints and region-point changes.
#          Bankpoints moved by hand (moved > 1e-6 m) become tipo/regola 'manuale' with z_dtm null (filled by write2.py from the DTM).
# Inputs : (cwd = WD) argv[1] = fix5 json (normally fix5.json), in/breaklines_50m.gpkg, in/centerline_50m.gpkg, in/regioni_ponti_50m.gpkg,
#          secs_new.json, regions2.json.
# Output : WD/write2.json = dict(bl, secs, cl, cp, bp, reg); prints the counts and the length of the three centerlines.
# Run    : cd WD ; python3 prep_write.py fix5.json      (Anaconda python3; relative paths: the working directory MUST be WD)
# Collect everything to be written into write2.json (Anaconda python: shapely/geopandas).
import json, sys, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
from shapely.ops import substring
# fixf = file with the fixed breaklines
fixf=sys.argv[1]
# F = new breaklines (fix5 file)
F={int(k):v for k,v in json.load(open(fixf))['F'].items()}
bl=gpd.read_file('in/breaklines_50m.gpkg',fid_as_index=True)
# O = current breaklines (arrays); blchg = breaklines whose coordinates changed
O={int(f):shapely.get_coordinates(g) for f,g in bl.geometry.items() if g is not None and not g.is_empty}
blchg={f:c for f,c in F.items() if len(c)!=len(O[f]) or np.abs(np.array(c)-O[f]).max()>1e-12}
# secs = new sections, R = region decisions
secs=json.load(open('secs_new.json')); R=json.load(open('regions2.json'))
# cl = centerlines; A = asta_principale, V = brenta_vecchio
cl=gpd.read_file('in/centerline_50m.gpkg'); A=cl[cl.nome=='asta_principale'].geometry.iloc[0]; V=cl[cl.nome=='brenta_vecchio'].geometry.iloc[0]
# N / VV / B = sections of each reach; sB0 = asta chainage of B00000
N=[s for s in secs if s['reach']=='N']; VV=[s for s in secs if s['reach']=='V']; B=[s for s in secs if s['reach']=='B']
sB0=B[0]['s_asta']
# lines = the three centerlines: N = asta 0..last N section, V = vecchio 0..last V section, B = asta from sB0 to its end
lines=[dict(nome='N_caldonazzo_borgo',ramo='N',coords=shapely.get_coordinates(substring(A,0,N[-1]['s'])).tolist(),s0_asta=0.0),
       dict(nome='V_brenta_vecchio',ramo='V',coords=shapely.get_coordinates(substring(V,0,VV[-1]['s'])).tolist(),s0_asta=None),
       dict(nome='B_borgo_valle',ramo='B',coords=shapely.get_coordinates(substring(A,sB0,A.length)).tolist(),s0_asta=sB0)]
# cp = centerpoints, bp = bankpoints, sx = sections
cp=[]; bp=[]; sx=[]
# centerpoints per reach: dist_next = distance along s to the next section (None for the last)
for reach in 'NVB':
    R_=[s for s in secs if s['reach']==reach]
    for i,s in enumerate(R_):
        cp.append(dict(nome=s['nome'],stream=reach,s_m=s['s'],x=s['cx'],y=s['cy'],dist_next=(R_[i+1]['s']-s['s']) if i+1<len(R_) else None))
# sections get consecutive fid 64.. and id 60..; bankpoints named <section>_sx / _dx
for k,s in enumerate(secs):
    sx.append(dict(fid=64+k,id=60+k,nome=s['nome'],coords=s['coords']))
    for sd in s['sides']:
        # man = bankpoint moved by hand
        man=sd['moved']>1e-6
        bp.append(dict(nome=f"{s['nome']}_{sd['tag']}",sezione=s['nome'],s_m=s['s'],z_dtm=None if man else sd['z'],dist_cp=float(np.hypot(sd['x']-s['cx'],sd['y']-s['cy'])),
                       tipo='manuale' if man else sd['tipo'],regola='manuale' if man else sd['regola'],prom=None if man else sd['prom'],x=sd['x'],y=sd['y']))
# new region points get consecutive fids after the current maximum
r=gpd.read_file('in/regioni_ponti_50m.gpkg',fid_as_index=True); pid0=int(r.index.max())+1
for i,p in enumerate(R['new']): p['fid']=pid0+i
# save
json.dump(dict(bl={str(f):c for f,c in blchg.items()},secs=sx,cl=lines,cp=cp,bp=bp,reg=dict(drop=R['drop'],new=R['new'])),open('write2.json','w'))
# reports
print('breaklines changed',len(blchg),'sections',len(sx),'cp',len(cp),'bp',len(bp),'reg drop',len(R['drop']),'new',len(R['new']),'manual bp',sum(b['tipo']=='manuale' for b in bp))
print('centerlines',[(l['nome'],round(LineString(l['coords']).length,1)) for l in lines])
