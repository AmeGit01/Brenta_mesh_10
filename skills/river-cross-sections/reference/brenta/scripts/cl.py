# cl.py - step 4. Computes the raw centerlines of the main channel ('main', from BC_caldonazzo to BC_brenta_valle) and of the
# Brenta vecchio ('vecchio') as paths on a fine Voronoi skeleton of the bed polygon, with a cost that prefers the centre of the channel.
# Inputs : WD/work/graph.pkl (via core.load_graph); WD/in/boundary.gpkg (indexed by 'nome': BC_caldonazzo, BC_brenta_valle,
#          divergenza_valle_brenta_vecchio, boale_brenta_vecchio_monte/valle, check_portata_Brenta_vecchio)
# Outputs: WD/work/rawcl.pkl (dict P = bed polygon, main = Nx2 array of path vertices, vecchio = Mx2 array);
#          WD/work/altmain.pkl (Nx2 array: alternative main route through the southern meander, for comparison only);
#          diagnostics on stdout
# Usage  : python3 cl.py WD      (Anaconda python3; needs core.py in WD/work)
# Hard-coded coordinates (EPSG:25832, m) below are manually chosen waypoints.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import networkx as nx
from scipy.spatial import Voronoi, cKDTree
from scipy.ndimage import gaussian_filter1d
from shapely.ops import unary_union
# faces, rows from graph.pkl
faces,rows=load_graph()
# bed faces (class 'bed' per core.cls)
bedf=[faces[r['face']] for r in rows if cls(r['nome'])=='bed']
# bed = union of bed faces (0.02 m buffer to close gaps); prints area (m2) and centroid of its holes (islands)
bed=unary_union([f.buffer(0.02) for f in bedf]); print('interiors',[round(Polygon(i).area,1) for i in bed.interiors],[[int(c) for c in Polygon(i).centroid.coords[0]] for i in bed.interiors])
# P = bed polygon with only the holes larger than 1000 m2 (smaller islands are filled)
P=Polygon(bed.exterior,[i for i in bed.interiors if Polygon(i).area>1000])
# fine skeleton: 0.5 m seeds on narrow (Brenta vecchio) window, 1.5 elsewhere
# fine skeleton: Voronoi seeds every 0.6 m along all rings of P (the original comment says 0.5/1.5 m but the code uses 0.6 m everywhere)
a=np.vstack([shapely.get_coordinates(shapely.line_interpolate_point(r,np.arange(0,r.length,0.6))) for r in [P.exterior]+list(P.interiors)]); print('seeds',len(a))
# V = Voronoi of seeds a; vv = vertices; ins = vertex inside P
V=Voronoi(a); vv=V.vertices; ins=shapely.contains_xy(P,vv[:,0],vv[:,1])
# g = skeleton graph
g=nx.Graph()
# kd on seeds: dbd[k] = distance (m) from Voronoi vertex k to the nearest seed ~ distance to the bed boundary
kd=cKDTree(a); dbd,_=kd.query(vv)
for p,q in V.ridge_vertices:
    # ridge (p,q) with both vertices inside P and shorter than 40 m
    if p>=0 and q>=0 and ins[p] and ins[q]:
        d=float(np.hypot(*(vv[p]-vv[q])))
        # w = length (m); c = cost = length / max(min boundary distance of the 2 vertices, 0.15 m): cheap in the middle of the channel, expensive near the banks
        if d<40: g.add_edge(p,q,w=d,c=d/(max(min(dbd[p],dbd[q]),0.15)**1.0))   # central-preferring cost
# components, largest first
cc=sorted(nx.connected_components(g),key=len,reverse=True); print('comps',[len(c) for c in cc[:6]])

# bridge secondary components (>=80 nodes, e.g. strips separated by islands) to the others: link the two closest, >50 m apart, contact points (<=25 m)
for c in cc[1:]:
    # skip small components (<80 nodes)
    if len(c)<80: continue
    # a = node ids of this component; ta = its KD-tree
    a=np.array(list(c)); ta=cKDTree(vv[a])
    # others = nodes of the other big components; d,i = distance to / index of the nearest node of this component
    others=np.array([n for cc2 in cc if cc2 is not c and len(cc2)>=80 for n in cc2])
    # (order is computed but never used)
    d,i=ta.query(vv[others]); order=np.argsort(d)[:1]
    # two nearest separated contacts (both ends of the strip)
    # picked = indexes (into others) of the chosen contacts
    picked=[]
    for j in np.argsort(d):
        if d[j]>25: break
        p=vv[others[j]]
        if all(np.hypot(*(p-vv[others[k]]))>50 for k in picked):
            # add a bridging edge, cost doubled (2*distance) to discourage its use unless necessary
            picked.append(j); g.add_edge(int(others[j]),int(a[i[j]]),w=float(d[j]),c=float(d[j])*2)
        if len(picked)==2: break
    print('bridged comp',len(c),[round(float(d[j]),2) for j in picked],[vv[others[j]].round().tolist() for j in picked])
# main component after bridging
cc=sorted(nx.connected_components(g),key=len,reverse=True); print('comps after',[len(c) for c in cc[:4]])
# H = main component; nodes/xy = node ids and coordinates; T = KD-tree of them
H=g.subgraph(cc[0]); nodes=np.array(list(H.nodes)); xy=vv[nodes]; T=cKDTree(xy)
# boundary lines indexed by name
bd=gpd.read_file(f'{SP}/in/boundary.gpkg').set_index('nome')
# nn(p): id of the skeleton node nearest to point p; cen(n): centroid xy of boundary line named n
def nn(p): return int(nodes[T.query(p)[1]])
def cen(n): return np.array(bd.geometry[n].centroid.coords[0][:2])
# A = start node (inflow BC_caldonazzo), Z = end node (BC_brenta_valle)
A=nn(cen('BC_caldonazzo')); Z=nn(cen('BC_brenta_valle'))
# mp = main path: least-cost path over cost c
mp=nx.shortest_path(H,A,Z,weight='c')
print('main nodes',len(mp))
# alternative upstream route through the southern meander (compare)
try:
    # M1 = skeleton node near a manually chosen point inside the southern meander; alt = A->M1 then M1->Z; saved for comparison, not used later
    M1=nn(np.array([678150.,5096930.]))
    print('meander node',vv[M1].round(1))
    alt=nx.shortest_path(H,A,M1,weight='c'); alt2=nx.shortest_path(H,M1,Z,weight='c')
    pa=alt+alt2[1:]; print('alt len via meander',round(float(np.hypot(*np.diff(vv[pa],axis=0).T).sum())))
    pickle.dump(vv[pa],open(f'{SP}/work/altmain.pkl','wb')); 
except Exception as e: print('alt fail',e)

# Brenta vecchio : waypoints
# wp = ordered waypoints of the old Brenta (divergence, two manual points, boale monte/valle, check_portata)
wp=[cen('divergenza_valle_brenta_vecchio'),np.array([687960.,5102512.]),np.array([688400.,5102655.]),cen('boale_brenta_vecchio_monte'),cen('boale_brenta_vecchio_valle'),cen('check_portata_Brenta_vecchio')]
# ids = nearest nodes; prints the snapping distance (m) for each waypoint
ids=[nn(p) for p in wp]; print('wp dist',[round(float(np.hypot(*(vv[i]-p))),2) for i,p in zip(ids,wp)])
# vp = vecchio node path: concatenation of shortest paths (weight w = plain length) through consecutive waypoints
vp=[]
for a0,b0 in zip(ids[:-1],ids[1:]):
    p=nx.shortest_path(H,a0,b0,weight='w'); vp+=p if not vp else p[1:]
# extend vecchio to confluence: to nearest main node downstream of link (s by main nodes)
# mset = main-path nodes; kdm = their KD-tree (used only for the final check distances)
mset=np.array(mp); kdm=cKDTree(vv[mset]); 
last=vp[-1]
# path from last to the main node at link_borgo_monte
conf=nx.shortest_path(H,last,nn(np.array([689850.,5102944.])),weight='w'); vp+=conf[1:]
# pl(p): polyline length (m) of node path p; main/vecchio lengths printed
def pl(p): a=vv[p]; return float(np.hypot(*np.diff(a,axis=0).T).sum())
print('main L',round(pl(mp)),'vecchio L',round(pl(vp)))
# prints head/tail of vecchio and its distance (m) from the main path at confluence and at the divergence
print('vecchio head/tail',vv[vp[0]].round(1),vv[vp[-1]].round(1), 'main at conf dist',round(float(kdm.query(vv[vp[-1]])[0]),2),'at div',round(float(kdm.query(vv[vp[0]])[0]),2))
# save raw centerlines (vertex coordinates, not yet smoothed/resampled)
pickle.dump(dict(P=P,main=vv[mp],vecchio=vv[vp]),open(f'{SP}/work/rawcl.pkl','wb'))
