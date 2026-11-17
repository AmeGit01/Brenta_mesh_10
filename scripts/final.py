# final.py  (step 19: final checks on the written layers + export of the section table)
# Purpose: (1) check the '5 m rule': at every point where a section crosses a breakline, no breakline vertex should lie within 5 m (except the
#          vertex coinciding with the crossing); (2) check clearance of the new region points; (3) write the CSV table of all sections.
# Inputs : layers/{breaklines,boundary,regioni_ponti,bankpoints,centerpoints}_50m.gpkg (absolute path), WD/work/newfaces.pkl; core.py from WD/work.
# Output : /home/amedeo/Documents/Brenta_mesh_10/docs/Brenta_sections_50m_mesh10.csv (OVERWRITTEN, absolute path); printed statistics.
# Run    : python3 final.py WD      (Anaconda python3)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import csv, json
from scipy.spatial import cKDTree
L='/home/amedeo/Documents/Brenta_mesh_10/layers'
rd=lambda n: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True)
bl,bd,rg,bp,cp=rd('breaklines_50m'),rd('boundary_50m'),rd('regioni_ponti_50m'),rd('bankpoints_50m'),rd('centerpoints_50m')
def co(g): return shapely.get_coordinates(next(iter(shapely.get_parts(g))))
# sec = section nodestrings (names S/V + 5 digits); oth = all other boundary features.
sec=bd[[(n[0] in 'SV') and n[1:6].isdigit() for n in bd.nome]]
oth=bd[[not((n[0] in 'SV') and n[1:6].isdigit()) for n in bd.nome]]
# F[fid] = coordinates of every non-empty breakline in breaklines_50m.
F={k:co(g) for k,g in bl.dropna(subset=['geometry']).geometry.items() if not g.is_empty}
# NF/tb/tk: bed outline segments (tk is not used afterwards).
NF=pickle.load(open(f'{SP}/work/newfaces.pkl','rb')); fc,rows=NF['fc'],NF['rows']
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); tk={key(s) for s in tb}
# NOTE: despite the name 'toe', these are ALL breaklines of breaklines_50m. vt = all their vertices (KD-tree kd); ln = LineStrings; T = STRtree.
toe=F
print('toe lines',len(toe))
vt=np.vstack(list(toe.values())); kd=cKDTree(vt); ln={k:LineString(v) for k,v in toe.items()}; keys=list(ln); T=shapely.STRtree(list(ln.values()))
# For each section: P = set of crossing points with any breakline (rounded 1e-4 m). For each crossing, vertices within 5.0 m are looked up in the KD-tree;
# distances <= 1 mm are discarded (the crossing coincides with a vertex). Remaining distances (smallest) -> violation (section, point, distance).
viol=[]; n=0
for nm,g in zip(sec.nome,sec.geometry):
    l=LineString(co(g)); P=set()
    for i in T.query(l,predicate='intersects'):
        x=shapely.get_coordinates(l.intersection(ln[keys[i]]))
        for p in x: P.add((round(float(p[0]),4),round(float(p[1]),4)))
    for p in P:
        d=kd.query_ball_point(p,5.0); v=[float(np.hypot(*(vt[j]-np.array(p)))) for j in d]; v=sorted({round(x,3) for x in v if x>1e-3})
        n+=1
        if v: viol.append((nm,p,v[0]))
print('5 m rule: crossings',n,'with a vertex in (0,5) m',len(viol),'sections',len({v[0] for v in viol}),'min dist',min(v[2] for v in viol))
print('5 m rule below 0.5 m:',sorted([(v[0],v[2]) for v in viol if v[2]<0.5],key=lambda x:x[1])[:15], 'count', sum(v[2]<0.5 for v in viol))
# regnew = region points added by write.py: hard-coded as fid > 176 (176 = largest fid of the original regioni_ponti layer).
# Clearance of the new points from all breaklines and boundary features (expected >= 1 m; those < 1 m are listed).
regnew=rg[rg.index>176]; 
print('regioni by nome',rg.dropna(subset=['geometry']).nome.value_counts().head(12).to_dict())
# (the assignment below is immediately superseded by the import on the next line)
lines=unary_union=None
from shapely.ops import unary_union
all_=unary_union([LineString(v) for v in F.values()]+[LineString(co(g)) for g in bd.geometry])
d=shapely.distance(all_,regnew.geometry.values); print('new points clear',round(float(d.min()),2),'<1 m:',[(int(i),round(float(x),2),regnew.nome[i]) for i,x in zip(regnew.index,d) if x<1])
# CSV: one row per section (order of centerpoints): left/right bankpoint z, distance from the centerpoint, kind, rule, prominence (blank if None/NaN),
# and the section length (m).
out=[]
for nm,s in zip(cp.nome,cp.s_m):
    a=bp[bp.sezione==nm]
    get=lambda t: a[a.nome.str.endswith('_'+t)].iloc[0]
    sx,dx=get('sx'),get('dx'); g=sec[sec.nome==nm].geometry.iloc[0]; c=co(g)
    out.append([nm,round(s,2),round(sx.z_dtm,3),round(sx.dist_cp,2),sx.tipo,sx.regola,'' if sx.prom is None or sx.prom!=sx.prom else round(sx.prom,3),round(dx.z_dtm,3),round(dx.dist_cp,2),dx.tipo,dx.regola,'' if dx.prom is None or dx.prom!=dx.prom else round(dx.prom,3),round(float(np.hypot(*(c[1]-c[0]))),2)])
# Header columns: sezione s_m z_sx dist_cp_sx tipo_sx regola_sx prom_sx z_dx dist_cp_dx tipo_dx regola_dx prom_dx lunghezza_m.
with open('/home/amedeo/Documents/Brenta_mesh_10/docs/Brenta_sections_50m_mesh10.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow('sezione s_m z_sx dist_cp_sx tipo_sx regola_sx prom_sx z_dx dist_cp_dx tipo_dx regola_dx prom_dx lunghezza_m'.split()); w.writerows(out)
print('csv',len(out))
