# check_bp.py  (step 19: independent verification of the bankpoints)
# Purpose: recompute every bankpoint with an independent method (profile sampled every 1 cm instead of exact cell traversal) and compare
#          with the bankpoints stored in layers/bankpoints_50m.gpkg; also verify z_dtm against the DTM and the 5 m rule.
# Inputs : WD/work/sec_in.json (section data incl. maxL/maxR), layers/DTM_finale.tif, layers/bankpoints_50m.gpkg, layers/boundary_50m.gpkg (absolute paths).
# Output : print-only (lines 12 and 13 and 'residual' lines; see docs/scripts/check_bp.md).
# Run    : /usr/bin/python3 check_bp.py WD      (needs osgeo/GDAL; does not import core.py)
import json, sys, math, numpy as np, sqlite3, struct
from osgeo import gdal, ogr
gdal.UseExceptions()
# gt = GDAL geotransform of the DTM (gt[0],gt[3] = top-left corner; gt[1] = pixel width; gt[5] = negative pixel height).
SP=sys.argv[1]; L='/home/amedeo/Documents/Brenta_mesh_10/layers'
ds=gdal.Open(L+'/DTM_finale.tif'); b=ds.GetRasterBand(1); gt=ds.GetGeoTransform()
S=json.load(open(f'{SP}/work/sec_in.json')); 
# bp[nome] = (x, y, z_dtm, tipo, regola, dist_cp) of every stored bankpoint; sec[nome] = geometry clones of the section nodestrings (only counted/printed).
dsv=ogr.Open(L+'/bankpoints_50m.gpkg'); v=dsv.GetLayer(); bp={}
for f in v: g=f.GetGeometryRef(); bp[f['nome']]=(g.GetX(),g.GetY(),f['z_dtm'],f['tipo'],f['regola'],f['dist_cp'])
dsb=ogr.Open(L+'/boundary_50m.gpkg'); ns=dsb.GetLayer('boundary'); sec={}
for f in ns:
    n=f['nome']
    if n and n[0] in 'SV' and n[1:6].isdigit(): sec[n]=f.GetGeometryRef().Clone()
print('sec layer',len(sec))
# cell(): (col,row) of the DTM cell containing (x,y). sampled(): profile along the section direction every 1 cm (step) up to T m: t, z, cols, rows.
def cell(x,y): return int(math.floor((x-gt[0])/gt[1])),int(math.floor((gt[3]-y)/(-gt[5])))
def sampled(s,sgn,T,step=0.01):
    t=np.arange(step/2,T,step); xs=s['x']+s['nx']*sgn*t; ys=s['y']+s['ny']*sgn*t
    cols=np.floor((xs-gt[0])/gt[1]).astype(int); rows=np.floor((gt[3]-ys)/(-gt[5])).astype(int)
    c0,c1,r0,r1=cols.min(),cols.max(),rows.min(),rows.max()
    A=b.ReadAsArray(int(c0),int(r0),int(c1-c0+1),int(r1-r0+1)).astype(float); z=A[rows-r0,cols-c0]; return t,z,cols,rows
# Counters: errz = z_dtm differs from DTM cell value (> 1e-6); err5 = bankpoint closer than 5 m to the top-of-bank line; ndiff = disagreements with the
# independent recomputation; total = number of bankpoints examined.
errz=0; err5=0; first=0; ndiff=[]; total=0; mid=0
# For each section and side: name n = S/V + abscissa as in dump.py; tt = toe distance, cc = top-of-bank distance, mx = next-bed cap (maxL/maxR).
for idx,s in enumerate(S):
    n=('S' if s['stream']=='main' else 'V')+f"{int(round(s['s'])):05d}"
    for tag,sgn,tt,cc,mx in (('sx',1,s['tL'],s['cL'],s.get('maxL')),('dx',-1,s['tR'],s['cR'],s.get('maxR'))):
        x,y,z,tipo,rg,t0=bp[f'{n}_{tag}']; total+=1
        c,r=cell(x,y); v=float(b.ReadAsArray(c,r,1,1)[0,0])
        if abs(v-z)>1e-6: errz+=1
        # Wall points: only the z check applies; no independent recomputation.
        if tipo=='muro': continue
        if t0>cc-5.0+1e-6: err5+=1
        # Same limit rule as bank.py: cap, mid-width+15 m, or toe+15 m (B = bed width > 30 m or window < 2 m).
        cap=min(cc-5.0, mx if mx else 1e9); mid=(s['cL']-s['cR'])/2*sgn; B=s['tL']+s['tR']
        lim=min(cap,mid+15.0)
        if B>30 or lim<=tt+2.0: lim=min(cap,tt+15.0)
        # Independent profile (1 cm samples) -> plateaus of equal value (runs) -> local maxima by prominence (same definition as bank.py analyse()).
        t,z_,co,ro=sampled(s,sgn,min(cc+60.0,1500.0))
        # independent run-length plateaus by cell+value with 1 cm samples
        i=0; runs=[]
        while i<len(t):
            j=i
            while j+1<len(t) and z_[j+1]==z_[i]: j+=1
            runs.append((i,j,z_[i])); i=j+1
        rn=len(runs); vals=[q[2] for q in runs]
        def prom(k):
            v=vals[k]; lmin=None; m=v
            for q in range(k-1,-1,-1):
                m=min(m,vals[q])
                if vals[q]>v: lmin=m; break
            rmin=None; m=v
            for q in range(k+1,rn):
                m=min(m,vals[q])
                if vals[q]>v: rmin=m; break
            cs=[w for w in (lmin,rmin) if w is not None]
            return v-max(cs) if cs else v-min(vals)
        # mask = samples in (toe, lim); zt = value at toe; zm = max in window; thr = half of the height range (ignore lower half of the bank).
        # pk = first run that is a local maximum with prominence >= 5 cm and z >= thr, overlapping (toe, lim); otherwise fallback = highest sample.
        mask=(t>tt)&(t<lim); zt=z_[np.argmax(t>tt)]; zm=z_[mask].max(); thr=zt+0.5*(zm-zt)
        pk=None
        for k,(a,e,zz) in enumerate(runs):
            if k==0 or k==rn-1 or not(vals[k-1]<zz and vals[k+1]<zz): continue
            if t[e]<=tt or t[a]>=lim or zz<thr: continue
            if prom(k)>=0.05: pk=(a,e,zz); break
        tp=np.where(mask)[0]
        ref=(pk[0],pk[1],pk[2]) if pk else (None,None,z_[tp[np.argmax(z_[tp])]])
        tipo2='max' if pk else 'fallback'
        # Disagreement if the kind differs or the height differs by more than 1 mm.
        if tipo2!=tipo or abs(ref[2]-z)>1e-3: ndiff.append((n,tag,tipo,tipo2,round(z,3),round(float(ref[2]),3)))
print('12 z_dtm mismatch',errz,'of',total,'; bankpoints closer than 5 m to top',err5)
print('13 independent 1-cm bankpoint comparison: differences',len(ndiff),ndiff[:20])
# For each disagreement: length (m) of the stored bankpoint's DTM cell that lies inside the valid search window. If <= 1 cm (0.0105) the 1 cm sampling
# could not see the cell, so the difference is a sampling artefact; larger values are printed as 'residual' (real discrepancies to investigate).
# in-range stretch of winning cell for the differing cases
wnd=[]
for n,tag,*rest in ndiff:
    s=[x for x in S if ('S' if x['stream']=='main' else 'V')+f"{int(round(x['s'])):05d}"==n][0]
    x,y,z,tp,rg,t0=bp[f'{n}_{tag}']; sgn=1 if tag=='sx' else -1
    c,r=cell(x,y); x0,y1=gt[0]+c*gt[1],gt[3]+r*gt[5]; x1,y0=x0+gt[1],y1+gt[5]
    dx,dy=s['nx']*sgn,s['ny']*sgn; ox,oy=s['x'],s['y']
    tt=sorted([(v-o)/dd for v,o,dd in ((x0,ox,dx),(x1,ox,dx),(y0,oy,dy),(y1,oy,dy)) if abs(dd)>1e-12]); a,b_=tt[1],tt[2]
    tto=s['tL'] if tag=='sx' else s['tR']; cc=s['cL'] if tag=='sx' else s['cR']; mx=s.get('maxL' if tag=='sx' else 'maxR'); cap=min(cc-5.0, mx if mx else 1e9); mid=(s['cL']-s['cR'])/2*sgn; B=s['tL']+s['tR']; lim=min(cap,mid+15.0)
    if B>30 or lim<=tto+2.0: lim=min(cap,tto+15.0)
    wnd.append(round(min(b_,lim)-max(a,tto),4))
    if wnd[-1]>0.0105: print('  residual',n,tag,tp,'z stored',round(z,3),'t',round(t0,3),'toe',round(tto,3),'lim',round(lim,3),'rest',rest)
print('in-range stretch of winning cell (m)',sorted(wnd),'; at most 1 cm:',sum(w<=0.0105 for w in wnd),'of',len(wnd))
