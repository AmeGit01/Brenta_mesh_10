# core.py - shared helper module (NOT run directly; imported with `from core import *`).
# Purpose: common imports, the work-dir variable SP, face classification by name (cls), loading of graph.pkl,
# and geometric helpers (ring segments, top/toe line extraction, ray/segment first-hit queries).
# Inputs : WD/work/graph.pkl (only through load_graph(), produced by graph.py).
# Outputs: none.
# Usage  : the importing script must first do sys.path.insert(0, WD+'/work') and be launched as `python3 script.py WD`,
#          because SP is taken from sys.argv[1] at import time. Interpreter: Anaconda python3 (geopandas, shapely 2.1, numpy).
# Note   : `from core import *` also re-exports pickle, np, shapely, gpd, warnings, collections, sys, LineString, Point, Polygon.
import pickle, numpy as np, shapely, geopandas as gpd, warnings, collections
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point, Polygon
import sys
# SP = working directory WD (argv[1]); contains in/ (input gpkg) and work/ (scripts + intermediate pkl/json)
SP=sys.argv[1]  # cartella di lavoro con sottocartelle in/ e work/
# cls(n): maps a face/region name n (field 'nome' of regioni_ponti) to one of 5 classes:
# 'bed' (riverbed), 'sponda' (bank), 'muro' (wall/urban), 'inter' (intermedio), 'flood' (everything else)
def cls(n):
    if n in('bed','bed_borgo','Ponte_Bordignon','raccordo_sifone_brentavecchio') or n.endswith('_bed') or n.startswith('source_'): return 'bed'
    if n.startswith('sponda') or n.endswith('sponda_nat'): return 'sponda'
    if n in('muro','pilone-borgo','sottopasso-borgo'): return 'muro'
    if n.startswith('intermedio'): return 'inter'
    return 'flood'
# load_graph(): reads WD/work/graph.pkl; returns (faces, rows): faces = list of shapely Polygons (planar-graph faces),
# rows = list of dicts {face (index in faces), fid, nome, mat, area} for faces that contain a region point
def load_graph():
    G=pickle.load(open(f'{SP}/work/graph.pkl','rb')); return G['faces'],G['rows']
# ring_segs(poly): all segments of the exterior and interior rings of poly as an (N,4) array [x0,y0,x1,y1] (m, EPSG:25832)
def ring_segs(poly):
    out=[]
    for r in [poly.exterior]+list(poly.interiors):
        a=shapely.get_coordinates(r); out.append(np.c_[a[:-1],a[1:]])
    return np.vstack(out)
# key(s): canonical hashable id of a segment s=[x0,y0,x1,y1]: endpoints rounded to 1e-4 m and ordered,
# so the same segment gets the same key whatever its direction
def key(s): 
    a=(round(s[0],4),round(s[1],4)); b=(round(s[2],4),round(s[3],4)); return (a,b) if a<b else (b,a)
# boundary_segs(faces,rows,pred): segments forming the outer boundary of the union of the faces whose class name satisfies pred(nome).
# A segment shared by two selected faces is counted twice and dropped; only segments counted once are kept. Returns (M,4) array.
def boundary_segs(faces,rows,pred):
    cnt=collections.Counter(); keep={}
    for r in rows:
        if pred(r['nome']):
            for s in ring_segs(faces[r['face']]):
                k=key(s); cnt[k]+=1; keep[k]=s
    return np.array([keep[k] for k,v in cnt.items() if v==1])
# Rays: first-hit queries of lines against a fixed set of segments (uses an STRtree for candidate selection)
class Rays:
    """first-hit queries of rays against a set of segments"""
    def __init__(self,segs):
        # segs: (N,4) array [x0,y0,x1,y1]; self.s keeps them, self.t = spatial index of the segments as LineStrings
        self.s=segs; self.t=shapely.STRtree(shapely.linestrings(segs.reshape(-1,2,2)))
    # hits(o,d,L): intersections of the line through point o with UNIT direction d, limited to |t|<=L metres.
    # Returns the sorted signed distances t (m) along d from o (t>0 on the d side, t<0 on the opposite side); empty array if none.
    # Callers use d = left normal of the centerline: positive t = left bank, negative t = right bank.
    def hits(self,o,d,L):
        # candidate segments: those intersecting the segment o-d*L .. o+d*L
        ray=LineString([o-d*L,o+d*L]); idx=self.t.query(ray)
        if len(idx)==0: return np.array([])
        # solve o + t*d = p + u*r (r = segment vector); den = cross(d,r); parallel segments (|den|<=1e-12) are skipped
        S=self.s[idx]; p=S[:,:2]; r=S[:,2:]-p
        den=d[0]*r[:,1]-d[1]*r[:,0]; m=np.abs(den)>1e-12
        if not m.any(): return np.array([])
        p=p[m]; r=r[m]; den=den[m]; w=p-o
        # t = distance along the ray, u = position on the segment (0..1, tolerance 1e-9); keep only hits inside the segment and within L
        t=(w[:,0]*r[:,1]-w[:,1]*r[:,0])/den; u=(w[:,0]*d[1]-w[:,1]*d[0])/den
        return np.sort(t[(u>=-1e-9)&(u<=1+1e-9)&(np.abs(t)<=L)])
