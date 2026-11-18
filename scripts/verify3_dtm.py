# verify3_dtm.py  (stage 4, 2026-11-18; companion of verify3.py)
# Purpose: check that z_dtm of every bankpoint equals the value of the DTM cell under the point (no interpolation), and that no value is
#          nodata or null. Read-only.
# Inputs : /home/amedeo/Documents/Brenta_mesh_10/layers/bankpoints_50m.gpkg and DTM_finale.tif.
# Output : print: number of bankpoints checked, maximum absolute difference, list of mismatches (> 1e-6 m), nulls and nodata.
# Run    : /usr/bin/python3 scripts/verify3_dtm.py      (system python: needs osgeo/GDAL)
from osgeo import ogr, gdal
gdal.UseExceptions(); ogr.UseExceptions()
L='/home/amedeo/Documents/Brenta_mesh_10/layers'
dt=gdal.Open(f'{L}/DTM_finale.tif'); gt=dt.GetGeoTransform(); band=dt.GetRasterBand(1); nd=band.GetNoDataValue()
ds=ogr.Open(f'{L}/bankpoints_50m.gpkg'); lyr=ds.GetLayer(0); n=0; dmax=0.0; bad=[]; nul=[]; ndv=[]
for f in lyr:
    g=f.GetGeometryRef(); x,y=g.GetX(),g.GetY(); z=f.GetField('z_dtm'); n+=1
    c=int((x-gt[0])//gt[1]); r=int((gt[3]-y)//(-gt[5])); v=float(band.ReadAsArray(c,r,1,1)[0,0])
    if z is None: nul.append(f.GetField('nome')); continue
    if nd is not None and v==nd: ndv.append(f.GetField('nome'))
    d=abs(z-v); dmax=max(dmax,d)
    if d>1e-6: bad.append((f.GetField('nome'),z,v))
print(f'bankpoints {n}; max |z_dtm - DTM cell| {dmax:.2e} m; mismatches {bad}; null {nul}; nodata {ndv}', 'OK' if not bad and not nul and not ndv else '**CHECK**')
