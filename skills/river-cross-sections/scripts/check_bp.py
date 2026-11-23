# check_bp.py - independent verification of the bankpoints (recomputed with a different method).
# Purpose: recompute every bankpoint with an independent method (profile sampled every 1 cm instead of exact cell traversal) and compare
#          with the bankpoints stored in the derived bankpoints layer; also verify z against the DTM and the near-node rule.
# Inputs : work/<params.check_bp.sec_in> (section data of the bankpoint computation: one record per section with stream/tag, s, x, y, nx, ny,
#          tL, tR, cL, cR and optional maxL, maxR; an optional key 'name' gives the section name directly), the DTM (inputs.dtm),
#          outputs.bankpoints, outputs.boundary, fields.bankpoints (name, z, kind, rule, dist_cp), fields.boundary.name, bankpoint_values
#          (left, right), sections.digits, rules.near_node.radius, params.check_bp {sec_in, stream_prefix, kind_wall, kind_max, kind_fallback,
#          step, mid_window, toe_window, wide_bed, min_window, prom_min, extra_search, max_search, tol_z, tol_kind_z, residual_len}.
# Outputs: print only (lines 12 and 13 and 'residual' lines).
# Run    : cd <working folder>; /usr/bin/python3 <toolkit>/scripts/check_bp.py [-c rcs_config.json]   (OGR interpreter: osgeo/GDAL)
# Origin : Brenta project, check_bp.py, step 19 of the original pipeline.
import sys, os, json, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from osgeo import gdal, ogr
gdal.UseExceptions()
cfg = common.load(common.parser('independent recomputation of the bankpoints').parse_args())
P = cfg['params']['check_bp']
BV = cfg['bankpoint_values']; LEFT, RIGHT = BV['left'], BV['right']
KWALL, KMAX, KFALL = P['kind_wall'], P['kind_max'], P['kind_fallback']
STEP, MIDW, TOEW, WIDE, MINW, PROM_MIN, EXTRA, MAXS = P['step'], P['mid_window'], P['toe_window'], P['wide_bed'], P['min_window'], P['prom_min'], P['extra_search'], P['max_search']
TOLZ, TOLK, RESL = P['tol_z'], P['tol_kind_z'], P['residual_len']
R5 = cfg['rules']['near_node']['radius']
fbp = cfg['fields']['bankpoints']; FN, FZ, FK, FR, FD = (fbp[k] for k in ('name', 'z', 'kind', 'rule', 'dist_cp'))
# gt = GDAL geotransform of the DTM (gt[0],gt[3] = top-left corner; gt[1] = pixel width; gt[5] = negative pixel height).
ds=gdal.Open(cfg.dtm()); b=ds.GetRasterBand(1); gt=ds.GetGeoTransform()
S=json.load(open(cfg.work(P['sec_in'])))
# bp[name] = (x, y, z, kind, rule, dist_cp) of every stored bankpoint; sec[name] = geometry clones of the section nodestrings (only counted/printed).
dsv=ogr.Open(cfg.layer('out','bankpoints')); v=dsv.GetLayer(); bp={}
for f in v: g=f.GetGeometryRef(); bp[f[FN]]=(g.GetX(),g.GetY(),f[FZ],f[FK],f[FR],f[FD])
dsb=ogr.Open(cfg.layer('out','boundary')); ns=dsb.GetLayer(0); sec={}
for f in ns:
    n=f[cfg['fields']['boundary']['name']]
    if cfg.is_section(n): sec[n]=f.GetGeometryRef().Clone()
print('sec layer',len(sec))
# secname(): section name of a record: its 'name' key, else prefix of its tag (or stream) + chainage number
def secname(s):
    if 'name' in s: return s['name']
    return cfg.section_name(P['stream_prefix'][s.get('tag', s['stream'])], int(round(s['s'])))
# cell(): (col,row) of the DTM cell containing (x,y). sampled(): profile along the section direction every 1 cm (step) up to T m: t, z, cols, rows.
def cell(x,y): return int(math.floor((x-gt[0])/gt[1])),int(math.floor((gt[3]-y)/(-gt[5])))
def sampled(s,sgn,T,step=STEP):
    t=np.arange(step/2,T,step); xs=s['x']+s['nx']*sgn*t; ys=s['y']+s['ny']*sgn*t
    cols=np.floor((xs-gt[0])/gt[1]).astype(int); rows=np.floor((gt[3]-ys)/(-gt[5])).astype(int)
    c0,c1,r0,r1=cols.min(),cols.max(),rows.min(),rows.max()
    A=b.ReadAsArray(int(c0),int(r0),int(c1-c0+1),int(r1-r0+1)).astype(float); z=A[rows-r0,cols-c0]; return t,z,cols,rows
# Counters: errz = z_dtm differs from DTM cell value (> 1e-6); err5 = bankpoint closer than the near-node radius to the top-of-bank line; ndiff = disagreements with the
# independent recomputation; total = number of bankpoints examined.
errz=0; err5=0; first=0; ndiff=[]; total=0; mid=0
# For each section and side: name n = S/V + abscissa as in dump.py; tt = toe distance, cc = top-of-bank distance, mx = next-bed cap (maxL/maxR).
for idx,s in enumerate(S):
    n=secname(s)
    for tag,sgn,tt,cc,mx in ((LEFT,1,s['tL'],s['cL'],s.get('maxL')),(RIGHT,-1,s['tR'],s['cR'],s.get('maxR'))):
        x,y,z,tipo,rg,t0=bp[f'{n}_{tag}']; total+=1
        c,r=cell(x,y); v=float(b.ReadAsArray(c,r,1,1)[0,0])
        if abs(v-z)>TOLZ: errz+=1
        # Wall points: only the z check applies; no independent recomputation.
        if tipo==KWALL: continue
        if t0>cc-R5+1e-6: err5+=1
        # Same limit rule as bank.py: cap, mid-width+15 m, or toe+15 m (B = bed width > 30 m or window < 2 m).
        cap=min(cc-R5, mx if mx else 1e9); mid=(s['cL']-s['cR'])/2*sgn; B=s['tL']+s['tR']
        lim=min(cap,mid+MIDW)
        if B>WIDE or lim<=tt+MINW: lim=min(cap,tt+TOEW)
        # Independent profile (1 cm samples) -> plateaus of equal value (runs) -> local maxima by prominence (same definition as bank.py analyse()).
        t,z_,co,ro=sampled(s,sgn,min(cc+EXTRA,MAXS))
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
            if prom(k)>=PROM_MIN: pk=(a,e,zz); break
        tp=np.where(mask)[0]
        ref=(pk[0],pk[1],pk[2]) if pk else (None,None,z_[tp[np.argmax(z_[tp])]])
        tipo2=KMAX if pk else KFALL
        # Disagreement if the kind differs or the height differs by more than 1 mm.
        if tipo2!=tipo or abs(ref[2]-z)>TOLK: ndiff.append((n,tag,tipo,tipo2,round(z,3),round(float(ref[2]),3)))
print('12 z_dtm mismatch',errz,'of',total,'; bankpoints closer than the near-node radius to top',err5)
print('13 independent 1-cm bankpoint comparison: differences',len(ndiff),ndiff[:20])
# For each disagreement: length (m) of the stored bankpoint's DTM cell that lies inside the valid search window. If <= 1 cm (0.0105) the 1 cm sampling
# could not see the cell, so the difference is a sampling artefact; larger values are printed as 'residual' (real discrepancies to investigate).
# in-range stretch of winning cell for the differing cases
wnd=[]
for n,tag,*rest in ndiff:
    s=[x for x in S if secname(x)==n][0]
    x,y,z,tp,rg,t0=bp[f'{n}_{tag}']; sgn=1 if tag==LEFT else -1
    c,r=cell(x,y); x0,y1=gt[0]+c*gt[1],gt[3]+r*gt[5]; x1,y0=x0+gt[1],y1+gt[5]
    dx,dy=s['nx']*sgn,s['ny']*sgn; ox,oy=s['x'],s['y']
    tt=sorted([(v-o)/dd for v,o,dd in ((x0,ox,dx),(x1,ox,dx),(y0,oy,dy),(y1,oy,dy)) if abs(dd)>1e-12]); a,b_=tt[1],tt[2]
    tto=s['tL'] if tag==LEFT else s['tR']; cc=s['cL'] if tag==LEFT else s['cR']; mx=s.get('maxL' if tag==LEFT else 'maxR'); cap=min(cc-R5, mx if mx else 1e9); mid=(s['cL']-s['cR'])/2*sgn; B=s['tL']+s['tR']; lim=min(cap,mid+MIDW)
    if B>WIDE or lim<=tto+MINW: lim=min(cap,tto+TOEW)
    wnd.append(round(min(b_,lim)-max(a,tto),4))
    if wnd[-1]>RESL: print('  residual',n,tag,tp,'z stored',round(z,3),'t',round(t0,3),'toe',round(tto,3),'lim',round(lim,3),'rest',rest)
print('in-range stretch of winning cell (m)',sorted(wnd),'; at most 1 cm:',sum(w<=RESL for w in wnd),'of',len(wnd))
