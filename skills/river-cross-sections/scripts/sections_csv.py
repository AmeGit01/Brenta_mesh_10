# sections_csv.py - write the summary table of the sections (one row per section) from the derived layers read back from disk.
# Purpose: columns: section, reach, s_m (chainage within the reach, from centerpoints), for each side z, dist_cp, kind, rule, prom (from
#          bankpoints), and the length of the section line (from boundary). Rows follow the order of the boundary layer.
# Inputs : config keys: outputs.boundary / centerpoints / bankpoints (GeoPackages in paths.layers), outputs.sections_csv (CSV path relative
#          to the working folder), fields.*, bankpoint_values (left, right), sections.name_pattern, params.sections_csv.header (the 14 column
#          titles). Optional: --suffix S inserted before .gpkg to read tagged backups (e.g. _backup_20261118); --out PATH overrides the CSV path.
# Outputs: the CSV (OVERWRITTEN); prints the number of rows.
# Run    : cd <working folder>; ~/anaconda3/bin/python3 <toolkit>/scripts/sections_csv.py [-c rcs_config.json] [--suffix S] [--out PATH]
# Rounding: s_m 2 decimals, z 3, dist_cp 2, prom 3, length 2; empty field for null values.
# Origin : Brenta project, sections_csv.py, 2026-11-18.
import sys, os, csv, geopandas as gpd, shapely, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
warnings.filterwarnings('ignore')
ap = common.parser('write the sections summary CSV')
ap.add_argument('--suffix', default='', help='suffix inserted before .gpkg to read backups')
ap.add_argument('--out', default=None, help='CSV path relative to the working folder (default outputs.sections_csv)')
args = ap.parse_args(); cfg = common.load(args)
outf = cfg.path(args.out or cfg['outputs']['sections_csv'])
def rd(key):
    p = cfg.layer('out', key)
    return gpd.read_file(p[:-len('.gpkg')] + args.suffix + '.gpkg')
fb, fc, fp = cfg['fields']['boundary'], cfg['fields']['centerpoints'], cfg['fields']['bankpoints']
b = rd('boundary'); cp = rd('centerpoints'); bp = rd('bankpoints')
BV = cfg['bankpoint_values']
# sections = boundary features whose name matches the section pattern; s = chainage per section; side = bankpoint row per name
sec = b[[cfg.is_section(n) for n in b[fb['name']]]]; s = dict(zip(cp[fc['name']], cp[fc['s']])); side = {r[fp['name']]: r for _, r in bp.iterrows()}
# f(x, n): rounded number or empty string for null/NaN
def f(x, n): return '' if x is None or x != x else round(float(x), n)
rows = []
for nm, g in zip(sec[fb['name']], sec.geometry):
    r = [nm, cfg.reach_of(nm), f(s[nm], 2)]
    for t in (BV['left'], BV['right']):
        q = side[f'{nm}_{t}']; r += [f(q[fp['z']], 3), f(q[fp['dist_cp']], 2), q[fp['kind']], q[fp['rule']], f(q[fp['prom']], 3)]
    r.append(f(shapely.length(g), 2)); rows.append(r)
os.makedirs(os.path.dirname(outf), exist_ok=True)
with open(outf, 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(cfg['params']['sections_csv']['header']); w.writerows(rows)
print('rows', len(rows), '->', os.path.relpath(outf, cfg.wd))
