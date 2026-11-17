# map.py  (exploratory, NOT needed to produce the layers)
# Purpose: map of the faces of classes bed / bed_borgo / sponda_nat / sponda_antro (two panels along the river) saved as map.png, and print
#          the connected components of each group (area in ha, bounding-box corners) to check connectivity of bed and banks.
# Inputs : WD/work/graph.pkl (graph.py), WD/in/boundary.gpkg.  Outputs: WD/work/map.png (95 dpi) and printed text.
# Run    : python3 map.py WD      (Anaconda python3 with matplotlib; does not import core.py)
import pickle, sys, numpy as np, shapely, geopandas as gpd, warnings
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.ops import unary_union
SP=sys.argv[1]
G=pickle.load(open(f'{SP}/work/graph.pkl','rb')); faces=G['faces']; rows=G['rows']
bd=gpd.read_file(f'{SP}/in/boundary.gpkg')
# col: face name -> colour; pick(n): polygons of all faces whose region name is n; the two panels cover easting 675500-690600 and 690300-705600.
col={'bed':'#1f77b4','bed_borgo':'#d62728','sponda_nat':'#2ca02c','sponda_antro':'#ff7f0e'}
def pick(n):
    return [faces[r['face']] for r in rows if r['nome']==n]
fig,axs=plt.subplots(2,1,figsize=(18,11))
for ax,(x0,x1) in zip(axs,[(675500,690600),(690300,705600)]):
    for n,c in col.items():
        g=gpd.GeoSeries(pick(n)); g.plot(ax=ax,color=c,linewidth=0.6,edgecolor=c)
    ax.set_xlim(x0,x1); ax.set_aspect('equal')
    for _,r in bd.iterrows():
        c=r.geometry.centroid
        if x0<c.x<x1 and (r.nome.startswith('BC_') or r.nome.startswith('diverg')):
            ax.plot(*c.xy,'k.',ms=3); ax.annotate(r.nome.replace('BC_',''),(c.x,c.y),fontsize=7)
    ax.margins(y=.1)
axs[0].legend(handles=[plt.Line2D([],[],color=c,lw=3,label=n) for n,c in col.items()],loc='upper left')
plt.tight_layout(); plt.savefig(f'{SP}/work/map.png',dpi=95)
# Union of faces (buffered 0.01 m to merge touching faces) per group; print number of components and the 12 largest (area ha, lower-left, upper-right corners).
# bed/sponda connectivity
for n in ['bed','bed_borgo','sponda_nat','sponda_antro']:
    u=unary_union([f.buffer(0.01) for f in pick(n)])
    parts=list(u.geoms) if u.geom_type=='MultiPolygon' else [u]
    print(n,'components',len(parts),[ (round(p.area/1e4,2),[int(v) for v in p.bounds[:2]],[int(v) for v in p.bounds[2:]]) for p in sorted(parts,key=lambda p:-p.area)[:12]])
