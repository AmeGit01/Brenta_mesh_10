# cl2.py - step 5. Smooths the raw centerlines (rawcl.pkl), resamples them at exactly 1 m (so that array INDEX = progressive distance s in m)
# and measures, at every point, the distances to the toe lines and to the top-of-bank lines along the perpendicular. Result = table cltab.pkl.
# Inputs : WD/work/graph.pkl (core.load_graph); WD/work/rawcl.pkl (cl.py: keys main, vecchio)
# Outputs: WD/work/cltab.pkl (dict name -> dict q (Nx2 xy, 1 m step), t (Nx6), B, SL, SR, W; name = 'main'|'vecchio'); WD/work/tab.png (plot); diagnostics on stdout
# Usage  : python3 cl2.py WD      (Anaconda python3; core.py in WD/work)
# Sign convention here: n = LEFT normal of the local direction; Rays.hits gives t>0 on the left, t<0 on the right. In this script 'L' (tl, cl, SL)
# refers to the NEGATIVE-t side (geometrically the right side); widen.py/place.py use L for the POSITIVE-t side.
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
from scipy.ndimage import gaussian_filter1d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
# RC = raw centerlines: RC['main'], RC['vecchio']
faces,rows=load_graph(); RC=pickle.load(open(f'{SP}/work/rawcl.pkl','rb'))
# tb = toe segments (bed boundary); tc = top-of-bank segments (boundary of bed+sponda+muro); Rb/Rc = ray-query objects on them
tb=boundary_segs(faces,rows,lambda n: cls(n)=='bed'); tc=boundary_segs(faces,rows,lambda n: cls(n) in('bed','sponda','muro'))
Rb,Rc=Rays(tb),Rays(tc)
# res(a,st): resample polyline a every st metres (default 1 m)
def res(a,st=1.0):
    l=LineString(a); s=np.arange(0,l.length,st); return shapely.get_coordinates(shapely.line_interpolate_point(l,s))
# w(q,i,R,step=10): hits of the normal at point i with the segments of R, within +-1500 m. Tangent from the chord q[i-10]..q[i+10] (local direction, 20 m); returns (hits, normal)
def w(q,i,R,step=10):
    a=q[max(i-step,0)]; b=q[min(i+step,len(q)-1)]; t=b-a; t/=np.hypot(*t); n=np.array([-t[1],t[0]]); h=R.hits(q[i],n,1500)
    return h,n
# smooth(q,bw): blend of a light smoothing (Gaussian sigma 6 m) and a heavy one (sigma 60 m) of the centerline.
# Weight a of the heavy one: 0 when the (smoothed) bed width bw <=15 m, 1 when >=50 m, linear between: narrow reaches follow the channel, wide ones are straightened
def smooth(q,bw):
    s0=np.c_[gaussian_filter1d(q[:,0],6,mode='nearest'),gaussian_filter1d(q[:,1],6,mode='nearest')]
    s1=np.c_[gaussian_filter1d(q[:,0],60,mode='nearest'),gaussian_filter1d(q[:,1],60,mode='nearest')]
    # blend by smoothed bed width: narrow -> s0, wide -> s1
    # a = weight of the heavy smoothing (0..1) per point, as a column vector
    a=np.clip((gaussian_filter1d(bw,50,mode='nearest')-15)/35,0,1)[:,None]
    return s0*(1-a)+s1*a
# table(q): for each point of q a row [tl,tr,cl,cr,0,0] (last two columns always 0, unused); NaN row if the normal does not cross toe and top lines on both sides.
# tl/tr: nearest toe crossing on the negative/positive side (tl<0<tr, signed m); cl/cr: nearest top-of-bank crossing on the negative/positive side (cl<0<cr)
def table(q):
    out=np.full((len(q),6),np.nan)
    for i in range(len(q)):
        hb,n=w(q,i,Rb); hc,_=w(q,i,Rc)
        # skip points where the normal misses the toe or top lines on one side
        if len(hb)==0 or not (hb>0).any() or not (hb<0).any() or len(hc)==0 or not (hc>0).any() or not (hc<0).any(): continue
        # nearest crossings on each side: hb<0 -> max (closest), hb>0 -> min
        tl=hb[hb<0].max(); tr=hb[hb>0].min(); cl=hc[hc<0].max(); cr=hc[hc>0].min()
        out[i]=[tl,tr,cl,cr,0,0]
    return out
# res1 = results by name
res1={}
for name in ['main','vecchio']:
    # resample the raw path at 1 m
    q=res(RC[name])
    # first pass widths to drive smoothing
    # t = first table; bw = bed width (tr-tl, m), NaN replaced by 10 m
    t=table(q); bw=np.nan_to_num(t[:,1]-t[:,0],nan=10.); 
    # qs = smoothed centerline; s = its cumulative length (computed but not used afterwards)
    qs=smooth(q,bw); s=np.r_[0,np.cumsum(np.hypot(*np.diff(qs,axis=0).T))]
    # resample at exact 1 m
    # qf = final centerline (index i = distance s=i m); t = final table
    l=LineString(qs); ss=np.arange(0,l.length,1.0); qf=shapely.get_coordinates(shapely.line_interpolate_point(l,ss)); t=table(qf)
    # B = bed width (toe-to-toe); SL/SR = toe-to-top distance on the negative/positive side (bank width); W = total width top-to-top (all in m)
    B=t[:,1]-t[:,0]; SL=t[:,0]-t[:,2]; SR=t[:,3]-t[:,1]; W=t[:,3]-t[:,2]
    # prints length, number of points with no crossing, percentiles of B, and of the bank widths SL/SR
    print(name,'L',round(l.length,1),'in-bed miss',int(np.isnan(t[:,0]).sum()),'B p5/50/95',np.nanpercentile(B,[5,50,95]).round(1),'bank L',np.nanpercentile(SL,[1,5,50,95]).round(1),'R',np.nanpercentile(SR,[1,5,50,95]).round(1))
    # store
    res1[name]=dict(q=qf,t=t,B=B,SL=SL,SR=SR,W=W)
# save table
pickle.dump(res1,open(f'{SP}/work/cltab.pkl','wb'))
# M = main-stem results
M=res1['main']
# R(a,b): percentiles (1% and 50%) of B,SL,SR,W for the points with index (=s in m) in [a,b)
def R(a,b):
    m=(np.arange(len(M['q']))>=a)&(np.arange(len(M['q']))<b)
    return [ (np.nanpercentile(M[k][m],[1,50]).round(1).tolist()) for k in('B','SL','SR','W')]
# report per 3 km block of the main stem: percentiles and fraction of points where a bank is narrower than 10 m / 20 m (sections where widening will be needed)
for a in range(0,34001,3000):
    print('s',a,a+3000,R(a,a+3000),'frac bank<10',round(float(np.nanmean((M['SL'][a:a+3000]<10)|(M['SR'][a:a+3000]<10))),2),'bank<20',round(float(np.nanmean((M['SL'][a:a+3000]<20)|(M['SR'][a:a+3000]<20))),2))
# diagnostic plot: bank widths (top) and bed/total width (bottom, dotted = 40 m) along s; saved to work/tab.png
fig,ax=plt.subplots(2,1,figsize=(16,6))
ax[0].plot(M['SL'],lw=.4,label='sponda sx');ax[0].plot(M['SR'],lw=.4,label='sponda dx');ax[0].set_ylim(0,60);ax[0].legend();ax[0].axhline(20,c='k',ls=':')
ax[1].plot(M['B'],lw=.5);ax[1].plot(M['W'],lw=.5);ax[1].axhline(40,c='k',ls=':');ax[1].set_ylim(0,250)
plt.tight_layout();plt.savefig(f'{SP}/work/tab.png',dpi=75)
