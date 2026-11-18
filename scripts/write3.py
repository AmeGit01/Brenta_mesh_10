# write3.py  (stage 4, 2026-11-18; previous: sync_cp_bp.py or fix_manual.py, next: verify3.py)
# Purpose: write a payload into layers/*_50m.gpkg, after a dated backup of every layer the payload touches (<name>_backup_<TAG>.gpkg,
#          verified by SHA-256; stops if a backup with that tag already exists). All keys are optional:
#            bl      {fid: [[x,y],...]}  new geometry of breaklines (MultiLineStringZM, z = m = 0);
#            bd      {fid: [[x,y],...]}  new geometry of boundary features (MultiLineStringZM, z = m = 0), name/id unchanged;
#            reg_new [{nome, mat_id, max_area, buco, x, y}]  new region points (fid = current maximum + 1, ...);
#            cl, cp, bp  REBUILD centerline_50m, centerpoints_50m, bankpoints_50m (same schema as write2.py); bankpoints with z_dtm None get
#                        the value of the DTM cell under the point.
# Inputs : argv[1] = payload json (sync_cp_bp.py -> cl/cp/bp; fix_manual.py -> bd/bl/reg_new), argv[2] = backup tag (e.g. 20261118b);
#          absolute path LAY with the *_50m.gpkg and DTM_finale.tif.
# Output : the modified layers and their backups; prints 'backup ok', what was written and 'written'.
# Run    : /usr/bin/python3 scripts/write3.py WD/write3.json 20261118b      (system python: needs osgeo/OGR; WRITES INTO layers/)
# History: first run 2026-11-18 with cl/cp/bp only (tag 20261118b); second run with bd/bl/reg_new (tag 20261118c).
import json, os, shutil, hashlib, sys
from osgeo import ogr, osr, gdal
gdal.UseExceptions(); ogr.UseExceptions()
D=json.load(open(sys.argv[1])); LAY='/home/amedeo/Documents/Brenta_mesh_10/layers'; TAG=sys.argv[2]
sha=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
# layers touched by this payload
NAMES=[n for k,n in (('bl','breaklines_50m'),('bd','boundary_50m'),('reg_new','regioni_ponti_50m')) if D.get(k)]
if 'cl' in D: NAMES+=['centerline_50m','centerpoints_50m','bankpoints_50m']
# backups first (never overwrite an existing backup)
for n in NAMES:
    src=f'{LAY}/{n}.gpkg'; dst=f'{LAY}/{n}_backup_{TAG}.gpkg'
    if os.path.exists(dst): raise SystemExit('backup exists: '+dst)
    shutil.copyfile(src,dst); assert sha(src)==sha(dst); print('backup ok',dst)
# mls(c): MultiLineStringZM (z = m = 0) from a list of (x,y)
def mls(c):
    g=ogr.Geometry(ogr.wkbMultiLineStringZM); l=ogr.Geometry(ogr.wkbLineStringZM)
    for x,y in c: l.AddPointZM(x,y,0.0,0.0)
    g.AddGeometry(l); return g
# breaklines / boundary: replace the geometry of the listed fids (one transaction per file)
for key,n in (('bl','breaklines_50m'),('bd','boundary_50m')):
    if not D.get(key): continue
    ds=ogr.Open(f'{LAY}/{n}.gpkg',1); lyr=ds.GetLayer(0); ds.StartTransaction()
    for k,c in D[key].items():
        f=lyr.GetFeature(int(k)); f.SetGeometry(mls(c)); lyr.SetFeature(f)
    ds.CommitTransaction(); ds=None; print(n,'geometries replaced',len(D[key]))
# new region points (fid after the current maximum; buco only if not null)
if D.get('reg_new'):
    ds=ogr.Open(f'{LAY}/regioni_ponti_50m.gpkg',1); lyr=ds.GetLayer(0); defn=lyr.GetLayerDefn()
    fid0=max(f.GetFID() for f in lyr)+1; lyr.ResetReading(); ds.StartTransaction()
    for i,p in enumerate(D['reg_new']):
        f=ogr.Feature(defn); f.SetFID(fid0+i); f.SetField('nome',p['nome']); f.SetField('mat_id',p['mat_id']); f.SetField('max_area',p['max_area'])
        if p['buco'] is not None: f.SetField('buco',p['buco'])
        g=ogr.Geometry(ogr.wkbPoint); g.AddPoint_2D(p['x'],p['y']); f.SetGeometry(g); lyr.CreateFeature(f)
    ds.CommitTransaction(); ds=None; print('region points added',len(D['reg_new']),'fid from',fid0)
# rebuild centerline, centerpoints, bankpoints (same schema as write2.py)
if 'cl' in D:
    dt=gdal.Open(f'{LAY}/DTM_finale.tif'); gt=dt.GetGeoTransform(); band=dt.GetRasterBand(1); nz=0
    for b in D['bp']:
        if b['z_dtm'] is None:
            c=int((b['x']-gt[0])//gt[1]); r=int((gt[3]-b['y'])//(-gt[5])); b['z_dtm']=float(band.ReadAsArray(c,r,1,1)[0,0]); nz+=1
    print('DTM values read',nz)
    drv=ogr.GetDriverByName('GPKG'); srs=osr.SpatialReference(); srs.ImportFromEPSG(25832)
    for n in ('centerline_50m','centerpoints_50m','bankpoints_50m'): drv.DeleteDataSource(f'{LAY}/{n}.gpkg')
    ds=drv.CreateDataSource(f'{LAY}/centerline_50m.gpkg'); lyr=ds.CreateLayer('centerline_50m',srs,ogr.wkbLineString)
    for n,t in (('nome',ogr.OFTString),('ramo',ogr.OFTString),('lung_m',ogr.OFTReal),('s0_asta',ogr.OFTReal)): lyr.CreateField(ogr.FieldDefn(n,t))
    for c in D['cl']:
        f=ogr.Feature(lyr.GetLayerDefn()); l=ogr.Geometry(ogr.wkbLineString)
        for x,y in c['coords']: l.AddPoint_2D(x,y)
        f.SetField('nome',c['nome']); f.SetField('ramo',c['ramo']); f.SetField('lung_m',l.Length())
        if c['s0_asta'] is not None: f.SetField('s0_asta',c['s0_asta'])
        f.SetGeometry(l); lyr.CreateFeature(f)
    ds=None
    # pts(name, rows, fields): point layer, one feature per dict (fields set only when not None), one transaction
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
    pts('centerpoints_50m',D['cp'],[('nome',ogr.OFTString),('stream',ogr.OFTString),('s_m',ogr.OFTReal),('dist_next',ogr.OFTReal)])
    pts('bankpoints_50m',D['bp'],[('nome',ogr.OFTString),('sezione',ogr.OFTString),('s_m',ogr.OFTReal),('z_dtm',ogr.OFTReal),('dist_cp',ogr.OFTReal),('tipo',ogr.OFTString),('regola',ogr.OFTString),('prom',ogr.OFTReal)])
print('written')
