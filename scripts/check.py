# check.py  (step 19: verification of the written layers, read back from disk; independent of the pipeline scripts)
# Purpose: sanity-check layers/*_50m.gpkg against the original layers. Print-only (no assertions, no files written);
#          the numbered lines 1-11 printed are described in docs/scripts/check.md together with the expected result.
# Inputs : /home/amedeo/Documents/Brenta_mesh_10/layers/{breaklines,boundary,regioni_ponti}.gpkg (originals) and the six *_50m.gpkg.
# Run    : python3 check.py      (Anaconda python3; takes NO argument, does not import core.py)
import sys, numpy as np, shapely, geopandas as gpd, sqlite3, warnings, collections, json
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
# L = layers directory; rd(name) = read layer `name` with the GPKG fid as the DataFrame index.
L='/home/amedeo/Documents/Brenta_mesh_10/layers'
rd=lambda n,**k: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True,**k)
# *0 = original layers; without suffix = *_50m; cl/cp/bp = centerline, centerpoints, bankpoints.
bl0,bd0,rg0=rd('breaklines'),rd('boundary'),rd('regioni_ponti')
bl,bd,rg=rd('breaklines_50m'),rd('boundary_50m'),rd('regioni_ponti_50m')
cl,cp,bp=rd('centerline_50m'),rd('centerpoints_50m'),rd('bankpoints_50m')
# n(): shorthand for print.
n=lambda s,*a: print(s,*a)
n('1. counts: breaklines',len(bl),'(orig',len(bl0),') boundary',len(bd),'(orig',len(bd0),'+',len(bd)-len(bd0),') regioni',len(rg),'(orig',len(rg0),') cl',len(cl),'cp',len(cp),'bp',len(bp))
# new = boundary features added by write.py (the sections).
new=bd[~bd.index.isin(bd0.index)]
n('2. names unique',bd.nome.is_unique,'ids unique',bd.id.is_unique,'new nome',new.nome.iloc[0],new.nome.iloc[-1],'new sections',len(new),'fid',new.index.min(),new.index.max(),'id',new.id.min(),new.id.max(), 'main',int(new.nome.str.startswith('S').sum()),'vecchio',int(new.nome.str.startswith('V').sum()))
# Check 3: GPKG internal consistency via sqlite: integrity_check, feature_count in gpkg_ogr_contents, rtree rows, table rows, SRS id, geometry type/Z/M.
for f in ('breaklines','boundary','regioni_ponti'):
    a=f'{L}/{f}_50m.gpkg'; c=sqlite3.connect(a); 
    print('3.',f,c.execute('pragma integrity_check').fetchone()[0],c.execute('select feature_count from gpkg_ogr_contents').fetchone(),c.execute(f'select count(*) from rtree_{f}_geom').fetchone(),c.execute('select count(*) from '+f).fetchone(),c.execute('select srs_id from gpkg_geometry_columns').fetchone(),c.execute('select geometry_type_name,z,m from gpkg_geometry_columns').fetchone())
    c.close()
print('   fields',list(bd.columns),list(bl.columns),list(rg.columns))
# co(): coordinates of the first part of a (multi)geometry as an (N,2) array.
# Check 4: features unchanged w.r.t. the originals (bit-identical geometry, tolerance 0).
def co(g): return shapely.get_coordinates(next(iter(shapely.get_parts(g))))
# unchanged features bit identical (compare coords)
same=lambda A,B: sum(1 for k in A.index if k in B.index and A.geometry[k] is not None and B.geometry[k] is not None and not (A.geometry[k].is_empty or B.geometry[k].is_empty) and (A.geometry[k].equals_exact(B.geometry[k],0)))
print('4. breaklines identical to original',same(bl0.dropna(subset=['geometry']),bl.dropna(subset=['geometry'])),'of',len(bl0.dropna(subset=['geometry'])),'; boundary old',same(bd0,bd),'of',len(bd0),'; regioni kept identical',same(rg0,rg),'of',len(rg0))
print('   regioni dropped',sorted(set(rg0.index)-set(rg.index)))
# Checks 5-6, per stream: ds = difference of s_m between consecutive centerpoints, ch = straight distance between consecutive centerpoints,
# both expected within 50 +- 0.5 m; rs = s recomputed by projecting centerpoints on the centerline; ang = deviation from perpendicularity
# between the centerline chord (s-1, s+1 m) and the section; ol = number of sections whose first vertex lies on the left of the direction of travel.
# spacing
res={}
bpxy={r.nome:(r.geometry.x,r.geometry.y) for r in bp.itertuples()}
errv=0
tilted=[]
for stream,prefix in (('asta_principale','S'),('brenta_vecchio','V')):
    ln=cl[cl.nome==stream].geometry.iloc[0]; sec=new[new.nome.str.startswith(prefix)]; cpg=cp[cp.nome.str.startswith(prefix)].sort_values('s_m')
    s=cpg.s_m.values; ch=np.hypot(np.diff(cpg.geometry.x.values),np.diff(cpg.geometry.y.values)); ds=np.diff(s)
    # re-project centerpoints onto centerline independently
    rs=np.array([ln.project(g) for g in cpg.geometry]); 
    print(f'5. {stream} sections {len(s)} ds along centerline [{ds.min():.2f},{ds.max():.2f}] straight [{ch.min():.2f},{ch.max():.2f}]; ds out of 49.5-50.5:',int(((ds<49.5-1e-6)|(ds>50.5+1e-6)).sum()),'chord out:',int(((ch<49.5-1e-6)|(ch>50.5+1e-6)).sum()),'at',np.round(s[:-1][(ch<49.5)|(ch>50.5)],1).tolist(),np.round(ch[(ch<49.5)|(ch>50.5)],2).tolist(),'|s-proj|max',round(float(np.abs(rs-s).max()),3),'first',s[0],'dist last to end',round(ln.length-s[-1],2))
    ang=[]; ol=0
    for r in sec.itertuples():
        c=co(r.geometry); 
        if len(c)!=2: errv+=1
        if not (np.allclose(c[0],bpxy[r.nome+'_sx']) and np.allclose(c[1],bpxy[r.nome+'_dx'])): errv+=1
        sc=cpg[cpg.nome==r.nome].s_m.iloc[0]; a=np.array(ln.interpolate(max(sc-1,0)).coords[0][:2]); b=np.array(ln.interpolate(min(sc+1,ln.length)).coords[0][:2]); t=(b-a)/np.hypot(*(b-a)); d=(c[1]-c[0])/np.hypot(*(c[1]-c[0])); ang.append(abs(float(np.degrees(np.arcsin(abs(t@d))))))
        ol+= (np.cross(t,c[0]-((c[0]+c[1])/2))>0)
    print(f'6. {stream} perpendicular max dev deg {max(ang):.2e}; first vertex on orographic left: {ol}/{len(sec)}')
print('   errors 2-vertices/bankpoints match:',errv)
# Checks 7-8: section-section crossings and crossings of sections with the other (non-section) boundary nodestrings.
# z mostly tested later
g0=[LineString(co(g)) for g in bl.dropna(subset=['geometry']).geometry if not g.is_empty]; rg=rg.dropna(subset=['geometry']); g_b=[LineString(co(g)) for g in bd.geometry]; g_b_old=[LineString(co(g)) for k,g in zip(bd.index,bd.geometry) if k in bd0.index]
Tbl=shapely.STRtree(g0); Tbold=shapely.STRtree(g_b_old)
secL=[LineString(co(g)) for g in new.geometry]
ST=shapely.STRtree(secL); a,b=ST.query(secL,predicate='intersects'); print('7. section-section crossings',int(sum(a<b)))
a,b=Tbold.query(secL,predicate='intersects'); print('8. section vs other nodestrings crossings',len(a),[(new.nome.iloc[x]) for x in a][:20])
# planar graph
# Check 9: planar graph of breaklines+boundary: number of faces, minimum area, region points per face (expected exactly 1), faces with several points, points outside faces.
fc=list(polygonize(unary_union(g0+g_b))); A=np.array([f.area for f in fc]); T=shapely.STRtree(fc); ix=T.query(rg.geometry.values,predicate='within'); pc=np.bincount(ix[1],minlength=len(fc))
print('9. faces',len(fc),'min area',round(float(A.min()),3),'points per face',dict(zip(*np.unique(pc,return_counts=True))),'multi fid',[[int(rg.index[j]) for j in ix[0][ix[1]==i]] for i in np.where(pc>1)[0]],'points outside',[int(rg.index[j]) for j in set(range(len(rg)))-set(ix[0])])
# number of breaklines crossed per section : toe count
# Check 10: how many breaklines each section intersects (histogram). Check 11: bankpoints by kind (tipo) and rule (regola).
bdry_toe=[]
cross=[]
for l in secL:
    idx=Tbl.query(l,predicate='intersects'); cross.append(len(idx))
print('10. breaklines touched by each section',dict(sorted(collections.Counter(cross).items())))
print('11. bp counts by tipo',bp.tipo.value_counts().to_dict(),'regola',bp.regola.value_counts().to_dict())
