# net.py - step 3. Extracts from the skeleton (skel.pkl) the shortest paths from the main inflow BC_caldonazzo to the outflow
# BC_brenta_valle and from each other BC_* boundary to the main path (tributaries); smooths them and plots the widths of bed and bed+bank corridor.
# Inputs : WD/work/skel.pkl (skel.py); WD/in/boundary.gpkg (lines named BC_*: boundary-condition lines)
# Outputs: WD/work/net.pkl (dict paths: name -> list of skeleton node ids, T: name -> terminal node id); WD/work/w.png (width plot); diagnostics on stdout
# Usage  : python3 net.py WD      (Anaconda python3; geopandas, shapely, scipy, networkx, matplotlib)
# Note   : net.pkl is not read by the later scripts of this folder (cl.py rebuilds the centerline by itself); the step is exploratory/diagnostic.
import pickle, sys, numpy as np, shapely, geopandas as gpd, warnings, networkx as nx, json
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from scipy.ndimage import gaussian_filter1d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
# SP = working directory WD
SP=sys.argv[1]
# S = skeleton data: g (graph), vv (vertex xy), bed and cor (polygons)
S=pickle.load(open(f'{SP}/work/skel.pkl','rb')); g,vv,bed,cor=S['g'],S['vv'],S['bed'],S['cor']
# connected components of the skeleton, largest first; bounding boxes of components 2-4 printed
cc=sorted(nx.connected_components(g),key=len,reverse=True)
for c in cc[1:4]:
    a=vv[list(c)]; print('comp',len(c),a.min(0).round(),a.max(0).round())
# main = largest component; H = its subgraph; nodes = array of node ids; xy = their coordinates
main=cc[0]; H=g.subgraph(main).copy(); nodes=np.array(list(H.nodes)); xy=vv[nodes]
# bd = boundary lines (GeoDataFrame)
bd=gpd.read_file(f'{SP}/in/boundary.gpkg')
# near(x,y): id of the skeleton node closest to point (x,y)
def near(x,y): 
    return int(nodes[np.argmin((xy[:,0]-x)**2+(xy[:,1]-y)**2)])
# T: terminal node for each boundary line whose name starts with BC_ (node nearest to the line centroid)
T={r.nome:near(r.geometry.centroid.x,r.geometry.centroid.y) for _,r in bd.iterrows() if r.nome.startswith('BC_')}
# d: distance (m) between each terminal node and the line centroid (printed to check the snapping)
d={k:float(np.hypot(*(vv[v]-np.array(bd[bd.nome==k].geometry.iloc[0].centroid.coords[0][:2])))) for k,v in T.items()}
print('terminal dist',{k:round(v,1) for k,v in d.items()})
# penalize edges near boundary so paths stay central
# dist: distance of a node from the bed boundary - defined but never used (the penalty announced in the comment above is not implemented)
dist=lambda n: shapely.distance(bed.boundary,Point(vv[n]))
# paths: name -> list of skeleton node ids
paths={}
# main = shortest path (weight = edge length, m) from BC_caldonazzo to BC_brenta_valle
mainp=nx.shortest_path(H,T['BC_caldonazzo'],T['BC_brenta_valle'],weight='weight'); paths['main']=mainp
# done = nodes already on the main path
done=set(mainp)
# tributary terminals ordered by distance to the outlet (nearest first); processed from the farthest
order=sorted([k for k in T if k not in('BC_caldonazzo','BC_brenta_valle')],key=lambda k:nx.shortest_path_length(H,T[k],T['BC_brenta_valle'],weight='weight'))
for k in order[::-1]:
    # from each terminal run Dijkstra over the whole graph; ln = distances, pt = paths
    p=nx.single_source_dijkstra(H,T[k],target=None,weight='weight')
    ln,pt=p
    # t = the already-built node (main path) closest along the graph; the path from the terminal to t is the tributary
    t=min((n for n in done if n in ln),key=lambda n:ln[n]); paths[k]=pt[t]; 
    # do not merge (keep tribs only)
print('lengths')
# L(p): length (m) of the polyline through the nodes in p; print length and the end point of each path
def L(p): a=vv[p]; return float(np.hypot(*np.diff(a,axis=0).T).sum())
for k,p in paths.items(): print(f'  {k:28s}{L(p):9.0f} m  join at {vv[p[-1]].round().tolist()}')
# save the paths
pickle.dump(dict(paths=paths,T=T),open(f'{SP}/work/net.pkl','wb'))
# resample + smooth + widths
# smooth(p,step=1.0,sig=8): resample the path every 1 m and smooth x,y with a Gaussian filter (sigma = 8 samples = 8 m)
def smooth(p,step=1.0,sig=8):
    a=vv[p]; l=LineString(a); s=np.arange(0,l.length,step)
    q=shapely.get_coordinates(shapely.line_interpolate_point(l,s)); 
    q2=np.c_[gaussian_filter1d(q[:,0],sig,mode='nearest'),gaussian_filter1d(q[:,1],sig,mode='nearest')]
    return q2
# widths(q,poly,every=5): every 5 samples (m) of q, cut poly with a line of 1200 m (+-600 m) perpendicular to the path
# (n = left normal of the local tangent) and take the length of the intersection part containing the path point; NaN if none. First/last 10 samples skipped.
def widths(q,poly,every=5):
    out=[]
    for i in range(10,len(q)-10,every):
        t=q[i+1]-q[i-1]; t/=np.hypot(*t); n=np.array([-t[1],t[0]])
        ray=LineString([q[i]-n*600,q[i]+n*600]); x=ray.intersection(poly)
        for part in getattr(x,'geoms',[x]):
            if part.distance(Point(q[i]))<1e-6: out.append(part.length); break
        # for/else: if no part contains the point -> NaN
        else: out.append(np.nan)
    return np.array(out)
# figure with two panels: main stem (top) and tributaries (bottom)
fig,axs=plt.subplots(2,1,figsize=(16,7))
# q = smoothed main path; W = width of corridor (bed+bank), B = width of bed alone (m)
q=smooth(mainp); W=widths(q,cor); B=widths(q,bed)
# s = progressive distance (m) of each width sample
s=np.arange(10,len(q)-10,5)
# prints percentiles (min,5,50,95,max) of the widths along the main path
print('main',len(q),'cor width',np.nanpercentile(W,[0,5,50,95,100]).round(1),'bed',np.nanpercentile(B,[0,5,50,95,100]).round(1))
# fraction of the main path where the corridor is narrower than 40 m / 30 m
print('main frac cor<40:',round(float(np.nanmean(W<40)),3),' cor<30:',round(float(np.nanmean(W<30)),3))
# plot widths vs distance in km; dotted line = 40 m target width
axs[0].plot(s/1000,W,lw=.6,label='bed+sponda'); axs[0].plot(s/1000,B,lw=.6,label='bed'); axs[0].axhline(40,c='k',ls=':'); axs[0].set_ylim(0,300); axs[0].legend(); axs[0].set_title('main stem')
# tributaries: same, only if the smoothed path has >=40 points
for k,p in paths.items():
    if k=='main':continue
    q=smooth(p)
    if len(q)<40: print(k,'short',len(q)); continue
    W=widths(q,cor,5); B=widths(q,bed,5)
    print(f'  {k:28s} L={len(q):5d} cor',np.nanpercentile(W,[0,50,100]).round(1),'bed',np.nanpercentile(B,[0,50,100]).round(1))
    axs[1].plot(np.arange(len(W))*5/1000,W,lw=.5,label=k)
axs[1].set_ylim(0,120);axs[1].axhline(40,c='k',ls=':');axs[1].legend(ncol=4,fontsize=6);axs[1].set_title('rami')
# 2nd panel: tributary corridor widths; save figure to work/w.png
plt.tight_layout();plt.savefig(f'{SP}/work/w.png',dpi=90)
