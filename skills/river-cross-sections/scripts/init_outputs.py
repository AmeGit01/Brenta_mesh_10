# init_outputs.py - create the derived layers as exact copies of the original layers and record the SHA-256 of the originals
# Purpose: the toolkit never edits the original breaklines/boundary/regions layers. This script makes the working copies that the
#          other scripts edit (cfg 'inputs' -> 'outputs': breaklines, boundary, regions) and writes the SHA-256 of the originals
#          to work/sha_originals.txt, so that later checks can confirm that the originals never changed (--check).
# Inputs : cfg inputs (breaklines, boundary, regions; dtm only with --dtm), cfg outputs, cfg paths.
# Outputs: the three derived GeoPackages (layers/<output>.gpkg); work/sha_originals.txt (lines '<sha256>  <path relative to the
#          working folder>', in the format of sha256sum). Prints OK / **CHECK** for each copy.
# Safety : refuses if a target exists (or has a -wal file); refuses if an original has a -wal file (open in QGIS) unless --force-open,
#          in which case the copy is made with the SQLite backup API (includes the -wal content) and compared by feature count.
# Run    : cd <working folder> ; python3 <toolkit>/scripts/init_outputs.py [-c rcs_config.json] [--dtm] [--force-open]
#          later:   python3 <toolkit>/scripts/init_outputs.py --check      (recompute the hashes and compare with the file)
#          (plain python: standard library only)
import sys, os, shutil, hashlib, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = common.parser('create derived layers as exact copies of the originals and record the SHA-256 of the originals')
ap.add_argument('--dtm', action='store_true', help='include the DTM in the hash list (large file)')
ap.add_argument('--check', action='store_true', help='only recompute the SHA-256 of the originals and compare with work/sha_originals.txt')
ap.add_argument('--force-open', action='store_true', help='allow originals that have a -wal file')
args = ap.parse_args(); cfg = common.load(args)
KEYS = ('breaklines', 'boundary', 'regions')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
rel = lambda p: os.path.relpath(p, cfg.wd)
SHAF = cfg.work('sha_originals.txt')
orig = [cfg.layer('in', k) for k in KEYS] + ([cfg.dtm()] if args.dtm else [])
missing = [p for p in orig if not os.path.exists(p)]
if missing: raise SystemExit('missing originals: ' + ', '.join(rel(p) for p in missing))

if args.check:
    # compare the current hashes with the recorded ones
    rec = dict(l.strip().split('  ', 1)[::-1] for l in open(SHAF) if l.strip())
    bad = 0
    for p in rec:
        now = sha(os.path.join(cfg.wd, p)); ok = now == rec[p]; bad += not ok
        print(('OK        ' if ok else '**CHECK** ') + p)
    print('OK: originals unchanged' if not bad else '**CHECK** originals changed: %d' % bad); sys.exit(1 if bad else 0)

# refuse before writing anything
for k in KEYS:
    t = cfg.layer('out', k)
    if os.path.exists(t) or os.path.exists(t + '-wal'): raise SystemExit('target exists: ' + rel(t))
for p in orig[:len(KEYS)]:
    if os.path.exists(p + '-wal') and not args.force_open: raise SystemExit(f'{rel(p)}-wal exists: the original is open in QGIS; close it or use --force-open')

def count(p):
    """Feature counts of every feature table of a GeoPackage (read-only connection)."""
    c = sqlite3.connect('file:' + p + '?mode=ro', uri=True)
    try:
        tabs = [t for (t,) in c.execute("SELECT table_name FROM gpkg_contents WHERE data_type='features' ORDER BY table_name")]
        return [c.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tabs]
    finally: c.close()

with open(SHAF, 'w') as fh:
    for p in orig: fh.write(f'{sha(p)}  {rel(p)}\n')
print('SHA-256 of the originals written to', rel(SHAF))
for k in KEYS:
    src, dst = cfg.layer('in', k), cfg.layer('out', k)
    if os.path.exists(src + '-wal'):
        a = sqlite3.connect('file:' + src + '?mode=ro', uri=True); b = sqlite3.connect(dst); a.backup(b); b.close(); a.close()
        ok = count(src) == count(dst); how = 'SQLite backup (-wal included), feature counts equal'
    else:
        shutil.copyfile(src, dst); ok = sha(src) == sha(dst); how = 'byte-identical copy (SHA-256 equal)'
    print(('OK  ' if ok else '**CHECK** ') + f'{rel(dst)} <- {rel(src)}: {how}')
