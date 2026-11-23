# write3.py - the single writer of the sections toolkit: applies a JSON payload to the derived layers
# Purpose : every script that prepares a change (sync_cp_bp, fix_manual, fix_bridges, the section builders) writes a payload;
#           this script is the only one that writes it into the derived GeoPackages, after a tagged backup of every layer touched
#           (<layer>_backup_<tag>.gpkg, verified by SHA-256; it refuses to run if a backup with that tag exists).
#           It also covers what the old write2.py did (replace all sections, drop/add region points, rebuild the three section layers).
# Payload : JSON, every key optional, LOGICAL field names (mapped with cfg.f):
#             "bl"       {fid: [[x,y],...]}   new geometry of breaklines (MultiLineStringZM, z = m = 0)
#             "bd"       {fid: [[x,y],...]}   new geometry of boundary features (name/id unchanged)
#             "secs"     [{"name","coords"}]  replace ALL section features of the boundary layer: features whose name matches
#                                             sections.name_pattern are deleted, the new ones are inserted in the given order with
#                                             fid = sections.first_fid + k and id = sections.first_id + k
#             "reg_drop" [fid,...]            region points to delete
#             "reg_new"  [{"x","y","name","mat_id","max_area","hole"}]   new region points (fid = previous maximum + 1, ...;
#                                             "hole" written only when not null)
#             "cl" [{"name","reach","coords","s0"}], "cp" [{"name","reach","s","x","y","dist_next"}],
#             "bp" [{"name","section","s","x","y","z","dist_cp","kind","rule","prom"}]
#                                             REBUILD centerline, centerpoints, bankpoints (all three together; z null = read the DTM cell)
# Inputs  : argv[1] payload json (path relative to the current folder), argv[2] backup tag; derived layers (cfg 'outputs'), DTM (cfg
#           inputs.dtm) when a bankpoint has z null; CRS from cfg project.crs; field names from cfg fields; sections from cfg sections.
# Outputs : the modified layers and their backups. Prints 'backup ok', what was written and 'written'.
# Safety  : refuses to run if a '-wal' file exists next to a layer it must write (the layer is probably open in QGIS) unless --force-open;
#           with --force-open the '-wal' file is copied next to the backup too. No rollback: restore from the backups of the tag.
# Run     : cd <working folder> ; /usr/bin/python3 <toolkit>/scripts/write3.py [-c rcs_config.json] [--force-open] payload.json <tag>
#           (system python: needs osgeo/OGR; WRITES INTO the derived layers)
import json, os, shutil, hashlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from osgeo import ogr, osr, gdal
gdal.UseExceptions(); ogr.UseExceptions()

ap = common.parser('apply a payload to the derived layers (backup first)')
ap.add_argument('payload'); ap.add_argument('tag')
ap.add_argument('--force-open', action='store_true', help='write even if a -wal file exists next to a layer (layer open in QGIS)')
args = ap.parse_args(); cfg = common.load(args)
D = json.load(open(args.payload)); TAG = args.tag
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
F = cfg.f
KNOWN = {'bl', 'bd', 'secs', 'reg_drop', 'reg_new', 'cl', 'cp', 'bp'}
if set(D) - KNOWN: raise SystemExit(f'unknown payload keys: {sorted(set(D) - KNOWN)}')
REBUILD = [k for k in ('cl', 'cp', 'bp') if k in D]
if REBUILD and len(REBUILD) != 3: raise SystemExit('cl, cp and bp must be given together (the three layers are rebuilt together)')

# layer keys touched by this payload, in a fixed order
KEYS = []
if D.get('bl'): KEYS.append('breaklines')
if D.get('bd') or 'secs' in D: KEYS.append('boundary')
if D.get('reg_drop') or D.get('reg_new'): KEYS.append('regions')
if REBUILD: KEYS += ['centerline', 'centerpoints', 'bankpoints']
if not KEYS: raise SystemExit('empty payload: nothing to write')
lp = lambda k: cfg.layer('out', k)

# ---- safety checks (nothing is written before all of them pass)
for k in KEYS:
    if os.path.exists(lp(k)) and os.path.exists(lp(k) + '-wal') and not args.force_open:
        raise SystemExit(f'{lp(k)}-wal exists: the layer is probably open in QGIS; close it or use --force-open')
    if k not in REBUILD and not os.path.exists(lp(k)): raise SystemExit('missing layer ' + lp(k))
    if os.path.exists(cfg.backup(k, TAG)): raise SystemExit('backup exists: ' + cfg.backup(k, TAG))
# backups (a rebuilt layer that does not exist yet needs none)
for k in KEYS:
    src, dst = lp(k), cfg.backup(k, TAG)
    if not os.path.exists(src): continue
    shutil.copyfile(src, dst); assert sha(src) == sha(dst); print('backup ok', dst)
    if os.path.exists(src + '-wal'): shutil.copyfile(src + '-wal', dst + '-wal'); print('  (-wal copied too)')

# mls(c): MultiLineStringZM (z = m = 0) from a list of (x,y), the geometry type of the line layers
def mls(c):
    g = ogr.Geometry(ogr.wkbMultiLineStringZM); l = ogr.Geometry(ogr.wkbLineStringZM)
    for x, y in c: l.AddPointZM(x, y, 0.0, 0.0)
    g.AddGeometry(l); return g

def set_opt(f, name, v):
    """Set a field only when the value is not None."""
    if v is not None: f.SetField(name, v)

# ---- breaklines / boundary: replace the geometry of the listed fids (one transaction per file)
for key, k in (('bl', 'breaklines'), ('bd', 'boundary')):
    if not D.get(key): continue
    ds = ogr.Open(lp(k), 1); lyr = ds.GetLayer(0); ds.StartTransaction()
    for fid, c in D[key].items():
        f = lyr.GetFeature(int(fid))
        if f is None: ds.RollbackTransaction(); raise SystemExit(f'{k}: fid {fid} not found')
        f.SetGeometry(mls(c)); lyr.SetFeature(f)
    ds.CommitTransaction(); ds = None; print(k, 'geometries replaced', len(D[key]))

# ---- boundary sections: delete every section feature, insert the new ones
if 'secs' in D:
    S = cfg['sections']; fid_id, fid_nm = F('boundary', 'id'), F('boundary', 'name')
    ds = ogr.Open(lp('boundary'), 1); lyr = ds.GetLayer(0); defn = lyr.GetLayerDefn(); ds.StartTransaction()
    old = [f.GetFID() for f in lyr if cfg.is_section(f.GetField(fid_nm))]
    keep = {f.GetFID() for f in lyr} - set(old); lyr.ResetReading()
    new_fids = [S['first_fid'] + i for i in range(len(D['secs']))]
    if keep & set(new_fids): ds.RollbackTransaction(); raise SystemExit(f'fid collision with non-section features: {sorted(keep & set(new_fids))[:5]}')
    for fid in old: lyr.DeleteFeature(fid)
    for i, s in enumerate(D['secs']):
        if not cfg.is_section(s['name']): ds.RollbackTransaction(); raise SystemExit('not a section name: ' + s['name'])
        f = ogr.Feature(defn); f.SetFID(new_fids[i]); f.SetField(fid_id, S['first_id'] + i); f.SetField(fid_nm, s['name'])
        f.SetGeometry(mls(s['coords'])); lyr.CreateFeature(f)
    ds.CommitTransaction(); ds = None; print('boundary: sections removed', len(old), 'added', len(D['secs']))

# ---- region points: drop, then add (fid after the maximum that existed before the drops)
if D.get('reg_drop') or D.get('reg_new'):
    ds = ogr.Open(lp('regions'), 1); lyr = ds.GetLayer(0); defn = lyr.GetLayerDefn()
    fid0 = max(f.GetFID() for f in lyr) + 1; lyr.ResetReading(); ds.StartTransaction()
    for fid in D.get('reg_drop', []):
        if lyr.GetFeature(int(fid)) is None: ds.RollbackTransaction(); raise SystemExit(f'regions: fid {fid} not found')
        lyr.DeleteFeature(int(fid))
    for i, p in enumerate(D.get('reg_new', [])):
        f = ogr.Feature(defn); f.SetFID(fid0 + i)
        for lg in ('name', 'mat_id', 'max_area'): f.SetField(F('regions', lg), p[lg])
        set_opt(f, F('regions', 'hole'), p.get('hole'))
        g = ogr.Geometry(ogr.wkbPoint); g.AddPoint_2D(p['x'], p['y']); f.SetGeometry(g); lyr.CreateFeature(f)
    ds.CommitTransaction(); ds = None
    print('region points dropped', len(D.get('reg_drop', [])), 'added', len(D.get('reg_new', [])), ('fid from %d' % fid0) if D.get('reg_new') else '')

# ---- rebuild centerline, centerpoints, bankpoints
if REBUILD:
    dt = gdal.Open(cfg.dtm()); gt = dt.GetGeoTransform(); band = dt.GetRasterBand(1); nz = 0; nodata = cfg.get('dtm', {}).get('nodata')
    for b in D['bp']:
        if b.get('z') is None:
            c = int((b['x'] - gt[0]) // gt[1]); r = int((gt[3] - b['y']) // (-gt[5]))
            b['z'] = float(band.ReadAsArray(c, r, 1, 1)[0, 0]); nz += 1
            if nodata is not None and b['z'] == nodata: print('**CHECK** DTM nodata under bankpoint', b['name'])
    print('DTM values read', nz)
    drv = ogr.GetDriverByName('GPKG'); srs = osr.SpatialReference(); srs.ImportFromEPSG(int(cfg['project']['crs']))
    for k in ('centerline', 'centerpoints', 'bankpoints'):
        if os.path.exists(lp(k)): drv.DeleteDataSource(lp(k))
    # centerline: LineString, fields name, reach, length (of the geometry), s0 (only when not null)
    ds = drv.CreateDataSource(lp('centerline')); lyr = ds.CreateLayer(cfg.layer_name('out', 'centerline'), srs, ogr.wkbLineString)
    for lg, t in (('name', ogr.OFTString), ('reach', ogr.OFTString), ('length', ogr.OFTReal), ('s0', ogr.OFTReal)):
        lyr.CreateField(ogr.FieldDefn(F('centerline', lg), t))
    for c in D['cl']:
        f = ogr.Feature(lyr.GetLayerDefn()); l = ogr.Geometry(ogr.wkbLineString)
        for x, y in c['coords']: l.AddPoint_2D(x, y)
        f.SetField(F('centerline', 'name'), c['name']); f.SetField(F('centerline', 'reach'), c['reach'])
        f.SetField(F('centerline', 'length'), l.Length()); set_opt(f, F('centerline', 's0'), c.get('s0'))
        f.SetGeometry(l); lyr.CreateFeature(f)
    ds = None
    # pts(key, rows, fields): point layer, one feature per dict (fields set only when not null), one transaction
    def pts(key, rows, layer, fields):
        ds = drv.CreateDataSource(lp(key)); lyr = ds.CreateLayer(cfg.layer_name('out', key), srs, ogr.wkbPoint)
        for lg, t in fields: lyr.CreateField(ogr.FieldDefn(F(layer, lg), t))
        ds.StartTransaction()
        for r in rows:
            f = ogr.Feature(lyr.GetLayerDefn())
            for lg, _ in fields: set_opt(f, F(layer, lg), r.get(lg))
            g = ogr.Geometry(ogr.wkbPoint); g.AddPoint_2D(r['x'], r['y']); f.SetGeometry(g); lyr.CreateFeature(f)
        ds.CommitTransaction(); ds = None
    S_, R_ = ogr.OFTString, ogr.OFTReal
    pts('centerpoints', D['cp'], 'centerpoints', [('name', S_), ('reach', S_), ('s', R_), ('dist_next', R_)])
    pts('bankpoints', D['bp'], 'bankpoints', [('name', S_), ('section', S_), ('s', R_), ('z', R_), ('dist_cp', R_), ('kind', S_), ('rule', S_), ('prom', R_)])
    print('rebuilt: centerline', len(D['cl']), 'centerpoints', len(D['cp']), 'bankpoints', len(D['bp']))
print('written')
