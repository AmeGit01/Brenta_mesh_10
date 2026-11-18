# sync_cp_bp.py  (stage 4, 2026-11-18; after manual edits of sections in boundary_50m; next: write3.py, then verify3.py)
# Purpose: bring centerline, centerpoints and bankpoints back in line with the sections as they are now in boundary_50m.gpkg
#          (sections moved or reshaped by hand in QGIS). For every section (reaches N, V, B):
#            * centre point = intersection of the section with the centre line of its reach; s_m = chainage of that point within the reach;
#            * the B centre line starts at B00000: it is cut again from the asta principale (reference centre line) at the new B00000;
#            * dist_next = s_m(next) - s_m (None for the last section of a reach);
#            * bankpoints = the two section vertices (left = first). A vertex that coincides (<= 1e-6 m) with the stored bankpoint keeps
#              tipo/regola/prom/z_dtm; a vertex that moved becomes tipo/regola 'manuale', prom None, z_dtm None (read from the DTM by write3.py),
#              except when the vertex is an end of a nodestring with the same geometry as the section (B00400 = idrometro_Borgo):
#              then tipo 'nodestring', regola = nodestring name; dist_cp is recomputed for every bankpoint.
# Inputs : argv[1] = layers folder (current *_50m.gpkg), argv[2] = reference centre-line file containing 'asta_principale' and 'brenta_vecchio'
#          (e.g. layers/centerline_50m_backup_20261117.gpkg), argv[3] = output json (e.g. WD/write3.json).
# Output : json dict(cl, cp, bp) in the format of write2.json (read by write3.py); prints the sections whose centre point or s_m changed,
#          the bankpoints that changed status, and consistency checks for the unchanged sections.
# Run    : python3 scripts/sync_cp_bp.py layers layers/centerline_50m_backup_20261117.gpkg WD/write3.json      (Anaconda python3)
import sys, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import substring
L,REF,OUT=sys.argv[1],sys.argv[2],sys.argv[3]
co=lambda g: shapely.get_coordinates(g)
# current layers
b=gpd.read_file(f'{L}/boundary_50m.gpkg'); cl=gpd.read_file(f'{L}/centerline_50m.gpkg')
cp=gpd.read_file(f'{L}/centerpoints_50m.gpkg'); bp=gpd.read_file(f'{L}/bankpoints_50m.gpkg')
ref=gpd.read_file(REF); A=ref[ref.nome=='asta_principale'].geometry.iloc[0]
sec=b[b.nome.str.match(r'^[NVB]\d{5}$')]; ns=b[~b.nome.str.match(r'^[NVB]\d{5}$')]
CP={r.nome:r for r in cp.itertuples()}; BP={r.nome:r for r in bp.itertuples()}
# nodestrings: name -> 2-vertex coordinates (to recognise a section that is a nodestring)
NS={n:co(g) for n,g in zip(ns.nome,ns.geometry)}
# centre lines: N and V unchanged; B recut from the asta at its intersection with the new B00000
line={r.ramo:r.geometry for r in cl.itertuples()}
g0=LineString(co(sec[sec.nome=='B00000'].geometry.iloc[0])); x0=g0.intersection(A); assert x0.geom_type=='Point', x0.geom_type
sB0=A.project(x0); line['B']=substring(A,sB0,A.length)
old_sB0=cl[cl.ramo=='B'].s0_asta.iloc[0]
print(f'B00000 on the asta: s0_asta {old_sB0:.3f} -> {sB0:.3f} (shift {sB0-old_sB0:+.3f} m)')
# per section: centre point and chainage
rows={}
for nm,g in zip(sec.nome,sec.geometry):
    # B sections are intersected with the full asta (the recut B line starts exactly on B00000, which gives a degenerate intersection)
    l=LineString(co(g)); base=A if nm[0]=='B' else line[nm[0]]; x=l.intersection(base)
    assert x.geom_type=='Point', (nm,x.geom_type)
    s=float(base.project(x))-(sB0 if nm[0]=='B' else 0.0)
    rows[nm]=dict(nome=nm,stream=nm[0],x=x.x,y=x.y,s_m=s,coords=co(g))
# report: centre points that moved (> 1 mm) or s_m that changed (> 1 mm)
mv=[(n,round(float(np.hypot(r['x']-CP[n].geometry.x,r['y']-CP[n].geometry.y)),3),round(r['s_m']-CP[n].s_m,3)) for n,r in rows.items()
    if np.hypot(r['x']-CP[n].geometry.x,r['y']-CP[n].geometry.y)>1e-3 or abs(r['s_m']-CP[n].s_m)>1e-3]
print('centre points moved or s_m changed (name, move m, delta s_m):',len(mv)); print(' ',mv[:40])
# dist_next per reach (order of the boundary layer = reach order)
order=list(rows)
for i,n in enumerate(order):
    nx=order[i+1] if i+1<len(order) and order[i+1][0]==n[0] else None
    rows[n]['dist_next']=rows[nx]['s_m']-rows[n]['s_m'] if nx else None
# bankpoints
bpo=[]; changed=[]
for n,r in rows.items():
    c=r['coords']
    # nodestring with the same geometry as the section (either direction)
    same=[k for k,v in NS.items() if v.shape==c.shape and (np.abs(v-c).max()<1e-6 or np.abs(v[::-1]-c).max()<1e-6)]
    for t,p in (('sx',c[0]),('dx',c[-1])):
        q=BP[f'{n}_{t}']; d=float(np.hypot(p[0]-q.geometry.x,p[1]-q.geometry.y))
        e=dict(nome=f'{n}_{t}',sezione=n,s_m=r['s_m'],x=float(p[0]),y=float(p[1]),dist_cp=float(np.hypot(p[0]-r['x'],p[1]-r['y'])))
        if d<=1e-6:
            e.update(z_dtm=float(q.z_dtm),tipo=q.tipo,regola=q.regola,prom=None if q.prom!=q.prom else float(q.prom))
        else:
            e.update(z_dtm=None,prom=None,tipo='nodestring' if same else 'manuale',regola=same[0] if same else 'manuale')
            changed.append((e['nome'],round(d,2),q.tipo,'->',e['tipo']))
        bpo.append(e)
print('bankpoints moved:',len(changed)); print(' ',changed)
# centre lines out
cl_out=[]
for r in cl.itertuples():
    g=line[r.ramo]
    cl_out.append(dict(nome=r.nome,ramo=r.ramo,coords=co(g)[:,:2].tolist(),s0_asta=(float(sB0) if r.ramo=='B' else (None if r.s0_asta!=r.s0_asta else float(r.s0_asta)))))
cp_out=[dict(nome=r['nome'],stream=r['stream'],s_m=r['s_m'],x=r['x'],y=r['y'],dist_next=r['dist_next']) for r in rows.values()]
json.dump(dict(cl=cl_out,cp=cp_out,bp=bpo),open(OUT,'w'))
print('written',OUT,'cl',len(cl_out),'cp',len(cp_out),'bp',len(bpo))
