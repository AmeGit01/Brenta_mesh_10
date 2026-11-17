# stats.py  (exploratory, NOT needed to produce the layers)
# Purpose: width statistics of the main channel along the skeleton path: bed width B and corridor width W (bed + banks), km of reach with
#          bed > 30 m / > 20 m / corridor < 40 m, and percentiles by easting range and by 3 km bin. Used to decide the widening strategy.
# Inputs : WD/work/skel.pkl (skel.py: vv, bed, cor) and WD/work/net.pkl (net.py: paths['main']).  Output: print only.
# Run    : python3 stats.py WD      (Anaconda python3 with scipy; does not import core.py)
import pickle, sys, numpy as np, shapely, geopandas as gpd, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import LineString, Point
from scipy.ndimage import gaussian_filter1d
SP=sys.argv[1]
S=pickle.load(open(f'{SP}/work/skel.pkl','rb')); N=pickle.load(open(f'{SP}/work/net.pkl','rb'))
# vv = skeleton vertices, bed = bed polygon, cor = corridor polygon (bed + banks); a = main path vertices -> l; q = 1 m resampling smoothed with a gaussian (sigma 8 samples = 8 m).
vv,bed,cor=S['vv'],S['bed'],S['cor']; a=vv[N['paths']['main']]; l=LineString(a)
s=np.arange(0,l.length,1.0); q=shapely.get_coordinates(shapely.line_interpolate_point(l,s))
q=np.c_[gaussian_filter1d(q[:,0],8,mode='nearest'),gaussian_filter1d(q[:,1],8,mode='nearest')]
# w(i,poly): length (m) of the piece of the normal line through q[i] (+-700 m) lying inside `poly` that contains q[i] (NaN if none).
def w(i,poly):
    t=q[i+1]-q[i-1]; t/=np.hypot(*t); n=np.array([-t[1],t[0]]); x=LineString([q[i]-n*700,q[i]+n*700]).intersection(poly)
    for p in getattr(x,'geoms',[x]):
        if p.distance(Point(q[i]))<1e-6: return p.length
    return np.nan
# Sample every 5 m (indices I, ss = abscissa in m): W = corridor width, B = bed width, X = coordinates of the samples.
I=range(10,len(q)-10,5); W=np.array([w(i,cor) for i in I]); B=np.array([w(i,bed) for i in I]); X=q[list(I)]; ss=np.array(list(I))
print('main length',round(l.length),'sections ~',int(l.length/50))
print('km bed>30 (15 m semi-width rule impossible):',round(np.nanmean(B>30)*l.length/1000,1),' km bed>20:',round(np.nanmean(B>20)*l.length/1000,1))
print('km cor<40:',round(np.nanmean(W<40)*l.length/1000,1))
# rng(): percentiles 5/50/95 of W and B and fraction W<40 for samples whose easting is within [x0,x1] (named reaches).
def rng(x0,x1,lab):
    m=(X[:,0]>=x0)&(X[:,0]<=x1); print(f'{lab:32s} s={ss[m].min():6d}-{ss[m].max():6d} cor p5/50/95={np.nanpercentile(W[m],[5,50,95]).round(1)} bed p5/50/95={np.nanpercentile(B[m],[5,50,95]).round(1)} frac<40={np.nanmean(W[m]<40):.2f}')
rng(675800,679478,'monte (Caldonazzo-P13)')
rng(679780,684663,'tratto report (ex Test_Brenta)')
rng(684663,687200,'P20-divergenza')
rng(687200,690900,'Borgo (divergenza-confluenza)')
rng(690900,696000,'a valle Borgo')
rng(696000,705400,'valle')
# Same statistics (medians and mean easting) per 3 km bin of abscissa.
for km in range(0,35,3):
    m=(ss>=km*1000)&(ss<(km+3)*1000)
    print(km,'-',km+3,'km', 'cor med',np.nanmedian(W[m]).round(1),'bed med',np.nanmedian(B[m]).round(1), 'E',int(X[m,0].mean()))
