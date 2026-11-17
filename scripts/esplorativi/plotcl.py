# plotcl.py  (exploratory, NOT needed to produce the layers)
# Purpose: plot the raw centerlines of main (red) and Brenta vecchio (magenta) over the bed polygon in four windows -> cl.png.
# Inputs : WD/work/rawcl.pkl (cl.py: P = bed polygon, main, vecchio = vertex arrays).  Output: WD/work/cl.png (85 dpi).
# Run    : python3 plotcl.py WD      (Anaconda python3 with matplotlib; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=pickle.load(open(f'{SP}/work/rawcl.pkl','rb'))
fig,axs=plt.subplots(2,2,figsize=(18,10))
wins=[(676800,678800,5096600,5097700),(686900,690100,5101500,5103400),(699900,702400,5098700,5100000),(702000,705500,5097300,5099000)]
for ax,w in zip(axs.flat,wins):
    gpd.GeoSeries([R['P']]).plot(ax=ax,color='#bcd7f0',edgecolor='#468',linewidth=.3)
    ax.plot(*R['main'].T,'r',lw=.8); ax.plot(*R['vecchio'].T,'m',lw=.8)
    ax.set_xlim(w[0],w[1]); ax.set_ylim(w[2],w[3]); ax.set_aspect('equal')
plt.tight_layout(); plt.savefig(f'{SP}/work/cl.png',dpi=85)
