# locked_lines.py - list the breaklines that bound the wall faces (regions with a locked mat_id): they must never be modified
# Purpose: faces of the planar graph made of the breaklines and the NON-section boundary lines (nodestrings) that contain a region point
#          whose material is in cfg locked.mat_ids are the 'wall' faces. Every breakline that shares more than params.min_shared metres
#          with the boundary of these faces (within params.buffer) is locked. The other scripts read the list with cfg.locked_lines().
# Inputs : breaklines, boundary, regions layers: by default the ORIGINAL ones (cfg 'inputs'); with --derived the derived ones
#          (cfg 'outputs'; sections are then skipped with sections.name_pattern); cfg locked.mat_ids, locked.lines_file,
#          fields.regions.mat_id, params.locked_lines {buffer, min_shared}.
# Output : work/<cfg locked.lines_file>  (JSON: sorted list of breakline fids); prints the number of wall faces and of locked lines.
# Run    : cd <working folder> ; ~/anaconda3/bin/python3 <toolkit>/scripts/locked_lines.py [-c rcs_config.json] [--derived]
import sys, os, json, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union
ap = common.parser('write the fids of the locked (wall) breaklines')
ap.add_argument('--derived', action='store_true', help='read the derived layers instead of the originals')
args = ap.parse_args(); cfg = common.load(args)
P = cfg['params']['locked_lines']; which = 'out' if args.derived else 'in'
rd = lambda k: gpd.read_file(cfg.layer(which, k), fid_as_index=True)
bl, bd, rg = rd('breaklines'), rd('boundary'), rd('regions')
bn, mid = cfg.f('boundary', 'name'), cfg.f('regions', 'mat_id')
# O = breaklines, NS = nodestrings that are not sections (sections are not obstacles)
O = {int(f): shapely.get_coordinates(g) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
NS = [LineString(shapely.get_coordinates(g)) for n, g in zip(bd[bn], bd.geometry) if not cfg.is_section(n)]
fc = list(polygonize(unary_union([LineString(c) for c in O.values()] + NS)))
T = shapely.STRtree(fc)
walls = {int(T.query(p, predicate='within')[0]) for p in rg[rg[mid].isin(cfg['locked']['mat_ids'])].geometry}
B = shapely.union_all([fc[i].boundary for i in walls]).buffer(P['buffer'])
lock = sorted(f for f, c in O.items() if LineString(c).intersection(B).length > P['min_shared'])
json.dump(lock, open(cfg.work(cfg['locked']['lines_file']), 'w'))
print('wall faces', len(walls), 'locked breaklines', len(lock), lock)
