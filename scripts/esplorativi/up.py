# up.py  (exploratory, NOT needed to produce the layers)
# Purpose: compare the bed width along two alternative routes of the main stream in the easting window 677860-678440 m
#          (the 'link' route in rawcl.pkl['main'] and the 'meander' route in altmain.pkl): 10/50/90 percentiles of the width and sample count.
# Inputs : WD/work/graph.pkl (via core.load_graph), rawcl.pkl, altmain.pkl (both from cl.py).  Output: print only.
# Run    : python3 up.py WD      (Anaconda python3; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
faces,rows=load_graph()
b=boundary_segs(faces,rows,lambda n: cls(n)=='bed'); R=Rays(b)
RC=pickle.load(open(f'{SP}/work/rawcl.pkl','rb')); 
import pickle as pk
alt=pk.load(open(f'{SP}/work/altmain.pkl','rb'))
# bw(): for the polyline a restricted to x in (x0,x1), every 10th vertex: normal from vertices i-8..i+8, rays (max 100 m) against bed edges;
# width = nearest hit on the left - nearest hit on the right. Returns (10/50/90 percentiles rounded to 0.1 m, number of samples).
def bw(a,x0,x1):
    m=(a[:,0]>x0)&(a[:,0]<x1); a=a[m]
    out=[]
    for i in range(10,len(a)-10,10):
        t=a[i+8]-a[i-8]; n=np.array([-t[1],t[0]])/np.hypot(*t); h=R.hits(a[i],n,100)
        if len(h) and (h>0).any() and (h<0).any(): out.append(h[h>0].min()-h[h<0].max())
    return np.round(np.percentile(out,[10,50,90]),1) if out else None, len(out)
vvmain=RC['main']
print('link route (in window)',bw(vvmain,677860,678440)); print('meander route',bw(alt,677860,678440))

# rebuild alt coordinates through saved graph is not kept: compare using RC['main'] only here
