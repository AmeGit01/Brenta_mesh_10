# verify3.py  (stage 4, 2026-11-18; previous: write3.py; companion: verify3_dtm.py for the DTM values)
# Purpose: independent checks of ALL attributes and geometries of the six *_50m layers read back from disk, after the manual edits of the
#          sections and the rebuild of centerpoints/bankpoints. Each check prints 'OK' or '**CHECK**' with the offending items.
#          Groups: (A) boundary: counts, names, ids, section geometry; (B) centerline; (C) centerpoints; (D) bankpoints;
#          (E) spacing and the 5 m rule compared with the exception lists; (F) crossings; (G) region points (one per face, attributes,
#          originals, clearance); (H) GeoPackage integrity.
# Inputs : /home/amedeo/Documents/Brenta_mesh_10/layers: the six *_50m.gpkg, the originals regioni_ponti.gpkg (attributes and fid<=176)
#          and centerline_50m_backup_20261117.gpkg (asta_principale, reference for the B chainage); argv[1] = mat11_lines.json (prep_inputs_nvb.py),
#          the breaklines of the walls (mat_id 11), locked.
# Output : print only.
# Run    : python3 scripts/verify3.py WD/mat11_lines.json      (Anaconda python3; read-only)
# Exceptions (decided by the user, 2026-11-18): 5 m rule -> N16000, and (EXCW) the Borgo sections B00000, B00100, B00150, B00200, B00300,
#          B00400, B00450, B00500 whose near vertex belongs to a locked wall line (mat_id 11); straight distance between consecutive sections out of 50+-0.5 m
#          -> pairs N01900-N01950, B11200-B11250, B00250-B00300, B00300-B00350 (B00250, B00300, B00350 moved by hand).
import sys, sqlite3, re, json, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union
from scipy.spatial import cKDTree
L='/home/amedeo/Documents/Brenta_mesh_10/layers'; rd=lambda n: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True)
bl,bd,rg,cp,bp,cl=rd('breaklines_50m'),rd('boundary_50m'),rd('regioni_ponti_50m'),rd('centerpoints_50m'),rd('bankpoints_50m'),rd('centerline_50m')
rg0=rd('regioni_ponti'); ref=rd('centerline_50m_backup_20261117'); A=ref[ref.nome=='asta_principale'].geometry.iloc[0]
EXC5={'N16000'}; EXCW={'B00000','B00100','B00150','B00200','B00300','B00400','B00450','B00500'}; LOCK=set(json.load(open(sys.argv[1]))); EXCD={('N01900','N01950'),('B11200','B11250'),('B00250','B00300'),('B00300','B00350')}
co=lambda g: shapely.get_coordinates(g)
k=0
def out(msg,ok=None):
    global k; k+=1; print(f'{k}. {msg}'+('' if ok is None else ('  OK' if ok else '  **CHECK**')))
issec=lambda n: bool(re.fullmatch(r'[NVB]\d{5}',n))
sec=bd[[issec(n) for n in bd.nome]]; oth=bd[[not issec(n) for n in bd.nome]]
# ---- (A) boundary
out(f'counts: breaklines {len(bl)}, boundary {len(bd)} ({len(oth)} nodestrings + {len(sec)} sections), regioni {len(rg)}, centerpoints {len(cp)}, bankpoints {len(bp)}, centerline {len(cl)}',
    len(oth)==53 and len(sec)==735 and len(cp)==735 and len(bp)==1470 and len(cl)==3)
ok=True; order=[]
for r in 'NVB':
    n=[x for x in sec.nome if x[0]==r]; v=[int(x[1:]) for x in n]; st=0 if r=='B' else 50; ok&= v==list(range(st,st+50*len(v),50)); order+=n
out('section names: per reach consecutive multiples of 50, in reach order N, V, B, unique',ok and list(sec.nome)==order and sec.nome.is_unique)
out(f'boundary: names unique {bd.nome.is_unique}, ids unique {bd.id.is_unique}, no null id/name {bool(bd.id.notna().all() and bd.nome.notna().all())}; section fid 64.. and id 60.. consecutive {list(sec.index)==list(range(64,64+735)) and list(sec.id)==list(range(60,60+735))}',
    bd.nome.is_unique and bd.id.is_unique and list(sec.index)==list(range(64,64+735)) and list(sec.id)==list(range(60,60+735)))
gt=set(sec.geometry.geom_type); np_=[n for n,g in zip(sec.nome,sec.geometry) if len(g.geoms)!=1 or len(co(g))!=2]
zm=[n for n,g in zip(sec.nome,sec.geometry) if np.abs(shapely.get_coordinates(g,include_z=True)[:,2]).max()>0]
out(f'sections: geometry types {gt}, not one part with 2 vertices {np_}, z not 0 {zm}',not np_ and not zm)
# ---- (B) centerline
line={r.ramo:r.geometry for r in cl.itertuples()}; lm=[(r.nome,round(r.lung_m-r.geometry.length,6)) for r in cl.itertuples() if abs(r.lung_m-r.geometry.length)>1e-6]
out(f'centerline: ramo {sorted(line)}, lung_m = geometry length (differences {lm})',sorted(line)==['B','N','V'] and not lm)
b0=LineString(co(sec[sec.nome=='B00000'].geometry.iloc[0])); xb=b0.intersection(A); s0=cl[cl.ramo=='B'].s0_asta.iloc[0]
out(f"centerline B: s0_asta {s0:.3f} = chainage of B00000 on the asta {A.project(xb):.3f}; starts on B00000 ({Point(co(line['B'])[0]).distance(b0):.2e} m); N s0_asta {cl[cl.ramo=='N'].s0_asta.iloc[0]}, V s0_asta null {bool(cl[cl.ramo=='V'].s0_asta.isna().iloc[0])}",
    abs(s0-A.project(xb))<1e-6 and Point(co(line['B'])[0]).distance(b0)<1e-6)
# ---- (C) centerpoints
C={r.nome:r for r in cp.itertuples()}; bad=[]
for nm,g in zip(sec.nome,sec.geometry):
    if nm not in C: bad.append((nm,'missing')); continue
    c=C[nm]; l=LineString(co(g)); p=c.geometry; base=A if nm[0]=='B' else line[nm[0]]; sB=s0 if nm[0]=='B' else 0.0
    if c.stream!=nm[0]: bad.append((nm,'stream',c.stream))
    if l.distance(p)>1e-6: bad.append((nm,'not on section',l.distance(p)))
    if line[nm[0]].distance(p)>1e-6 and base.distance(p)>1e-6: bad.append((nm,'not on centerline'))
    if abs(base.project(p)-sB-c.s_m)>1e-3: bad.append((nm,'s_m',c.s_m,base.project(p)-sB))
out(f'centerpoints: one per section, same name, stream = reach letter, on the section and on the centerline, s_m = chainage within the reach: problems {bad}',not bad and set(C)==set(sec.nome))
dn=[]
for i,n in enumerate(order):
    nx=order[i+1] if i+1<len(order) and order[i+1][0]==n[0] else None; v=C[n].dist_next
    if nx is None:
        if v==v and v is not None: dn.append((n,'last has dist_next',v))
    elif abs(v-(C[nx].s_m-C[n].s_m))>1e-6: dn.append((n,v,C[nx].s_m-C[n].s_m))
out(f'centerpoints: dist_next = s_m(next) - s_m, null for the last of each reach (problems {dn}); s_m starts {C["N00050"].s_m:.2f}/{C["V00050"].s_m:.2f}/{C["B00000"].s_m:.2f}',not dn and C['B00000'].s_m==0)
# ---- (D) bankpoints
B={r.nome:r for r in bp.itertuples()}; bad=[]; TIPI={'max','fallback','muro','manuale','nodestring','nobank','nodata'}
NSg={n:co(g) for n,g in zip(oth.nome,oth.geometry)}
for nm,g in zip(sec.nome,sec.geometry):
    v=co(g)
    for t,p in (('sx',v[0]),('dx',v[-1])):
        q=B.get(f'{nm}_{t}')
        if q is None: bad.append((nm,t,'missing')); continue
        if q.sezione!=nm: bad.append((q.nome,'sezione',q.sezione))
        if not np.array_equal(co(q.geometry)[0],p): bad.append((q.nome,'not = section vertex'))
        if abs(q.s_m-C[nm].s_m)>1e-9: bad.append((q.nome,'s_m'))
        if abs(q.dist_cp-q.geometry.distance(C[nm].geometry))>1e-6: bad.append((q.nome,'dist_cp',q.dist_cp,q.geometry.distance(C[nm].geometry)))
        if q.tipo not in TIPI: bad.append((q.nome,'tipo',q.tipo))
        if q.z_dtm!=q.z_dtm or q.z_dtm is None: bad.append((q.nome,'z null'))
        if q.tipo=='max' and not (q.prom==q.prom and q.prom>=0.05): bad.append((q.nome,'max without prom>=0.05'))
        if q.tipo!='max' and q.prom==q.prom and q.prom is not None: bad.append((q.nome,'prom on non-max',q.tipo))
        if q.tipo=='manuale' and q.regola!='manuale': bad.append((q.nome,'manuale regola',q.regola))
        if q.tipo=='nodestring' and not (q.regola in NSg and any(np.abs(NSg[q.regola]-p).sum(1).min()<1e-6 for _ in [0])): bad.append((q.nome,'nodestring end',q.regola))
        if q.tipo=='muro' and q.regola!='muro': bad.append((q.nome,'muro regola'))
out(f'bankpoints: two per section, sezione, = section vertices (sx first), s_m = centerpoint, dist_cp = distance to centerpoint, tipo/regola/prom coherent, z not null: problems {bad}',not bad and len(B)==1470)
# left/right: the left bankpoint must be on the left of the flow direction (local tangent of the centerline)
lr=[]
for nm,g in zip(sec.nome,sec.geometry):
    base=A if nm[0]=='B' else line[nm[0]]; s=base.project(C[nm].geometry); p0=np.array(base.interpolate(max(s-1,0)).coords[0]); p1=np.array(base.interpolate(s+1).coords[0])
    t=p1-p0; v=co(g)[0]-co(C[nm].geometry)[0]
    if t[0]*v[1]-t[1]*v[0]<=0: lr.append(nm)
out(f'sections run from the left bank (sx) to the right bank (dx): wrong {lr}',not lr)
cnt=collections.Counter(zip(bp.tipo,bp.regola)); out(f'bankpoints by tipo/regola: {dict(cnt)}')
out('bankpoints manuale: '+str(sorted(n for n,r in B.items() if r.tipo=='manuale'))+'; nodestring: '+str(sorted(n for n,r in B.items() if r.tipo=='nodestring')))
# ---- (E) spacing and 5 m rule vs exceptions
P={n:co(C[n].geometry)[0] for n in order}; ds=[]; ch=[]
for a,b in zip(order[:-1],order[1:]):
    if a[0]!=b[0]: continue
    d=C[b].s_m-C[a].s_m; c=float(np.hypot(*(P[a]-P[b])))
    if not 49.5-1e-6<=d<=50.5+1e-6: ds.append((a,b,round(d,3)))
    if not 49.5-1e-6<=c<=50.5+1e-6: ch.append((a,b,round(c,3)))
out(f'spacing along the centerline out of 50+-0.5 m (tolerance 1e-6 m): {ds}')
out(f'straight distance out of 50+-0.5 m (tolerance 1e-6 m): {ch}')
out('spacing anomalies are exactly the listed exceptions '+str(sorted(EXCD)),{(a,b) for a,b,_ in ds+ch}==EXCD)
F={f:co(g)[:,:2] for f,g in bl.geometry.items() if g is not None and not g.is_empty}; keys=list(F); ln=[LineString(F[f]) for f in keys]; TB=shapely.STRtree(ln)
vt=np.vstack(list(F.values())); kd=cKDTree(vt); viol=[]; ncr=0; nl=collections.Counter(); SL=[LineString(co(g)) for g in sec.geometry]; per={}
for nm,l in zip(sec.nome,SL):
    on=[i for i in TB.query(l,predicate='intersects') if l.distance(Point(F[keys[i]][0]))<1e-6 and l.distance(Point(F[keys[i]][-1]))<1e-6]
    hit=[i for i in TB.query(l,predicate='intersects') if i not in on]; nl[len(hit)]+=1; per[nm]=len(hit)
    Pp=[p for i in hit for p in co(l.intersection(ln[i]))]
    for p in Pp:
        ncr+=1; d=[float(np.hypot(*(vt[j]-p))) for j in kd.query_ball_point(p,5.0) if np.hypot(*(vt[j]-p))>1e-3 and all(np.hypot(*(vt[j]-q))>1e-6 for q in Pp)]
        if d:
            j=min((j for j in kd.query_ball_point(p,5.0) if np.hypot(*(vt[j]-p))>1e-3 and all(np.hypot(*(vt[j]-q))>1e-6 for q in Pp)),key=lambda j: np.hypot(*(vt[j]-p)))
            own=[keys[i] for i in TB.query(Point(vt[j]).buffer(1e-6)) if Point(vt[j]).distance(ln[i])<1e-6]
            viol.append((nm,round(min(d),2),'wall' if any(o in LOCK for o in own) else 'other',own))
v5=[v for v in viol if v[0] not in EXC5]
out(f'5 m rule: {ncr} crossings, {len(viol)} with a breakline vertex in (0,5) m; exceptions {sorted(EXC5)}: {[v[:2] for v in viol if v[0] in EXC5]}')
out(f'5 m rule, vertex on a locked wall line (mat_id 11, cannot move): {[v[:2] for v in v5 if v[2]=="wall"]}; exactly the wall exceptions {sorted(EXCW)}',{v[0] for v in v5 if v[2]=='wall'}==EXCW)
out(f'5 m rule outside the exceptions, other vertices: {[v[:2]+(v[3],) for v in v5 if v[2]!="wall"]}',not [v for v in v5 if v[2]!='wall'])
out(f'breaklines crossed per section: {dict(nl)}; sections with != 2: {[(n,c) for n,c in per.items() if c!=2]}')
# ---- (F) crossings between sections and with nodestrings
T=shapely.STRtree(SL); a,b=T.query(SL,predicate='intersects'); x1=[(sec.nome.iloc[i],sec.nome.iloc[j]) for i,j in zip(a,b) if i<j]
NL=[LineString(co(g)) for g in oth.geometry]; a2,b2=T.query(NL,predicate='intersects')
def kind(i,j):
    if NL[i].equals(SL[j]): return 'equal'
    e=[Point(p) for p in co(SL[j])]; x=co(NL[i].intersection(SL[j]))
    return 'section end on nodestring' if all(min(q.distance(Point(p)) for q in e)<1e-6 for p in x) else 'cross'
x2=[(oth.nome.iloc[i],sec.nome.iloc[j],kind(i,j)) for i,j in zip(a2,b2)]
out(f'section-section crossings {x1}; section-nodestring contacts {sorted(x2,key=lambda x:x[1])}; real crossings {[x for x in x2 if x[2]=="cross"]}',not x1 and not [x for x in x2 if x[2]=='cross'])
# ---- (G) region points
U=unary_union(ln+NL+SL); fc=list(polygonize(U)); TF=shapely.STRtree(fc); g=rg[rg.geometry.notna()]; cnt=collections.Counter(); fof={}
for p,f in zip(*TF.query(g.geometry.values,predicate='within')): cnt[int(f)]+=1; fof[g.index[p]]=int(f)
multi=[sorted(i for i,f in fof.items() if f==j) for j,c in cnt.items() if c>1]; empty=[i for i in range(len(fc)) if cnt[i]==0]; outside=[i for i in g.index if i not in fof]
out(f'planar graph: {len(fc)} faces; without point {len(empty)}; with >1 point {multi} (expected []: fid 58 deleted on 19 Nov); points not inside a face {outside}; null-geometry rows {sorted(rg.index[rg.geometry.isna()])} (expected []: fid 65, 135 deleted on 19 Nov)',
    not empty and not multi and not outside and rg.geometry.notna().all())
orig=rg0.loc[[i for i in rg0.index if i<=176 and i not in (58,65,135)]]  # 58, 65, 135 deleted on 2026-11-19 (drop_regions.py)
moved=[i for i in orig.index if not (i in rg.index and ((rg.geometry[i] is None and orig.geometry[i] is None) or (rg.geometry[i] is not None and orig.geometry[i] is not None and rg.geometry[i].equals(orig.geometry[i]))))]
attr=[i for i in orig.index if i in rg.index and any(not (rg.loc[i,c]==orig.loc[i,c] or (rg.loc[i,c]!=rg.loc[i,c] and orig.loc[i,c]!=orig.loc[i,c])) for c in ('nome','mat_id','max_area','buco'))]
out(f'original region points (fid<=176, from regioni_ponti.gpkg): missing or moved {moved} (expected [41], replaced on 9 Nov), attributes changed {attr}',moved==[41] and not attr)
# attribute combinations: every (nome, mat_id, max_area, buco) must exist among the original points
key=lambda r: (r.nome,int(r.mat_id),float(r.max_area),None if r.buco!=r.buco else float(r.buco))
K0={key(r) for r in rg0.itertuples()}; unk=collections.Counter(key(r) for r in rg.itertuples() if key(r) not in K0)
nul=[i for i in rg.index if rg.loc[i,['nome','mat_id','max_area']].isna().any()]
out(f'region attributes: null nome/mat_id/max_area {nul}; combinations not present in the original {dict(unk)}; mat_id per name unique {all(len(set(rg.mat_id[rg.nome==n]))==1 for n in set(rg.nome))}',not nul and not unk)
# clearance from the lines (< 1 m), split into original points and new points
cl1=[(i,rg.nome[i],round(U.distance(gg),2)) for i,gg in g.geometry.items() if U.distance(gg)<1.0]
out(f'region points closer than 1 m to a line: originals {[x for x in cl1 if x[0]<=176]}; new {[x for x in cl1 if x[0]>176]}',all(x[0]<=176 for x in cl1))
# coherence with the original data: the original face (planar graph of the original layers) that contains each new point should carry the same name
ob=rd('breaklines'); obd=rd('boundary'); OL=[LineString(co(gg)[:,:2]) for gg in list(ob.geometry)+list(obd.geometry) if gg is not None and not gg.is_empty]
ofc=list(polygonize(unary_union(OL))); TO=shapely.STRtree(ofc); og=rg0[rg0.geometry.notna()]; oname={}
for p,f in zip(*TO.query(og.geometry.values,predicate='within')): oname.setdefault(int(f),set()).add(og.nome.iloc[p])
mis=[]
for i,gg in g.geometry.items():
    if i<=176: continue
    f=TO.query(gg,predicate='within')
    nm=set().union(*[oname.get(int(x),set()) for x in f]) if len(f) else set()
    if rg.nome[i] not in nm: mis.append((i,rg.nome[i],sorted(nm)))
out(f'new region points whose name differs from the original region at the same place (widened banks expected): {len(mis)} {mis[:30]}')
# ---- (H) GeoPackage integrity
for n in ('breaklines_50m','boundary_50m','regioni_ponti_50m','centerline_50m','centerpoints_50m','bankpoints_50m'):
    c=sqlite3.connect(f'file:{L}/{n}.gpkg?mode=ro',uri=True); t=c.execute("select table_name from gpkg_contents").fetchone()[0]
    ic=c.execute('pragma integrity_check').fetchone()[0]; nn=c.execute(f'select count(*) from "{t}" where geom is not null').fetchone()[0]
    rt=c.execute(f'select count(*) from "rtree_{t}_geom"').fetchone()[0]; srs=c.execute("select srs_id from gpkg_geometry_columns").fetchone()[0]; gty=c.execute("select geometry_type_name from gpkg_geometry_columns").fetchone()[0]
    out(f'{n}: integrity {ic}, rtree {rt} / geometries {nn}, srs {srs}, type {gty}', ic=='ok' and srs==25832)
