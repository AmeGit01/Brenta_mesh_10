# check2.py  (step 19: verification of the widening, read back from disk)
# Purpose: verify that boundary/breaklines were changed only where intended, that no changed line crosses another, and that the channel widths
#          reach the targets (upstream of Borgo, s <= 17335 m: top-of-bank to top-of-bank width >= 40 m; downstream: each bank >= 16 m; vecchio >= 40 m).
#          Print-only, labelled A-H; see docs/scripts/check2.md.
# Inputs : layers/{breaklines_50m,breaklines,boundary_50m,boundary,regioni_ponti,centerline_50m}.gpkg (absolute path). NB: the region points used
#          to classify faces are those of the ORIGINAL regioni_ponti.gpkg (not _50m). core.py is imported from WD/work.
# Run    : python3 check2.py WD      (Anaconda python3)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from shapely.ops import unary_union, polygonize
from scipy.spatial import cKDTree
import json
# rd(): read layer by name with fid index. bl/bd/rg/cl = breaklines_50m, boundary_50m, regioni_ponti (original), centerline_50m; *0 = originals.
L='/home/amedeo/Documents/Brenta_mesh_10/layers'
rd=lambda n: gpd.read_file(f'{L}/{n}.gpkg',fid_as_index=True)
bl,bl0,bd,bd0,rg,cl=rd('breaklines_50m'),rd('breaklines'),rd('boundary_50m'),rd('boundary'),rd('regioni_ponti'),rd('centerline_50m')
def co(g): return shapely.get_coordinates(next(iter(shapely.get_parts(g))))
# A. boundary features whose geometry differs from the original: (fid, nome, max abs coordinate shift in m).
dif=[(k,bd0.nome[k],float(np.abs(co(bd.geometry[k])-co(bd0.geometry[k])).max())) for k in bd0.index if not bd.geometry[k].equals_exact(bd0.geometry[k],0)]; print('A. boundary features changed',dif)
# B. breaklines whose coordinates (count or values) differ from the original: fA = new coordinates, fB = original coordinates (empty geometries excluded).
keep=bl.dropna(subset=['geometry']); keep=keep[~keep.geometry.is_empty]
fA={k:co(g) for k,g in keep.geometry.items()}
fB={k:co(g) for k,g in bl0.dropna(subset=['geometry']).geometry.items() if not g.is_empty}
chg=[k for k in fA if not (len(fA[k])==len(fB[k]) and np.array_equal(fA[k],fB[k]))]; print('B. breaklines changed',len(chg))
# C. for each changed line, other lines that it properly crosses ('crosses' predicate); also list lines that are not simple (self-intersecting).
ls={k:LineString(v) for k,v in fA.items()}
rs=[ls[k] for k in ls]; keys=list(ls); T=shapely.STRtree(rs)
xs=[]; ov=0
for k in chg:
    for j in T.query(ls[k],predicate='crosses'):
        o=keys[j]
        if o!=k: xs.append((k,o))
print('C. changed lines crossing another line',len(xs),xs[:20]); print('   not simple',[k for k in ls if not ls[k].is_simple][:10])
# D-F. Widths measured on the saved layers: rebuild the planar graph (breaklines + boundary excluding the section nodestrings named S#####/V#####),
# assign each face the name of an original region point it contains, and use rays against two outlines:
#   Rb = bed edges (toe), Rc = bed+sponda+muro edges (top of bank).
# widths from disk
# (dead code: the conditional expression is always None.)
gl=[LineString(v) for v in fA.values()]+[LineString(co(g)) for g in bd.geometry if not bd.nome[bd.index[list(bd.geometry).index(g)]].startswith(('S0','S1','S2','S3','V0'))] if False else None
# gb = boundary nodestrings that are not cross-sections (name = S or V followed by 5 digits).
gb=[LineString(co(g)) for n,g in zip(bd.nome,bd.geometry) if not ((n[0] in 'SV') and n[1:6].isdigit())]
fc=list(polygonize(unary_union(list(ls.values())+gb))); t=shapely.STRtree(fc); rg2=rg.dropna(subset=['geometry']); ix=t.query(rg2.geometry.values,predicate='within')
rows=[]; seen=set()
for p,f in zip(*ix):
    if int(f) in seen: continue
    seen.add(int(f)); rows.append(dict(face=int(f),nome=rg2.nome.iloc[int(p)]))
print('D. faces',len(fc),'with point',len(rows))
tb=boundary_segs(fc,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(fc,rows,lambda n: cls(n) in('bed','sponda','muro'))
Rb,Rc=Rays(tb),Rays(tc)
# For each centerline: sample every 0.5 m (s from 1 m to length-1 m); normal from the chord s-1..s+1 m; for each sample find the nearest bed edge on the left (tl)
# and right (tr), then the nearest top-of-bank edge beyond each toe (cl_, cr_). W = cl_+cr_ = width top-to-top; SL = cl_-tl, SR = cr_-tr = bank widths (m).
# Samples without a bed edge or top edge on both sides give NaN.
for nm in ('asta_principale','brenta_vecchio'):
    ln=cl[cl.nome==nm].geometry.iloc[0]
    ss=np.arange(1,ln.length-1,0.5); P=shapely.get_coordinates(shapely.line_interpolate_point(ln,ss)); A=shapely.get_coordinates(shapely.line_interpolate_point(ln,ss-1)); B=shapely.get_coordinates(shapely.line_interpolate_point(ln,ss+1)); d=(B-A)/np.hypot(*(B-A).T)[:,None]; n=np.c_[-d[:,1],d[:,0]]
    W=[];SL=[];SR=[]; isborgo=[]
    for i in range(len(ss)):
        hb=Rb.hits(P[i],n[i],1500); hc=Rc.hits(P[i],n[i],1500)
        if len(hb)==0 or not(hb>0).any() or not(hb<0).any(): W.append(np.nan);SL.append(np.nan);SR.append(np.nan);continue
        tl=hb[hb>0].min(); tr=-hb[hb<0].max(); cc1=hc[hc>tl-1e-6]; cc2=hc[hc<-tr+1e-6]
        if not len(cc1) or not len(cc2): W.append(np.nan);SL.append(np.nan);SR.append(np.nan);continue
        cl_=cc1.min(); cr_=-cc2.max(); W.append(cl_+cr_); SL.append(cl_-tl); SR.append(cr_-tr)
    W,SL,SR=np.array(W),np.array(SL),np.array(SR)
    # E: main stream upstream of s=17335 m (end of Borgo): W < 40 should not occur (count and runs listed). F: downstream: bank widths SL/SR < 16 (count and runs).
    # E2 (else branch): Brenta vecchio: W < 40 (count and runs).
    if nm=='asta_principale':
        up=ss<=17335; dn=ss>17335
        print(f'E. main upstream of Borgo-end: {int(up.sum())} samples; W min/p1/median {np.nanmin(W[up]):.2f} {np.nanpercentile(W[up],1):.2f} {np.nanmedian(W[up]):.2f}; W<40 samples {int((W[up]<40).sum())} ({(W[up]<40).mean()*100:.2f}%)')
        m=up&(W<40)
        print('   runs W<40:',[ (round(float(a)),round(float(b)),round(float(np.nanmin(W[(ss>=a)&(ss<=b)])),1)) for a,b in zip(ss[np.where(np.diff(np.r_[0,m.astype(int),0])==1)[0]],ss[np.where(np.diff(np.r_[0,m.astype(int),0])==-1)[0]-1])])
        print(f'F. main downstream: bank L min/p1 {np.nanmin(SL[dn]):.2f} {np.nanpercentile(SL[dn],1):.2f}, R {np.nanmin(SR[dn]):.2f} {np.nanpercentile(SR[dn],1):.2f}; side<16: L {int((SL[dn]<16).sum())} R {int((SR[dn]<16).sum())}')
        m=dn&((SL<16)|(SR<16))
        print('   runs bank<16:',[(round(float(a)),round(float(b))) for a,b in zip(ss[np.where(np.diff(np.r_[0,m.astype(int),0])==1)[0]],ss[np.where(np.diff(np.r_[0,m.astype(int),0])==-1)[0]-1])][:30])
    else:
        print(f'E2. vecchio W min/p1/med {np.nanmin(W):.2f} {np.nanpercentile(W,1):.2f} {np.nanmedian(W):.2f}; W<40 {int((W<40).sum())} of {len(W)}')
        m=W<40; print('   runs',[(round(float(a)),round(float(b)),round(float(np.nanmin(W[(ss>=a)&(ss<=b)])),1)) for a,b in zip(ss[np.where(np.diff(np.r_[0,m.astype(int),0])==1)[0]],ss[np.where(np.diff(np.r_[0,m.astype(int),0])==-1)[0]-1])][:30])

# crossings of changed cross-lines already present originally?
# G. for the crossing pairs found in C, whether the same pair already crossed in the original geometry (True = pre-existing, not caused by the widening).
Lo={k:LineString(v) for k,v in fB.items()}
print('G. pairs crossing in original too:',[(a,b,Lo[a].crosses(Lo[b])) for a,b in xs])
# H. sections (boundary nodestrings S#####/V#####) that intersect exactly 3 breaklines: listed with the intersection points (informational).
Tt=shapely.STRtree(list(ls.values())); 
sec=bd[[ (n[0] in 'SV') and n[1:6].isdigit() for n in bd.nome]]
for nome,g in zip(sec.nome,sec.geometry):
    l=LineString(co(g)); ids=[keys[i] for i in Tt.query(l,predicate='intersects')]
    if len(ids)==3: print('H. 3-lines',nome,ids,[Point(p).wkt for p in shapely.get_coordinates(l.intersection(unary_union([ls[i] for i in ids])))])
