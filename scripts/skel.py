# skel.py - step 2. Builds a Voronoi-based skeleton (medial axis) of the riverbed ('bed' faces) as a networkx graph.
# Inputs : WD/work/graph.pkl (graph.py)
# Outputs: WD/work/skel.pkl (dict bed, cor, g, vv) - read by net.py; diagnostics on stdout
# Usage  : python3 skel.py WD      (Anaconda python3; geopandas, shapely, scipy, networkx)
# Note   : this is an earlier skeleton (seeds every 1.5 m); cl.py later recomputes a finer one on its own.
import pickle, sys, numpy as np, shapely, geopandas as gpd, warnings, networkx as nx
warnings.filterwarnings('ignore')
from shapely.ops import unary_union
from shapely.geometry import LineString, Point
from scipy.spatial import Voronoi
# SP = working directory WD
SP=sys.argv[1]
# faces = polygons of the planar graph, rows = faces with a region name (see graph.py)
G=pickle.load(open(f'{SP}/work/graph.pkl','rb')); faces=G['faces']; rows=G['rows']
# all distinct region names
names=sorted({r['nome'] for r in rows})
# isbed / isbank: same logic as core.cls: bed classes, and bank classes (sponda*, *sponda_nat, muro, pilone-borgo, sottopasso-borgo)
isbed=lambda n: n in('bed','bed_borgo','Ponte_Bordignon','raccordo_sifone_brentavecchio') or n.endswith('_bed') or n.startswith('source_')
isbank=lambda n: n.startswith('sponda') or n.endswith('sponda_nat') or n=='muro' or n in('pilone-borgo','sottopasso-borgo')
# bed = union of bed faces, each buffered by 0.02 m so that adjacent faces fuse despite rounding gaps
bed=unary_union([faces[r['face']].buffer(0.02) for r in rows if isbed(r['nome'])])
# cor = union of bed + bank faces (the whole 'corridor' bed+sponda), same 0.02 m buffer
cor=unary_union([faces[r['face']].buffer(0.02) for r in rows if isbed(r['nome']) or isbank(r['nome'])])
# prints geometry type, number of parts and area in hectares of bed and cor
print('bed',bed.geom_type,len(getattr(bed,'geoms',[bed])),round(bed.area/1e4,1),'cor',cor.geom_type,len(getattr(cor,'geoms',[cor])),round(cor.area/1e4,1))
# bed parts sorted by area (descending); the 8 largest are printed with area, bounds and number of holes
parts=sorted(getattr(bed,'geoms',[bed]),key=lambda p:-p.area)
for p in parts[:8]: print(' bedpart',round(p.area),[int(x) for x in p.bounds],len(p.interiors))
# P = the polygon used for the skeleton: the single part, otherwise the whole multipart bed
P=parts[0] if len(parts)==1 else bed
# skeleton
# skeleton: Voronoi seed points sampled every ~1.5 m along every ring (exterior and holes) of P
pts=[]
# loop over the rings of P (handles Polygon or MultiPolygon)
for ring in ([P.exterior]+list(P.interiors) if P.geom_type=='Polygon' else [r for q in P.geoms for r in [q.exterior]+list(q.interiors)]):
    # L = ring length (m); n = number of seeds (spacing ~1.5 m)
    L=ring.length; n=int(L/1.5)+1
    pts.append(shapely.get_coordinates(shapely.line_interpolate_point(ring,np.linspace(0,L,n,endpoint=False))))
# pts = all seeds (K,2); Voronoi diagram of the seeds; vv = Voronoi vertices
pts=np.vstack(pts); print('seeds',len(pts))
V=Voronoi(pts); vv=V.vertices
# inside[k] = True if Voronoi vertex k is inside P; Voronoi vertices inside the polygon approximate the medial axis
inside=shapely.contains_xy(P,vv[:,0],vv[:,1])
# g = graph of the skeleton
g=nx.Graph()
# ridge_vertices: pairs of Voronoi vertices joined by a Voronoi ridge (-1 = vertex at infinity, skipped)
for a,b in V.ridge_vertices:
    if a>=0 and b>=0 and inside[a] and inside[b]:
        # d = ridge length (m); keep only short ridges (<30 m) fully inside P; edge weight = length
        d=float(np.hypot(*(vv[a]-vv[b])))
        if d<30 and P.contains(LineString([vv[a],vv[b]])): g.add_edge(a,b,weight=d)
# connected components of the skeleton, largest first; sizes of the 6 largest printed
cc=sorted(nx.connected_components(g),key=len,reverse=True); print('skeleton comps',[len(c) for c in cc[:6]])
# save: bed, cor (shapely geometries), g (networkx Graph, nodes = Voronoi vertex indices), vv (vertex coordinates)
pickle.dump(dict(bed=bed,cor=cor,g=g,vv=vv),open(f'{SP}/work/skel.pkl','wb'))
