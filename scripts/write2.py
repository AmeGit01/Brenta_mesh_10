# write2.py  (stage 2, 2026-11-17; previous: prep_write.py, next: verify2.py)
# Purpose: write the N/V/B update into layers/*_50m.gpkg. It first makes a dated backup <name>_backup_20261117.gpkg of each of the six layers
#          (verified by SHA-256; stops if a backup exists), then: replaces the geometry of the changed breaklines, deletes all old S/V sections
#          from boundary and adds the new ones, deletes/adds region points, reads the DTM value for the bankpoints moved by hand, and REBUILDS
#          centerline_50m (fields nome, ramo, lung_m, s0_asta), centerpoints_50m and bankpoints_50m.
# Inputs : argv[1] = write2.json (prep_write.py), absolute path /home/amedeo/Documents/Brenta_mesh_10/layers (LAY) with the six *_50m.gpkg and DTM_finale.tif.
# Output : modified layers/*_50m.gpkg and the six backups; prints 'backup ok' per file, the boundary counts and 'written'.
# Run    : /usr/bin/python3 write2.py write2.json      (system python: needs osgeo/OGR; WRITES INTO layers/)
# Warning: not idempotent (a second run stops at the existing backups, which protects the backups).
# Write the N/V/B update into layers/*_50m.gpkg (system python, OGR). Dated backups first, verified by SHA-256.
import json, os, shutil, hashlib, sys
from osgeo import ogr, osr, gdal
gdal.UseExceptions(); ogr.UseExceptions()
# D = payload (argv[1]); LAY = layers folder (hard-coded); TAG = backup date tag; sha = SHA-256 of a file
D=json.load(open(sys.argv[1])); LAY='/home/amedeo/Documents/Brenta_mesh_10/layers'; TAG='20261117'
sha=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
# NAMES = the six layers touched
NAMES=['breaklines_50m','boundary_50m','regioni_ponti_50m','centerline_50m','centerpoints_50m','bankpoints_50m']
# backups: copy each layer, check identical hash, refuse to overwrite an existing backup
for n in NAMES:
    src=f'{LAY}/{n}.gpkg'; dst=f'{LAY}/{n}_backup_{TAG}.gpkg'
    if os.path.exists(dst):
        # rerun on the same day: the layer must first be restored from its backup (identical files)
        if sha(src)!=sha(dst): raise SystemExit('backup exists and differs from the layer: '+dst)
        print('backup already present and identical',dst); continue
    shutil.copyfile(src,dst); assert sha(src)==sha(dst); print('backup ok',dst)
# mls(c): MultiLineStringZM (z=m=0) from a list of (x,y), the geometry type of the breakline layer
def mls(c):
    g=ogr.Geometry(ogr.wkbMultiLineStringZM); l=ogr.Geometry(ogr.wkbLineStringZM)
    for x,y in c: l.AddPointZM(x,y,0.0,0.0)
    g.AddGeometry(l); return g
# (breaklines)
# breaklines: new geometry for the changed features
# open in update mode; one transaction; replace the geometry of each changed fid
ds=ogr.Open(f'{LAY}/breaklines_50m.gpkg',1); lyr=ds.GetLayer(0); ds.StartTransaction()
for k,c in D['bl'].items():
    f=lyr.GetFeature(int(k)); f.SetGeometry(mls(c)); lyr.SetFeature(f)
ds.CommitTransaction(); ds=None
# (boundary)
# boundary: drop all old sections (fid 64-800), add the new ones
# old = fids of all old sections (names S/V + 5 digits); delete them and add the new sections with the given fid/id/nome
ds=ogr.Open(f'{LAY}/boundary_50m.gpkg',1); lyr=ds.GetLayer(0); defn=lyr.GetLayerDefn(); ds.StartTransaction()
old=[f.GetFID() for f in lyr if f.GetField('nome')[0] in 'SV' and f.GetField('nome')[1:6].isdigit()]
for fid in old: lyr.DeleteFeature(fid)
for s in D['secs']:
    f=ogr.Feature(defn); f.SetFID(s['fid']); f.SetField('id',s['id']); f.SetField('nome',s['nome']); f.SetGeometry(mls(s['coords'])); lyr.CreateFeature(f)
ds.CommitTransaction(); ds=None; print('boundary: removed',len(old),'added',len(D['secs']))
# (region points)
# region points
# delete the dropped fids, add the new points (buco only if not null)
ds=ogr.Open(f'{LAY}/regioni_ponti_50m.gpkg',1); lyr=ds.GetLayer(0); defn=lyr.GetLayerDefn(); ds.StartTransaction()
for k in D['reg']['drop']: lyr.DeleteFeature(int(k))
for p in D['reg']['new']:
    f=ogr.Feature(defn); f.SetFID(p['fid']); f.SetField('nome',p['nome']); f.SetField('mat_id',p['mat_id']); f.SetField('max_area',p['max_area'])
    if p['buco'] is not None: f.SetField('buco',p['buco'])
    g=ogr.Geometry(ogr.wkbPoint); g.AddPoint_2D(p['x'],p['y']); f.SetGeometry(g); lyr.CreateFeature(f)
ds.CommitTransaction(); ds=None
# (DTM value)
# DTM value for the two bankpoints moved by hand
# read the DTM cell under each bankpoint with z_dtm None (moved by hand)
dt=gdal.Open(f'{LAY}/DTM_finale.tif'); gt=dt.GetGeoTransform(); band=dt.GetRasterBand(1)
for b in D['bp']:
    if b['z_dtm'] is None:
        c=int((b['x']-gt[0])//gt[1]); r=int((gt[3]-b['y'])//(-gt[5])); b['z_dtm']=float(band.ReadAsArray(c,r,1,1)[0,0])
# (rebuild)
# centerline, centerpoints, bankpoints: rebuilt (same schema, plus 'ramo'/'s0_asta' on the centerline)
# drv = GPKG driver, srs = EPSG:25832; delete the old files of the three rebuilt layers
drv=ogr.GetDriverByName('GPKG'); srs=osr.SpatialReference(); srs.ImportFromEPSG(25832)
for n in ('centerline_50m','centerpoints_50m','bankpoints_50m'): drv.DeleteDataSource(f'{LAY}/{n}.gpkg')
# centerline layer: LineString, fields nome, ramo, lung_m (length of the geometry), s0_asta (only if not None)
ds=drv.CreateDataSource(f'{LAY}/centerline_50m.gpkg'); lyr=ds.CreateLayer('centerline_50m',srs,ogr.wkbLineString)
for n,t in (('nome',ogr.OFTString),('ramo',ogr.OFTString),('lung_m',ogr.OFTReal),('s0_asta',ogr.OFTReal)): lyr.CreateField(ogr.FieldDefn(n,t))
for c in D['cl']:
    f=ogr.Feature(lyr.GetLayerDefn()); l=ogr.Geometry(ogr.wkbLineString)
    for x,y in c['coords']: l.AddPoint_2D(x,y)
    f.SetField('nome',c['nome']); f.SetField('ramo',c['ramo']); f.SetField('lung_m',l.Length())
    if c['s0_asta'] is not None: f.SetField('s0_asta',c['s0_asta'])
    f.SetGeometry(l); lyr.CreateFeature(f)
ds=None
# pts(name, rows, fields): create a point layer, one feature per dict (fields set only when not None), in one transaction
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
# centerpoints and bankpoints layers
pts('centerpoints_50m',D['cp'],[('nome',ogr.OFTString),('stream',ogr.OFTString),('s_m',ogr.OFTReal),('dist_next',ogr.OFTReal)])
pts('bankpoints_50m',D['bp'],[('nome',ogr.OFTString),('sezione',ogr.OFTString),('s_m',ogr.OFTReal),('z_dtm',ogr.OFTReal),('dist_cp',ogr.OFTReal),('tipo',ogr.OFTString),('regola',ogr.OFTString),('prom',ogr.OFTReal)])
# done
print('written')
