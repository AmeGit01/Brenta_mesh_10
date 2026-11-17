# bank.py  (step 14; previous: next_bed.py, next: finals.py)
# Purpose: find, for every section and each side, the bankpoint on the DTM (0.25 m cells, nodata -9999).
#          Rule: walk along the section from the toe outward; take the first local maximum of the DTM profile with prominence >= 5 cm,
#          ignoring points in the lower half of the bank height; it must lie >= 5 m inside the top-of-bank line and <= 15 m from the
#          mid-width of the channel ('mid' rule) or <= 15 m from the toe ('toe15' rule, wide beds or too small windows);
#          fallback = highest cell in the allowed window. Special kinds: 'muro' (wall: search cap at/before the toe), 'nobank', 'nodata'.
# Inputs : WD/work/sec_in.json (export_sec.py + next_bed.py) and /home/amedeo/Documents/Brenta_mesh_10/layers/DTM_finale.tif (absolute path).
# Output : WD/work/bank_out.json (list, same order as sec_in.json, of {L:{...},R:{...}}); prints a Counter of (kind, rule) for L and R.
# Run    : /usr/bin/python3 bank.py WD      (system python: needs osgeo/GDAL + numpy; Anaconda python has no osgeo)
# Units  : metres; t = distance along the section normal measured from the centerpoint (positive towards the side considered).
import json, sys, math, numpy as np
from osgeo import gdal
gdal.UseExceptions()
# SP = working directory (argument 1); DTM = hard-coded path of the terrain model; nd = nodata value of band 1.
SP=sys.argv[1]; DTM='/home/amedeo/Documents/Brenta_mesh_10/layers/DTM_finale.tif'
ds=gdal.Open(DTM); gt=ds.GetGeoTransform(); band=ds.GetRasterBand(1); nd=band.GetNoDataValue()
# GDAL geotransform: X0,Y0 = top-left corner of the raster, PW = pixel width, PH = pixel height (sign flipped to be positive; rows grow southward).
X0,PW,_,Y0,_,PH=gt; PH=-PH
def traverse(ox,oy,dx,dy,T):
    """every cell crossed by the segment o+t*d, t in [0,T]; returns (col,row,ta,tb)"""
    # Exact grid traversal (Amanatides-Woo / DDA): start cell (col,row) containing the origin.
    # tmc/tmr = parameter t at which the ray next crosses a vertical/horizontal cell edge; tdc/tdr = t increment for one full cell in x/y.
    col=int(math.floor((ox-X0)/PW)); row=int(math.floor((Y0-oy)/PH))
    stepc=1 if dx>0 else -1; stepr=-1 if dy>0 else 1   # row grows southward
    if dx!=0:
        nx_=X0+(col+(1 if dx>0 else 0))*PW; tmc=(nx_-ox)/dx; tdc=PW/abs(dx)
    else: tmc=tdc=float('inf')
    if dy!=0:
        ny_=Y0-(row+(1 if dy<0 else 0))*PH; tmr=(ny_-oy)/dy; tdr=PH/abs(dy)
    else: tmr=tdr=float('inf')
    # Loop: record the cell crossed in [t,nt], then step into the neighbouring cell (diagonal step if both edges are hit at the same t).
    t=0.; out=[]
    while t<T:
        nt=min(tmc,tmr,T)
        if nt>t+1e-12: out.append((col,row,t,nt))
        if nt>=T: break
        if tmc<tmr: col+=stepc; tmc+=tdc
        elif tmr<tmc: row+=stepr; tmr+=tdr
        else: col+=stepc; row+=stepr; tmc+=tdc; tmr+=tdr
        t=nt
    return out
# read(): DTM values of the listed cells, in the same order, using a single bounding-box ReadAsArray (float).
def read(cells):
    c0=min(c[0] for c in cells); c1=max(c[0] for c in cells); r0=min(c[1] for c in cells); r1=max(c[1] for c in cells)
    A=band.ReadAsArray(c0,r0,c1-c0+1,r1-r0+1).astype(float); return np.array([A[c[1]-r0,c[0]-c0] for c in cells])
def analyse(z):
    """plateau list [(i0,i1,zval)], returns list of local maxima with prominence"""
    # 1) group consecutive cells with exactly equal value into plateaus pl=[(first_idx,last_idx)] (a cell is a constant-height step).
    n=len(z); pl=[]; i=0
    while i<n:
        j=i
        while j+1<n and z[j+1]==z[i]: j+=1
        pl.append((i,j)); i=j+1
    # 2) for each interior plateau strictly higher than both neighbours (local maximum) compute its prominence:
    #    walk left/right until a higher plateau is found; 'left'/'right' = lowest value met on the way (the col);
    #    prominence = height - max(cols) (if no higher plateau exists on a side, that side gives no col; if on neither, height - global min).
    res=[]
    vals=[z[a] for a,b in pl]
    for k,(a,b) in enumerate(pl):
        v=vals[k]
        if k==0 or k==len(pl)-1: continue
        if not(vals[k-1]<v and vals[k+1]<v): continue
        left=None; m=v
        for q in range(k-1,-1,-1):
            m=min(m,vals[q])
            if vals[q]>v: left=m; break
        right=None; m=v
        for q in range(k+1,len(pl)):
            m=min(m,vals[q])
            if vals[q]>v: right=m; break
        col=[x for x in (left,right) if x is not None]
        pro=v-max(col) if col else v-min(vals)
        res.append((a,b,v,pro))
    return res
# side(): bankpoint on one side of section `sec`. sgn=+1 left / -1 right; tt = toe distance on this side; cc = top-of-bank distance on this side;
# tother, cother = same for the other side (unused). Returns dict(kind,t,z,prom,rule,limit,...): kind in max|fallback|muro|nobank|nodata.
def side(sec,sgn,tt,cc,tother,cother):
    # d = section direction towards this side; B = bed width (tL+tR) at the section.
    d=(sec['nx']*sgn,sec['ny']*sgn); B=sec['tL']+sec['tR']
    tm_signed=(sec['cL']-sec['cR'])/2.0     # mid of top-to-top in +L coordinates
    mid=tm_signed*sgn                       # its distance along this side's direction
    # cap5 = farthest allowed distance: >= 5 m inside the top-of-bank line (cc-5) and not beyond the next-bed cap (maxL/maxR from next_bed.py).
    cap5=min(cc-5.0,sec.get('max'+('L' if sgn>0 else 'R'),1e9))
    # 'mid' rule: search up to 15 m beyond the mid-width between the two top-of-bank lines.
    # Fall back to the 'toe15' rule (15 m beyond the own toe) when the bed is wider than 30 m or the mid window is less than 2 m beyond the toe.
    lim=min(cap5,mid+15.0); rule='mid'
    if B>30 or lim<=tt+2.0:
        lim=min(cap5,tt+15.0); rule='toe15'
    # Wall case: the cap is at or before the toe -> bankpoint placed at the cap distance, DTM value of the last crossed cell, kind 'muro'.
    if lim<=tt+1e-9 and sec.get('max'+('L' if sgn>0 else 'R'),1e9)<=tt:
        tw=float(sec['max'+('L' if sgn>0 else 'R')]); C=traverse(sec['x'],sec['y'],d[0],d[1],tw+0.01); z=read(C)
        return dict(kind='muro',t=tw,z=float(z[-1]),prom=None,rule='muro',limit=tw,ztoe=float(z[-1]),zrange=float(z[-1]))
    # No room for a bank at all -> 'nobank': point put midway between toe and top, no z.
    if lim<=tt+1e-9:
        return dict(kind='nobank',t=(tt+cc)/2.0,z=None,prom=None,rule='nobank',limit=lim)
    # Profile: cells crossed up to 60 m beyond the top-of-bank line (max 1500 m); ta/tb = entry/exit t of each cell; inr = cells overlapping (toe, lim).
    Tend=min(cc+60.0,1500.0)
    C=traverse(sec['x'],sec['y'],d[0],d[1],Tend); z=read(C)
    ta=np.array([c[2] for c in C]); tb=np.array([c[3] for c in C])
    inr=(tb>tt)&(ta<lim)
    if not inr.any(): return dict(kind='nobank',t=(tt+cc)/2.0,z=None,prom=None,rule='nocell',limit=lim)
    # any nodata cell in the search window -> 'nodata' (no bankpoint computed, point midway between toe and top).
    if (z[inr]==nd).any(): return dict(kind='nodata',t=(tt+cc)/2.0,z=None,prom=None,rule=rule,limit=lim)
    # ztoe = DTM at the toe cell, zmax = max in window; thr = toe + half of the height range: peaks below thr are ignored (lower half of the bank).
    itoe=int(np.argmax(tb>tt)); ztoe=z[itoe]; zmax=z[inr].max(); thr=ztoe+0.5*(zmax-ztoe)
    # Choose the FIRST (smallest distance) plateau-maximum that overlaps (toe, lim), has prominence >= 0.05 m (5 cm) and height >= thr.
    pk=analyse(z); pick=None
    for a,b,v,pro in pk:
        mt=(ta[a]+tb[b])/2.0
        if tb[b]<=tt or ta[a]>=lim: continue
        if pro<0.05 or v<thr: continue
        if pick is None or ta[a]<pick[0]: pick=(ta[a],a,b,v,pro)
    # Bankpoint = middle of the chosen plateau, clipped to [toe, lim]. Otherwise fallback: the highest cell in the window (clipped middle).
    if pick:
        _,a,b,v,pro=pick; t0=max(ta[a],tt); t1=min(tb[b],lim); t=(t0+t1)/2.0; kind='max'
    else:
        ii=np.where(inr)[0]; i=ii[np.argmax(z[ii])]; v=z[i]; pro=None; t0=max(ta[i],tt); t1=min(tb[i],lim); t=(t0+t1)/2.0; kind='fallback'
    return dict(kind=kind,t=float(t),z=float(v),prom=(float(pro) if pro is not None else None),rule=rule,limit=float(lim),ztoe=float(ztoe),zrange=float(zmax))
# Main: for every section compute the left (sgn=+1) and right (sgn=-1) bankpoints and store in the same order as sec_in.json.
S=json.load(open(f'{SP}/work/sec_in.json'))
out=[]
for i,s in enumerate(S):
    L=side(s,1,s['tL'],s['cL'],s['tR'],s['cR']); R=side(s,-1,s['tR'],s['cR'],s['tL'],s['cL'])
    out.append(dict(L=L,R=R))
json.dump(out,open(f'{SP}/work/bank_out.json','w'))
# Summary: how many bankpoints per (kind, rule) on each side (L/R).
import collections
for k in 'LR':
    print(k,collections.Counter((o[k]['kind'],o[k]['rule']) for o in out))
