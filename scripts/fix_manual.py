# fix_manual.py  (stage 4, 2026-11-18; after manual edits of sections in QGIS; next: write3.py, then sync_cp_bp.py/write3.py and verify3.py)
# Purpose: repair the side effects of sections edited by hand, without moving any section/nodestring vertex in plan:
#   1. sections with z or m different from 0 (vertices snapped in QGIS onto a 3D line): z = m = 0 (plan coordinates unchanged);
#   2. a section that crosses a breakline at less than NEAR (5 cm) from a breakline vertex (but not exactly on it): that vertex is moved
#      onto the crossing point, in every breakline that shares it (rule: move the breakline, never the nodestring). Not done if the
#      vertex belongs to a nodestring or to a locked line (mat11_lines.json): such cases are only reported;
#   3. faces of the planar graph (breaklines + all boundary lines) without a region point: a new point at the pole of inaccessibility
#      (polylabel), with the attributes of the original region (regioni_ponti.gpkg, original graph of breaklines.gpkg + boundary.gpkg)
#      whose face contains that point; ambiguous or missing origin -> reported, no point.
#   It also reports section ends lying at 0 < d < 1 cm from a line (ends that should be snapped exactly).
# Inputs : argv[1] = layers folder; argv[2] = mat11_lines.json (prep_inputs_nvb.py); argv[3] = output json (payload for write3.py).
# Output : json dict(bd={fid: coords}, bl={fid: coords}, reg_new=[{nome, mat_id, max_area, buco, x, y}]); prints every change.
# Run    : python3 scripts/fix_manual.py layers WD/mat11_lines.json WD/write3b.json      (Anaconda python3; read-only on the layers)
import sys, json, re, collections, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union, polylabel
L,LOCKF,OUT=sys.argv[1],sys.argv[2],sys.argv[3]; NEAR=0.05
rd=lambda n: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True)
bl,bd,rg=rd('breaklines_50m'),rd('boundary_50m'),rd('regioni_ponti_50m'); LOCK=set(json.load(open(LOCKF)))
co=lambda g: shapely.get_coordinates(g)[:,:2]
issec=lambda n: bool(re.fullmatch(r'[NVB]\d{5}',n))
sec=bd[[issec(n) for n in bd.nome]]; oth=bd[[not issec(n) for n in bd.nome]]
# 1. sections with z/m != 0
out_bd={}
for f,g in sec.geometry.items():
    z=shapely.get_coordinates(g,include_z=True)[:,2]
    if np.abs(z).max()>0: out_bd[int(f)]=co(g).tolist(); print('section z set to 0:',sec.nome[f],z.tolist())
# 2. near-coincident crossings
F={int(f):co(g).copy() for f,g in bl.geometry.items() if g is not None and not g.is_empty}
NSV={tuple(np.round(p,6)) for g in oth.geometry for p in co(g)}
moved=collections.OrderedDict()
for nm,g in zip(sec.nome,sec.geometry):
    l=LineString(co(g))
    for f,c in F.items():
        lf=LineString(c)
        if not l.intersects(lf): continue
        for p in co(l.intersection(lf)):
            d=np.hypot(*(c-p).T); j=int(np.argmin(d))
            if not (1e-9<d[j]<NEAR): continue
            v=tuple(c[j]); key=tuple(np.round(v,6))
            share=[h for h,cc in F.items() if (np.hypot(*(cc-np.array(v)).T)<1e-9).any()]
            if key in NSV or any(h in LOCK for h in share):
                print('NOT moved (nodestring or locked line):',nm,f,round(d[j]*1000,1),'mm',share); continue
            moved[key]=(nm,np.array(v),p,share); print(f'vertex moved onto the crossing: {nm} lines {share} by {d[j]*1000:.1f} mm')
out_bl={}
for key,(nm,v,p,share) in moved.items():
    for h in share:
        c=out_bl.get(h,F[h].copy()) if isinstance(out_bl.get(h),np.ndarray) else F[h].copy()
        i=np.hypot(*(c-v).T)<1e-9; c[i]=p; out_bl[h]=c
out_bl={h:c.tolist() for h,c in out_bl.items()}
# section ends close to, but not on, a line
U=unary_union([LineString(c) for c in F.values()]+[LineString(co(g)) for g in oth.geometry])
gap=[(nm,i,round(U.distance(Point(p))*1000,2)) for nm,g in zip(sec.nome,sec.geometry) for i,p in enumerate(co(g)) if 0<U.distance(Point(p))<0.01]
print('section ends at 0-10 mm from a line (mm):',gap)
# 3. faces without region point (graph with the corrected breaklines)
F2={**F,**{h:np.array(c) for h,c in out_bl.items()}}
ln=[LineString(c) for c in F2.values()]+[LineString(co(g)) for g in bd.geometry]
fc=list(polygonize(unary_union(ln))); T=shapely.STRtree(fc); g=rg[rg.geometry.notna()]
cnt=collections.Counter(int(f) for p,f in zip(*T.query(g.geometry.values,predicate='within')))
empty=[i for i in range(len(fc)) if cnt[i]==0]; print('faces',len(fc),'without point',len(empty))
rg0=rd('regioni_ponti'); ob=rd('breaklines'); obd=rd('boundary')
OL=[LineString(co(x)) for x in list(ob.geometry)+list(obd.geometry) if x is not None and not x.is_empty]
ofc=list(polygonize(unary_union(OL))); TO=shapely.STRtree(ofc); og=rg0[rg0.geometry.notna()]; oatt={}
for p,f in zip(*TO.query(og.geometry.values,predicate='within')): oatt.setdefault(int(f),[]).append(og.index[p])
reg_new=[]
for i in empty:
    q=polylabel(fc[i],0.01); f0=TO.query(q,predicate='within'); src=[s for x in f0 for s in oatt.get(int(x),[])]
    names={rg0.nome[s] for s in src}
    if len(names)!=1: print('face',i,'area %.1f'%fc[i].area,'origin ambiguous/missing',sorted(names),'-> no point'); continue
    s=min(src); r=rg0.loc[s]
    reg_new.append(dict(nome=r.nome,mat_id=int(r.mat_id),max_area=float(r.max_area),buco=None if r.buco!=r.buco else float(r.buco),x=q.x,y=q.y))
    print(f'new region point: face {i} area {fc[i].area:.1f} m2, clearance {fc[i].exterior.distance(q):.2f} m, attributes of original fid {s} ({r.nome}, mat_id {int(r.mat_id)}, max_area {r.max_area})')
json.dump(dict(bd=out_bd,bl=out_bl,reg_new=reg_new),open(OUT,'w')); print('written',OUT,'bd',len(out_bd),'bl',len(out_bl),'reg_new',len(reg_new))
