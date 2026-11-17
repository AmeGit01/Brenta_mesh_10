# write.py  (step 18, the only script that writes into layers/; previous: dump.py)
# Purpose: create the six *_50m GeoPackages in /home/amedeo/Documents/Brenta_mesh_10/layers/ from WD/work/write.json:
#          breaklines_50m, boundary_50m, regioni_ponti_50m (copies of the original layers with the modifications applied),
#          centerline_50m, centerpoints_50m, bankpoints_50m (new layers). The original layers (breaklines.gpkg, boundary.gpkg,
#          regioni_ponti.gpkg) are only read/copied and are NOT modified.
# WARNING: it writes into layers/ and does no backup. As coded, it stops at the start (SystemExit 'exists: <name>') if ANY of the six
#          output files already exists, so it does not overwrite existing outputs by itself; re-running requires deleting them by hand.
# Input  : WD/work/write.json (dump.py) and the three original GPKGs in layers/.
# Output : layers/{breaklines,boundary,regioni_ponti,centerline,centerpoints,bankpoints}_50m.gpkg ; prints 'written' at the end.
# Run    : /usr/bin/python3 write.py WD      (system python with osgeo/OGR; Anaconda python has no osgeo). CRS of the new layers: EPSG:25832.
import json, os, shutil, sys
from osgeo import ogr, osr, gdal
gdal.UseExceptions(); ogr.UseExceptions()
# SP = working directory; D = content of write.json; LAY = layers directory (hard-coded absolute path).
SP=sys.argv[1]; D=json.load(open(f'{SP}/work/write.json')); LAY='/home/amedeo/Documents/Brenta_mesh_10/layers'
# Safety guard: refuse to run if any of the output files exists already (nothing has been written yet at this point).
OUT=['breaklines_50m','boundary_50m','regioni_ponti_50m','centerline_50m','centerpoints_50m','bankpoints_50m']
for n in OUT:
    if os.path.exists(f'{LAY}/{n}.gpkg'): raise SystemExit('exists: '+n)
# mls(): MultiLineStringZM with a single part from [(x,y),...]; Z and M are set to 0 (appears to match the geometry type of the original layers).
def mls(coords):
    g=ogr.Geometry(ogr.wkbMultiLineStringZM); l=ogr.Geometry(ogr.wkbLineStringZM)
    for x,y in coords: l.AddPointZM(x,y,0.0,0.0)
    g.AddGeometry(l); return g
# srs: ETRS89 / UTM 32N (EPSG:25832) for the newly created layers.
srs=osr.SpatialReference(); srs.ImportFromEPSG(25832)
# breaklines_50m: copy of breaklines.gpkg, then replace the geometry of the moved (widened) features, looked up by fid, inside one transaction.
# breaklines
shutil.copyfile(f'{LAY}/breaklines.gpkg',f'{LAY}/breaklines_50m.gpkg')
ds=ogr.Open(f'{LAY}/breaklines_50m.gpkg',1); lyr=ds.GetLayer('breaklines'); ds.StartTransaction()
for k,c in D['bl'].items():
    f=lyr.GetFeature(int(k)); f.SetGeometry(mls(c)); lyr.SetFeature(f)
ds.CommitTransaction(); ds=None
# boundary_50m: copy of boundary.gpkg; replace geometry of the moved boundary features, then append the new section nodestrings
# with explicit fid, id and nome (other attribute fields are left NULL).
# boundary
shutil.copyfile(f'{LAY}/boundary.gpkg',f'{LAY}/boundary_50m.gpkg')
ds=ogr.Open(f'{LAY}/boundary_50m.gpkg',1); lyr=ds.GetLayer('boundary'); defn=lyr.GetLayerDefn(); ds.StartTransaction()
for k,c in D['bgn'].items():
    f=lyr.GetFeature(int(k)); f.SetGeometry(mls(c)); lyr.SetFeature(f)
for s in D['secs']:
    f=ogr.Feature(defn); f.SetFID(s['fid']); f.SetField('id',s['id']); f.SetField('nome',s['nome']); f.SetGeometry(mls(s['coords'])); lyr.CreateFeature(f)
ds.CommitTransaction(); ds=None
# regioni_ponti_50m: copy of regioni_ponti.gpkg; delete dropped region points by fid, then add the new points (nome, mat_id, max_area, buco only if not None).
# regioni
shutil.copyfile(f'{LAY}/regioni_ponti.gpkg',f'{LAY}/regioni_ponti_50m.gpkg')
ds=ogr.Open(f'{LAY}/regioni_ponti_50m.gpkg',1); lyr=ds.GetLayer('regioni_ponti'); defn=lyr.GetLayerDefn(); ds.StartTransaction()
for k in D['reg']['drop']: lyr.DeleteFeature(int(k))
for p in D['reg']['new']:
    f=ogr.Feature(defn); f.SetFID(p['fid']); f.SetField('nome',p['nome']); f.SetField('mat_id',p['mat_id']); f.SetField('max_area',p['max_area'])
    if p['buco'] is not None: f.SetField('buco',p['buco'])
    pt=ogr.Geometry(ogr.wkbPoint); pt.AddPoint_2D(p['x'],p['y']); f.SetGeometry(pt); lyr.CreateFeature(f)
ds.CommitTransaction(); ds=None
# New GeoPackages are created from scratch with the GPKG driver.
drv=ogr.GetDriverByName('GPKG')
# centerline_50m: two LineString features (asta_principale, brenta_vecchio) with fields nome and lung_m (length in m).
# centerline
ds=drv.CreateDataSource(f'{LAY}/centerline_50m.gpkg'); lyr=ds.CreateLayer('centerline_50m',srs,ogr.wkbLineString)
lyr.CreateField(ogr.FieldDefn('nome',ogr.OFTString)); lyr.CreateField(ogr.FieldDefn('lung_m',ogr.OFTReal))
for k,c in D['cl'].items():
    f=ogr.Feature(lyr.GetLayerDefn()); f.SetField('nome',{'main':'asta_principale','vecchio':'brenta_vecchio'}[k])
    l=ogr.Geometry(ogr.wkbLineString)
    for x,y in c: l.AddPoint_2D(x,y)
    f.SetField('lung_m',l.Length()); f.SetGeometry(l); lyr.CreateFeature(f)
ds=None
# points
# pts(): create a point GPKG `name` with the listed (field, type) schema; None values are left NULL; geometry from r['x'], r['y'].
def pts(name,rows,fields):
    ds=drv.CreateDataSource(f'{LAY}/{name}.gpkg'); lyr=ds.CreateLayer(name,srs,ogr.wkbPoint)
    for n,t in fields: lyr.CreateField(ogr.FieldDefn(n,t))
    ds.StartTransaction()
    for r in rows:
        f=ogr.Feature(lyr.GetLayerDefn())
        for n,_ in fields:
            if r.get(n) is not None: f.SetField(n,r[n])
        g=ogr.Geometry(ogr.wkbPoint); g.AddPoint_2D(r['x'],r['y']); f.SetGeometry(g); lyr.CreateFeature(f)
    ds.CommitTransaction(); ds=None
# centerpoints_50m: one point per section on the centerline; bankpoints_50m: two points per section (sx/dx) with z_dtm, kind (tipo) and rule (regola).
pts('centerpoints_50m',D['cp'],[('nome',ogr.OFTString),('stream',ogr.OFTString),('s_m',ogr.OFTReal),('dist_next',ogr.OFTReal)])
pts('bankpoints_50m',D['bp'],[('nome',ogr.OFTString),('sezione',ogr.OFTString),('s_m',ogr.OFTReal),('z_dtm',ogr.OFTReal),('dist_cp',ogr.OFTReal),('tipo',ogr.OFTString),('regola',ogr.OFTString),('prom',ogr.OFTReal)])
print('written')
