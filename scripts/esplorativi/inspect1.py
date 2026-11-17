# inspect1.py  (exploratory, NOT needed to produce the layers)
# Purpose: plot four windows of the Borgo area (faces coloured by class, boundary features labelled) to borgo.png and print the endpoint
#          degree statistics of the breaklines (dangling ends).
# Inputs : WD/work/graph.pkl (graph.py), WD/in/boundary.gpkg, WD/in/breaklines.gpkg.  Outputs: WD/work/borgo.png (85 dpi) and printed statistics.
# Run    : python3 inspect1.py WD      (Anaconda python3 with matplotlib; does not import core.py: it contains its own copy of cls())
import pickle, sys, numpy as np, shapely, geopandas as gpd, warnings, collections
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SP=sys.argv[1]
G=pickle.load(open(f'{SP}/work/graph.pkl','rb')); faces=G['faces']; rows=G['rows']
bd=gpd.read_file(f'{SP}/in/boundary.gpkg'); bl=gpd.read_file(f'{SP}/in/breaklines.gpkg',fid_as_index=True)
bl=bl[~(bl.geometry.is_empty|bl.geometry.isna())]
# Copy of core.cls(): class of a face from its region name (bed, sponda, muro, inter, flood).
def cls(n):
    if n in('bed','bed_borgo','Ponte_Bordignon','raccordo_sifone_brentavecchio') or n.endswith('_bed') or n.startswith('source_'): return 'bed'
    if n.startswith('sponda') or n.endswith('sponda_nat'): return 'sponda'
    if n in('muro','pilone-borgo','sottopasso-borgo'): return 'muro'
    if n.startswith('intermedio'): return 'inter'
    return 'flood'
# Colours per class; win = four plot windows (xmin,xmax,ymin,ymax) in EPSG:25832 metres around Borgo.
C={'bed':'#4a90d9','sponda':'#7fc97f','muro':'#d62728','inter':'#ffe08a','flood':'#eeeeee'}
win=[(687100,688000,5101500,5102650),(688000,689000,5102400,5103100),(689000,690100,5102600,5103350),(690100,691000,5102800,5103200)]
fig,axs=plt.subplots(2,2,figsize=(18,12))
for ax,(x0,x1,y0,y1) in zip(axs.flat,win):
    b=box(x0,y0,x1,y1)
    for r in rows:
        f=faces[r['face']]
        if f.intersects(b): gpd.GeoSeries([f]).plot(ax=ax,color=C[cls(r['nome'])],edgecolor='#555',linewidth=.25)
    for _,r in bd.iterrows():
        if r.geometry.intersects(b):
            gpd.GeoSeries([r.geometry]).plot(ax=ax,color='k',linewidth=1)
            c=r.geometry.centroid; ax.annotate(r.nome,(c.x,c.y),fontsize=6)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
plt.tight_layout(); plt.savefig(f'{SP}/work/borgo.png',dpi=85)
# Statistics on the breaklines: every part as a coordinate array; ends = first/last vertex rounded to 1 mm; degree = how many parts share an end point;
# dangling ends = points with degree 1 (candidates for gaps in the line network). The 'edges' variable is unused.
# classify all breakline noded edges by faces on either side
edges=[]; 
fcl={r['face']:cls(r['nome']) for r in rows}; 
ls=[]
for fid,g in bl.geometry.items():
    for p in shapely.get_parts(g):
        a=shapely.get_coordinates(p)
        ls.append((fid,a))
print('total pieces',len(ls), 'all 2 ends')
# endpoint degree
pts=collections.Counter()
for fid,a in ls:
    for e in (a[0],a[-1]): pts[(round(e[0],3),round(e[1],3))]+=1
print('end degree',collections.Counter(pts.values()))
un=[k for k,v in pts.items() if v==1]; print('dangling ends',len(un))
