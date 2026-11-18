# verify2.py  (stage 2, 2026-11-17; previous: write2.py)
# Purpose: independent checks on the six layers read back from disk (and on the *_backup_20261117 copies): counts, names, identity of the
#          other nodestrings, section vertices = bankpoints, spacing, B00050 vs Ponte_Bordignon_monte, no section-section / section-nodestring
#          crossings, 5 m rule, crossing points preserved, planar graph with one region point per face, original region points kept, and the
#          GeoPackage integrity (SQLite integrity_check, rtree count, SRS 25832, type). Each check prints 'OK' or '**CHECK**'.
# Inputs : /home/amedeo/Documents/Brenta_mesh_10/layers/*_50m.gpkg and *_50m_backup_20261117.gpkg (breaklines, boundary, regioni_ponti).
# Output : print only (24 numbered lines). Expected values are hard-coded: 53 nodestrings, 735 sections, 735 centerpoints, 1470 bankpoints, 3 centerlines.
# Run    : python3 verify2.py      (Anaconda python3; read-only; the working directory is irrelevant)
# Checks on the files read back from disk (independent of the production code).
import sqlite3, hashlib, re, json, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union
from scipy.spatial import cKDTree
# L = layers folder; rd(name) reads a layer with fid as index
L='/home/amedeo/Documents/Brenta_mesh_10/layers'; rd=lambda n: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True)
# current layers: breaklines, boundary, regions, centerpoints, bankpoints, centerline; *o = backups
bl,bd,rg,cp,bp,cl=rd('breaklines_50m'),rd('boundary_50m'),rd('regioni_ponti_50m'),rd('centerpoints_50m'),rd('bankpoints_50m'),rd('centerline_50m')
# backups of breaklines, boundary and regions
blo,bdo,rgo=rd('breaklines_50m_backup_20261117'),rd('boundary_50m_backup_20261117'),rd('regioni_ponti_50m_backup_20261117')
# k = counter of printed checks; out(msg, ok) prints one numbered check
k=0
def out(msg,ok=None):
    global k; k+=1; print(f'{k}. {msg}'+('' if ok is None else ('  OK' if ok else '  **CHECK**')))
# issec: name of a new section (N/V/B + 5 digits); sec = section features, oth = other nodestrings
issec=lambda n: bool(re.fullmatch(r'[NVB]\d{5}',n))
sec=bd[[issec(n) for n in bd.nome]]; oth=bd[[not issec(n) for n in bd.nome]]
out(f'counts: breaklines {len(bl)}, boundary {len(bd)} ({len(oth)} + {len(sec)}), regioni {len(rg)}, centerpoints {len(cp)}, bankpoints {len(bp)}, centerline {len(cl)}',
    len(bl)==len(blo) and len(oth)==53 and len(sec)==735 and len(cp)==735 and len(bp)==1470 and len(cl)==3)
ok=True
for r in 'NVB':
    n=[x for x in sec.nome if x[0]==r]; v=[int(x[1:]) for x in n]; st=0 if r=='B' else 50
    ok&= v==list(range(st,st+50*len(v),50))
out(f"names: N {sum(sec.nome.str[0]=='N')} (N00050-{max(x for x in sec.nome if x[0]=='N')}), V {sum(sec.nome.str[0]=='V')} (..{max(x for x in sec.nome if x[0]=='V')}), B {sum(sec.nome.str[0]=='B')} (B00000-{max(x for x in sec.nome if x[0]=='B')}); unique, consecutive multiples of 50", ok and sec.nome.is_unique and sec.id.is_unique and bd.nome.is_unique)
# co: coordinates of a geometry
co=lambda g: shapely.get_coordinates(g)
same=all(np.array_equal(co(oth.geometry[f]),co(bdo.geometry[f])) and oth.nome[f]==bdo.nome[f] for f in oth.index)
out('the 53 other nodestrings are identical to the backup (user edits kept)',same)
# bpd = bankpoint coordinates by name
bpd={n:co(g)[0] for n,g in zip(bp.nome,bp.geometry)}
ok=all(len(co(g))==2 and np.array_equal(co(g)[0],bpd[n+'_sx']) and np.array_equal(co(g)[1],bpd[n+'_dx']) for n,g in zip(sec.nome,sec.geometry))
out('every section has 2 vertices identical to its bankpoints sx -> dx',ok)
# s_/st = chainage and stream of the centerpoints; P = their coordinates; ds/ch = chainage steps and chord lengths per reach
s_=dict(zip(cp.nome,cp.s_m)); st=dict(zip(cp.nome,cp.stream)); ds=[];ch=[]
P={n:co(g)[0] for n,g in zip(cp.nome,cp.geometry)}
for r in 'NVB':
    n=sorted([x for x in cp.nome if x[0]==r]); d=np.diff([s_[x] for x in n]); ds+=list(d); c=[np.hypot(*(P[a]-P[b])) for a,b in zip(n[:-1],n[1:])]; ch+=[(r,a,round(x,2)) for a,x in zip(n,c) if not 49.5<=x<=50.5]
out(f'spacing along the centerline {min(ds):.2f}-{max(ds):.2f} m; straight distance out of 50+-0.5: {ch}', min(ds)>=49.5 and max(ds)<=50.5)
out(f"B00000 at s=0 of reach B (s_m {s_['B00000']}), first N/V at s_m {s_['N00050']}/{s_['V00050']}; last N {s_['N16050']}, last V {s_['V03000']}, last B {s_['B17650']:.2f}")
# br = Ponte_Bordignon_monte nodestring, b50 = section B00050, clB = centerline of reach B
br=LineString(co(bd[bd.nome=='Ponte_Bordignon_monte'].geometry.iloc[0])); b50=LineString(co(sec[sec.nome=='B00050'].geometry.iloc[0]))
clB=cl[cl.ramo=='B'].geometry.iloc[0]; xb=clB.intersection(br); out(f'B00050 upstream of Ponte Bordignon: centerline distance {clB.project(xb)-s_["B00050"]:.2f} m, min distance section-bridge {b50.distance(br):.2f} m', clB.project(xb)-s_['B00050']>=5)
# SL = section lines; T = index; x1 = section/section crossings; a2/b2 = section/nodestring crossings
SL=[LineString(co(g)) for g in sec.geometry]; T=shapely.STRtree(SL); a,b=T.query(SL,predicate='intersects')
x1=[(i,j) for i,j in zip(a,b) if i<j]; a2,b2=T.query([LineString(co(g)) for g in oth.geometry],predicate='intersects')
out(f'section-section crossings {len(x1)}, section-nodestring crossings {len(a2)}',len(x1)==0 and len(a2)==0)
# F = breakline coordinates; ln = LineStrings; TB = index; vt/kd = all vertices and KD-tree; viol = 5 m violations
F={f:co(g) for f,g in bl.geometry.items() if g is not None and not g.is_empty}; keys=list(F); ln=[LineString(F[f]) for f in keys]; TB=shapely.STRtree(ln)
vt=np.vstack(list(F.values())); kd=cKDTree(vt); viol=[]; ncr=0; nl=collections.Counter()
for nm,l in zip(sec.nome,SL):
    on=[i for i in TB.query(l,predicate='intersects') if l.distance(Point(F[keys[i]][0]))<1e-6 and l.distance(Point(F[keys[i]][-1]))<1e-6]
    hit=[i for i in TB.query(l,predicate='intersects') if i not in on]; nl[len(hit)]+=1
    Pp=[p for i in hit for p in co(l.intersection(ln[i]))]
    for p in Pp:
        ncr+=1; d=[float(np.hypot(*(vt[j]-p))) for j in kd.query_ball_point(p,5.0) if np.hypot(*(vt[j]-p))>1e-3 and all(np.hypot(*(vt[j]-q))>1e-6 for q in Pp)]
        if d: viol.append((nm,round(min(d),2)))
out(f'5 m rule: {ncr} crossings, {len(viol)} with a breakline vertex in (0,5) m: {viol}')
out(f'breaklines crossed per section: {dict(nl)}')
# OU = union of the old breaklines; every crossing of a section with a new breakline must lie on it too
OU=unary_union([g for g in blo.geometry if g is not None and not g.is_empty]); lost=0; tot=0
for l in SL:
    for i in TB.query(l,predicate='intersects'):
        for p in co(l.intersection(ln[i])):
            tot+=1; lost+=OU.distance(Point(p))>1e-4
out(f'crossing points of the sections lie on the previous breaklines too (crossings not moved): {tot-lost}/{tot}',lost==0)
# NS = other nodestrings; lostn = nodestring crossings of the backup no longer on the new breaklines
NS=[LineString(co(g)) for g in oth.geometry]; NU=unary_union([ln[i] for i in range(len(ln))])
lostn=sum(NU.distance(Point(p))>1e-4 for l in NS for g in blo.geometry if g is not None and not g.is_empty and g.intersects(l) for p in co(l.intersection(g)))
out(f'nodestring/breakline crossings of the backup still on the new breaklines: lost {lostn}',lostn==0)
# breaklines identical to the backup
untouched=[f for f in F if f in blo.index and blo.geometry[f] is not None and np.array_equal(co(blo.geometry[f]),F[f])]
out(f'breaklines: {len(untouched)} identical to backup, {len(F)-len(untouched)} changed; id field unchanged {bool((bl.id.fillna(-1)==blo.id.fillna(-1)).all())}')
# planar graph: faces; each face must hold exactly one region point (except the pair 57/58)
U=unary_union(ln+NS+SL); fc=list(polygonize(U)); T=shapely.STRtree(fc); g=rg[rg.geometry.notna()]; cnt=collections.Counter()
for p,f in zip(*T.query(g.geometry.values,predicate='within')): cnt[int(f)]+=1
multi=[i for i,c in cnt.items() if c>1]; empty=[i for i in range(len(fc)) if cnt[i]==0]
out(f'planar graph: {len(fc)} faces, without point {len(empty)}, with >1 point {len(multi)} (expected 1: 57/58), null-geometry rows {int(rg.geometry.isna().sum())}',len(empty)==0 and len(multi)==1)
# region points 485, 504, 568: present/removed and their clearance
for q in (485,504,568): out(f'region point {q}: '+('present, %.2f m from lines'%U.distance(rg.geometry[q]) if q in rg.index else 'removed'))
# all original region points (fid<=176) must still be present and unmoved
orig=rgo.loc[[i for i in rgo.index if i<=176]]; out('all original region points (fid<=176) still present and unmoved',all(i in rg.index and ((rg.geometry[i] is None and orig.geometry[i] is None) or rg.geometry[i].equals(orig.geometry[i])) for i in orig.index))
# GeoPackage integrity: sqlite integrity_check, rtree size = geometry count, SRS 25832
for n in ('breaklines_50m','boundary_50m','regioni_ponti_50m','centerline_50m','centerpoints_50m','bankpoints_50m'):
    c=sqlite3.connect(f'file:{L}/{n}.gpkg?mode=ro',uri=True); t=c.execute("select table_name from gpkg_contents").fetchone()[0]
    ic=c.execute('pragma integrity_check').fetchone()[0]; nn=c.execute(f'select count(*) from "{t}" where geom is not null').fetchone()[0]
    rt=c.execute(f'select count(*) from "rtree_{t}_geom"').fetchone()[0]; srs=c.execute("select srs_id from gpkg_geometry_columns").fetchone()[0]; gt=c.execute("select geometry_type_name from gpkg_geometry_columns").fetchone()[0]
    out(f'{n}: integrity {ic}, rtree {rt} = geometries {nn}, srs {srs}, type {gt}', ic=='ok' and rt==nn and srs==25832)
