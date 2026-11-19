# drop_regions.py  (2026-11-19)
# Purpose: delete given features (by fid) from layers/regioni_ponti_50m.gpkg, after a dated backup verified byte by byte.
#          Used on 2026-11-19 to remove the rows without geometry (fid 65, 135) and the second point of the face 57/58 (fid 58).
# Inputs : argv[1] = GeoPackage to edit; argv[2] = backup path to create (must not exist); argv[3:] = fids to delete.
# Output : the edited GeoPackage (same layer, fields, geometry type, CRS, spatial index; the other features untouched).
# Run    : /usr/bin/python3 scripts/drop_regions.py layers/regioni_ponti_50m.gpkg layers/regioni_ponti_50m_backup_20261119.gpkg 58 65 135
#          (system python3, GDAL/OGR). The layer must be closed in QGIS.
import sys, os, shutil, filecmp
from osgeo import ogr
ogr.UseExceptions()
src, bak, fids = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
if os.path.exists(bak): sys.exit(f'exists: {bak}')
shutil.copy2(src, bak)
if not filecmp.cmp(src, bak, shallow=False): sys.exit('backup differs from source')
print(f'backup {bak}: identical to {src}')
ds = ogr.Open(src, 1); lyr = ds.GetLayer(0)
missing = [f for f in fids if lyr.GetFeature(f) is None]
if missing: sys.exit(f'fids not found: {missing}')
ds.StartTransaction()
for f in fids:
    ft = lyr.GetFeature(f); g = ft.GetGeometryRef()
    print(f'delete fid {f}: nome={ft.GetField("nome")} mat_id={ft.GetField("mat_id")} max_area={ft.GetField("max_area")} geometry={"null" if g is None else g.ExportToWkt()}')
    lyr.DeleteFeature(f)
ds.CommitTransaction()
lyr.SyncToDisk(); ds = None
print('done')
