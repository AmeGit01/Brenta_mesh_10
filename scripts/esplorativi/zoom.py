# zoom.py  (exploratory, NOT needed to produce the layers)
# Purpose: zoomed plots (four small windows, mostly in Borgo and near easting 677900) of faces coloured by class with boundary features labelled -> zoom.png.
# Inputs : WD/work/graph.pkl (via core.load_graph), WD/in/boundary.gpkg.  Output: WD/work/zoom.png (80 dpi).
# Run    : python3 zoom.py WD      (Anaconda python3 with matplotlib; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from shapely.geometry import box
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
faces,rows=load_graph()
bd=gpd.read_file(f'{SP}/in/boundary.gpkg')
C={'bed':'#4a90d9','sponda':'#7fc97f','muro':'#d62728','inter':'#ffe08a','flood':'#eeeeee'}
wins=[(687900,688080,5102480,5102580),(688620,688900,5102740,5102860),(677840,677980,5096860,5097060),(689700,689900,5102880,5103010)]
fig,axs=plt.subplots(2,2,figsize=(17,11))
for ax,(x0,x1,y0,y1) in zip(axs.flat,wins):
    b=box(x0,y0,x1,y1)
    for r in rows:
        f=faces[r['face']]
        if f.intersects(b): gpd.GeoSeries([f]).plot(ax=ax,color=C[cls(r['nome'])],edgecolor='#333',linewidth=.5); 
        if f.intersects(b) and cls(r['nome']) in('bed',): 
            c=f.intersection(b).representative_point(); ax.annotate(r['nome'],(c.x,c.y),fontsize=7)
    for _,r in bd.iterrows():
        if r.geometry.intersects(b):
            gpd.GeoSeries([r.geometry]).plot(ax=ax,color='k',linewidth=1.3); c=r.geometry.centroid; ax.annotate(r.nome,(c.x,c.y),fontsize=7,color='r')
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
plt.tight_layout(); plt.savefig(f'{SP}/work/zoom.png',dpi=80)
