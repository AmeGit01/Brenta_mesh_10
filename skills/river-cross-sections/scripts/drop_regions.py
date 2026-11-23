# drop_regions.py - delete given region points (by fid) from the derived regions layer, after a verified backup
# Purpose: delete features (by fid) from the derived regions layer, after a tagged backup verified byte by byte. All other features,
#          the fields, geometry type, CRS and spatial index stay as they are. (write3.py can do the same with the payload key
#          "reg_drop" together with other changes; this script is the stand-alone form with a printed record of what is deleted.)
# Inputs : cfg outputs.regions (the derived layer, edited), cfg paths; argv: backup tag, then the fids to delete.
# Output : the edited layer; the backup layers/<regions output>_backup_<tag>.gpkg (must not exist). Prints, for every deleted fid,
#          name, mat_id, max_area and geometry.
# Safety : refuses if the backup exists, if a fid does not exist (nothing is modified), or if a '-wal' file exists next to the layer
#          (layer open in QGIS) unless --force-open.
# Run    : cd <working folder> ; /usr/bin/python3 <toolkit>/scripts/drop_regions.py [-c rcs_config.json] [--force-open] <tag> <fid> [<fid> ...]
#          (system python: needs osgeo/OGR; WRITES INTO the layer)
import sys, os, shutil, filecmp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from osgeo import ogr
ogr.UseExceptions()
ap = common.parser('delete region points by fid (backup first)')
ap.add_argument('tag'); ap.add_argument('fids', nargs='+', type=int)
ap.add_argument('--force-open', action='store_true', help='write even if a -wal file exists next to the layer')
args = ap.parse_args(); cfg = common.load(args)
src, bak, fids = cfg.layer('out', 'regions'), cfg.backup('regions', args.tag), args.fids
if not os.path.exists(src): sys.exit(f'missing layer {src}')
if os.path.exists(src + '-wal') and not args.force_open: sys.exit(f'{src}-wal exists: the layer is probably open in QGIS; close it or use --force-open')
if os.path.exists(bak): sys.exit(f'exists: {bak}')
shutil.copy2(src, bak)
if not filecmp.cmp(src, bak, shallow=False): sys.exit('backup differs from source')
if os.path.exists(src + '-wal'): shutil.copy2(src + '-wal', bak + '-wal')
print(f'backup {bak}: identical to {src}')
ds = ogr.Open(src, 1); lyr = ds.GetLayer(0)
fn, fm, fa = (cfg.f('regions', k) for k in ('name', 'mat_id', 'max_area'))
missing = [f for f in fids if lyr.GetFeature(f) is None]
if missing: sys.exit(f'fids not found: {missing}')
ds.StartTransaction()
for f in fids:
    ft = lyr.GetFeature(f); g = ft.GetGeometryRef()
    print(f'delete fid {f}: {fn}={ft.GetField(fn)} {fm}={ft.GetField(fm)} {fa}={ft.GetField(fa)} geometry={"null" if g is None else g.ExportToWkt()}')
    lyr.DeleteFeature(f)
ds.CommitTransaction()
lyr.SyncToDisk(); ds = None
print('done')
