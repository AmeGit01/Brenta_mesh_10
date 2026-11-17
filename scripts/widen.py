# widen.py - step 7. Computes how far each top-of-bank line (ciglio) must be moved outward and produces the new geometry of the moved lines.
# Rule: main stem upstream of Borgo (s <= BORGO_END) and Brenta vecchio: total corridor width (top to top) at least 40.10 m, shift split symmetrically;
# main stem downstream of Borgo: each bank (toe-to-top) at least 16.05 m. Shifts are capped to keep >= 5 m from the next outer line. Anthropic banks/walls are never moved.
# Inputs : WD/work/graph.pkl (core.load_graph); WD/work/chains.pkl (chains.py); WD/work/cltab.pkl (cl2.py, only the centerline 'q');
#          WD/in/boundary.gpkg
# Outputs: WD/work/widen.pkl (dict bmove, bgeo, endT, newf, ST, sL, sR, PTS, SH, DN) read by apply_widen.py; diagnostics on stdout
# Usage  : python3 widen.py WD      (Anaconda python3; core.py in WD/work)
# Convention: n = left normal of the centerline; L = positive-t side (left), R = negative-t side; all distances are in m measured from the centerline unless stated.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from scipy.spatial import cKDTree
from shapely.ops import unary_union, polygonize
# C = chains.pkl; T0 = cltab.pkl
faces,rows=load_graph(); C=pickle.load(open(f'{SP}/work/chains.pkl','rb')); T0=pickle.load(open(f'{SP}/work/cltab.pkl','rb'))
# unpack the chain data (see chains.py): feat fid->xy, S segments, meta (fid,i), L/R face names, Lc/Rc classes, istop flags
feat,S,meta,L,R,Lc,Rc,istop=[C[k] for k in 'feat S meta L R Lc Rc istop'.split()]
# tb = toe segments (bed); tc = top-of-bank segments (bed+sponda+muro); to = outer segments (also including 'intermedio'); ray queries Rb, Rc_, Ro
tb=boundary_segs(faces,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(faces,rows,lambda n: cls(n) in('bed','sponda','muro')); to=boundary_segs(faces,rows,lambda n: cls(n) in('bed','sponda','muro','inter'))
Rb,Rc_,Ro=Rays(tb),Rays(tc),Rays(to)
# tree of faces and face->name map (used only by the unused spondaname())
tree=shapely.STRtree(faces); fname={r['face']:r['nome'] for r in rows}
# BORGO_END: distance s (m) along the main stem where the urban reach of Borgo ends; downstream of it the 16.05 m-per-bank rule is used
BORGO_END=17335.  # m on main stem (confluence/urban reach end)
# ST: one row per centerline point and per name
ST=[]
for name in ('main','vecchio'):
    # q = centerline points (1 m step, index i = s in m)
    q=T0[name]['q']; N=len(q)
    for i in range(N):
        # a,b = neighbours; t = unit tangent; n = left normal
        a=q[max(i-1,0)]; b=q[min(i+1,N-1)]; t=(b-a)/np.hypot(*(b-a)); n=np.array([-t[1],t[0]])
        # hb/hc/ho = signed hit distances (m) of the normal with toe / top / outer lines (+-1500 m)
        hb=Rb.hits(q[i],n,1500); hc=Rc_.hits(q[i],n,1500); ho=Ro.hits(q[i],n,1500)
        # skip points where the normal does not cross the toe on both sides
        if not(len(hb) and (hb>0).any() and (hb<0).any()): continue
        # tL,tR = centerline-to-toe distances (+side, -side), both positive m
        tL=hb[hb>0].min(); tR=-hb[hb<0].max()
        # cL,cR = centerline-to-top-of-bank distances beyond the toe (NaN if none)
        cL=hc[hc>tL-1e-6].min() if (hc>tL-1e-6).any() else np.nan; cR=-hc[hc<-tR+1e-6].max() if (hc<-tR+1e-6).any() else np.nan
        # W = distance between the two top lines (m)
        W=cL+cR if np.isfinite(cL+cR) else np.nan
        # oL,oR = distance to the next outer line (class inter included) beyond the top; NaN if none
        oL=ho[ho>cL+1e-6].min() if np.isfinite(cL) and (ho>cL+1e-6).any() else np.nan; oR=-ho[ho<-cR-1e-6].max() if np.isfinite(cR) and (ho<-cR-1e-6).any() else np.nan
        # row: (name, i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR)
        ST.append((name,i,q[i][0],q[i][1],n[0],n[1],tL,tR,cL,cR,W,oL,oR))
# D = numeric columns as float array; nm = names
D=np.array([s[1:] for s in ST],float); nm=np.array([s[0] for s in ST])
# unpack columns (ix = index i = s in m)
ix,x,y,nxx,nyy,tL,tR,cL,cR,W,oL,oR=D.T
# shift rule
# rule(...) -> (shift left, shift right) in m, the outward displacement of the top line
def rule(name,i,W,tL,tR,cL,cR):
    # main downstream of Borgo: bank width (cL-tL, toe to top) brought to 16.05 m, per side
    if name=='main' and i>BORGO_END:
        return max(0,16.05-(cL-tL)),max(0,16.05-(cR-tR))
    # no valid width: no shift
    if not np.isfinite(W): return 0,0
    # otherwise corridor width W brought to 40.10 m (symmetric shift)
    s=max(0,(40.10-W)/2); return s,s
# sL,sR = shift per point; computed only where both top distances are finite
sL=np.zeros(len(D)); sR=np.zeros(len(D))
for j,(n0,i,w,a,b,c,d) in enumerate(zip(nm,ix,W,tL,tR,cL,cR)):
    if not np.isfinite(c+d): continue
    sL[j],sR[j]=rule(n0,i,w,a,b,c,d)
# outward clearance: keep >=5 m to next line
# okL/okR = gap between top line and next outer line (1e9 m if none)
okL=np.nan_to_num(oL-cL,nan=1e9); okR=np.nan_to_num(oR-cR,nan=1e9)
# cap: never shift more than (gap - 5 m), so that at least 5 m remain to the next line
capL=np.minimum(sL,np.maximum(okL-5,0)); capR=np.minimum(sR,np.maximum(okR-5,0))
# (prints number of points whose shift was reduced by the clearance cap)
print('clamped by clearance L/R',int((capL<sL-1e-6).sum()),int((capR<sR-1e-6).sum()))
sL,sR=capL,capR
# prints, per name, fraction of points widened on L/R and maximum shifts
for n0 in ('main','vecchio'):
    m=nm==n0; print(n0,'widen frac L,R',round(float((sL[m]>0).mean()),3),round(float((sR[m]>0).mean()),3),'max',round(float(sL[m].max()),2),round(float(sR[m].max()),2))
# same statistics for the main stem downstream of Borgo; 'km' = number of points (=m)/1000 widened
m=(nm=='main')&(ix>BORGO_END); print('downstream of Borgo: widened frac L,R',round(float((sL[m]>0).mean()),3),round(float((sR[m]>0).mean()),3),'km',round(float((sL[m]>0).sum()/1000),2),round(float((sR[m]>0).sum()/1000),2),'max',round(float(sL[m].max()),2),round(float(sR[m].max()),2))
# station points on top line
# TL/TR = top-of-bank points on the left/right at each centerline point (centre + n*cL, centre - n*cR)
TL=np.c_[x+nxx*cL,y+nyy*cL]; TR=np.c_[x-nxx*cR,y-nyy*cR]
vL=np.isfinite(cL); vR=np.isfinite(cR)
# PTS = all top stations (valid ones), SH = their shifts (m), DN = unit outward directions (left: +n, right: -n)
PTS=np.vstack([TL[vL],TR[vR]]); SH=np.r_[sL[vL],sR[vR]]; DN=np.vstack([np.c_[nxx,nyy][vL],-np.c_[nxx,nyy][vR]]); 
# kd = KD-tree of PTS; used to find the shift applicable to any vertex of a top line (within 3 m)
kd=cKDTree(PTS)
# sponda_antro / muro exclusion by point lookup
# spondaname(p,n,sign): name of the face 0.5 m behind p along -n; defined but never called
def spondaname(p,n,sign=1):
    pt=Point(p-n*0.5); idx=tree.query(pt,predicate='within'); 
    return fname.get(int(idx[0]),'') if len(idx) else ''
# shift_at(P): shift (m) and outward direction at point P from the nearest top station; (0,None) if none within 3 m
def shift_at(P):
    d,j=kd.query(P)
    if d>3.0: return 0.0,None
    return SH[j],DN[j]
# feature list needing change
topfid=collections.defaultdict(set)
for (fid,i),t in zip(meta,istop):
    if t: topfid[fid].add(i)
ALL=set(topfid)
print('top feats total',len(ALL))
# newf: fid -> new vertex array; changed = counter; bmove: tag -> new position of a forced point
newf={}; changed=0; bmove={}
# forced vertices: ends of other lines lying on a top line (interior T)
# keys/LS/TT: list of fids, their LineStrings, STRtree
keys=list(feat); LS=[LineString(feat[k]) for k in keys]; TT=shapely.STRtree(LS)
# forced[f2]: list of (original point, unit direction of the incident line towards the point, tag ('bl',fid,end))
forced=collections.defaultdict(list)
for k,a in feat.items():
    if not len(a): continue
    # for each end e (first/last vertex) of line k: top features within 1 mm
    for e in (0,-1):
        idx=TT.query(Point(a[e]),predicate='dwithin',distance=1e-3)
        for i in idx:
            f2=keys[i]
            if f2==k or f2 not in ALL: continue
            b=feat[f2]
            # ignore if the end of k coincides with an end of f2 (a plain end-to-end junction, not a T)
            if min(np.hypot(*(b[0]-a[e])),np.hypot(*(b[-1]-a[e])))<1e-3: continue
            # u = direction of the incident line at its end
            u=a[e]-a[1 if e==0 else -2]; u=u/np.hypot(*u); forced[f2].append((a[e].copy(),u,('bl',k,e)))
# same for boundary lines (bgeo: boundary fid -> vertices); tag ('bd',k,e)
bdf=gpd.read_file(f'{SP}/in/boundary.gpkg',fid_as_index=True); bgeo={}
for k,g in bdf.geometry.items():
    a=shapely.get_coordinates(next(iter(shapely.get_parts(g)))); bgeo[k]=a
    for e in (0,-1):
        idx=TT.query(Point(a[e]),predicate='dwithin',distance=1e-3)
        # chains = top features touched by the boundary end; others = non-top breaklines ending at the same point
        chains=[keys[i] for i in idx if keys[i] in ALL]
        others=[keys[i] for i in idx if keys[i] not in ALL and min(np.hypot(*(feat[keys[i]][0]-a[e])),np.hypot(*(feat[keys[i]][-1]-a[e])))<1e-3]
        if not chains: continue
        # boundary end shared with another (non-top) breakline: left as is
        if others: print('  boundary end coincident w breakline: left as is',bdf.nome[k],e,others[:2]); continue
        f2=chains[0]; b=feat[f2]
        if min(np.hypot(*(b[0]-a[e])),np.hypot(*(b[-1]-a[e])))<1e-3: 
            print('  boundary end at chain vertex',bdf.nome[k],e); 
        u=a[e]-a[1 if e==0 else -2]; u=u/np.hypot(*u); forced[f2].append((a[e].copy(),u,('bd',k,e)))
print('forced T points',sum(len(v) for v in forced.values()))
endT={}
# main loop: build the new geometry of each top feature
for fid in ALL:
    a=feat[fid]; idx=topfid[fid]
    # exclude antro bank features
    sa=[(L[np.where((np.array([m[0] for m in meta])==fid))[0]],R[np.where((np.array([m[0] for m in meta])==fid))[0]])]
    labs=set(sa[0][0])|set(sa[0][1])
    if 'sponda_antro' in labs: continue
    # mixed features (only some segments are top): not moved, reported
    if len(idx)!=sum(np.hypot(*(a[i+1]-a[i]))>1e-6 for i in range(len(a)-1)):   # mixed feature: leave and report
        print('mixed skip',fid); continue
    # densify 2 m
    # s = chainages along the feature: every 2 m, the end, all original vertices and the forced points; P = the points
    l=LineString(a); fp=[l.project(Point(p[0])) for p in forced.get(fid,[])]; s=np.unique(np.r_[np.arange(0,l.length,2.0),[l.length],[l.project(Point(p)) for p in a],fp]); P=shapely.get_coordinates(shapely.line_interpolate_point(l,s))
    # out = displaced points
    out=[]; moved=False
    for p in P:
        # shifted by the local widening if >1 mm
        sh,n=shift_at(p)
        if sh>1e-3: out.append(p+n*sh); moved=True
        else: out.append(p)
    # feature not touched by widening: keep the original
    if not moved: continue
    out=np.array(out)
    # forced vertices: move along the incident line direction u so that the T junction stays on the incident line (u/c, c=cos angle with n); if the angle is too oblique (c<=0.5) move along n
    for v,(orig,u,tag) in zip(fp,forced.get(fid,[])):
        i=int(np.argmin(np.abs(s-v))); sh,n=shift_at(P[i])
        if sh>1e-3:
            c=float(u@n); out[i]=(P[i]+u*sh/c) if c>0.5 else (P[i]+n*sh)
    # isf[i] = point is a forced vertex
    isf=np.zeros(len(s),bool)
    for v in fp: isf[int(np.argmin(np.abs(s-v)))]=True
    # split into parts at the forced vertices, simplify each (tolerance 0.02 m) then thin vertices closer than 2 m, so that the forced vertices are retained
    cuts=[0]+[i for i in np.where(isf)[0] if 0<i<len(s)-1]+[len(s)-1]
    res=[]
    for c0,c1 in zip(cuts[:-1],cuts[1:]):
        part=shapely.get_coordinates(LineString(out[c0:c1+1]).simplify(0.02,preserve_topology=False))
        keep=[0]
        for i in range(1,len(part)-1):
            if np.hypot(*(part[i]-part[keep[-1]]))>=2.0: keep.append(i)
        keep.append(len(part)-1); part=part[keep]
        # join the parts without duplicating the shared vertex
        res.append(part if not res else part[1:])
    # b = new vertex array
    b=np.vstack(res); newf[fid]=b; changed+=1
    # record where each forced point went: endT keyed by original xy rounded to mm; bmove keyed by tag
    for v,(orig,u,tag) in zip(fp,forced.get(fid,[])):
        i=int(np.argmin(np.abs(s-v))); endT[(round(orig[0],3),round(orig[1],3))]=out[i].copy(); bmove[tag]=out[i].copy()
# changed top features
print('changed top features',changed)
# save: bmove (tag->new xy), bgeo (original boundary vertices), endT, newf (fid->new xy), ST=(names,D), sL/sR shifts, PTS/SH/DN top stations
pickle.dump(dict(bmove=bmove,bgeo=bgeo,endT=endT,newf=newf,ST=(nm,D),sL=sL,sR=sR,PTS=PTS,SH=SH,DN=DN),open(f'{SP}/work/widen.pkl','wb'))
