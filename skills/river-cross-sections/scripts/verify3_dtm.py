# verify3_dtm.py - check z of every bankpoint against the DTM cell under the point.
# Purpose: z_dtm of every bankpoint must equal the value of the DTM cell under the point (no interpolation), and no value may be nodata or
#          null. Read-only. Companion of verify3.py.
# Inputs : config keys: outputs.bankpoints, inputs.dtm, fields.bankpoints (name, z).
# Outputs: print: number of bankpoints checked, maximum absolute difference, list of mismatches (> 1e-6 m), nulls and nodata.
# Run    : cd <working folder>; /usr/bin/python3 <toolkit>/scripts/verify3_dtm.py [-c rcs_config.json]   (OGR interpreter: needs osgeo/GDAL)
# Origin : Brenta project, verify3_dtm.py, 2026-11-18.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from osgeo import ogr, gdal
gdal.UseExceptions(); ogr.UseExceptions()
cfg = common.load(common.parser('check bankpoint z against the DTM').parse_args())
FN, FZ = cfg.f('bankpoints', 'name'), cfg.f('bankpoints', 'z')
dt=gdal.Open(cfg.dtm()); gt=dt.GetGeoTransform(); band=dt.GetRasterBand(1); nd=band.GetNoDataValue()
ds=ogr.Open(cfg.layer('out', 'bankpoints')); lyr=ds.GetLayer(0); n=0; dmax=0.0; bad=[]; nul=[]; ndv=[]
for f in lyr:
    g=f.GetGeometryRef(); x,y=g.GetX(),g.GetY(); z=f.GetField(FZ); n+=1
    c=int((x-gt[0])//gt[1]); r=int((gt[3]-y)//(-gt[5])); v=float(band.ReadAsArray(c,r,1,1)[0,0])
    if z is None: nul.append(f.GetField(FN)); continue
    if nd is not None and v==nd: ndv.append(f.GetField(FN))
    d=abs(z-v); dmax=max(dmax,d)
    if d>1e-6: bad.append((f.GetField(FN),z,v))
print(f'bankpoints {n}; max |z_dtm - DTM cell| {dmax:.2e} m; mismatches {bad}; null {nul}; nodata {ndv}', 'OK' if not bad and not nul and not ndv else '**CHECK**')
