# xn_points.py - meeting points of nodestrings and breaklines (used by place.py / dp.py as obstacles for the toe crossings)
# Purpose: list every point where a nodestring that is not a section meets a breakline (a crossing, or the ends of an overlapping part).
#          place.py penalises the candidate sections whose toe crossing lies closer than rules.near_node.radius to one of them
#          (weight params.placement.weights.xn).
# Inputs : cfg layers boundary and breaklines of group 'in' (default; the widened geometry is used if work/widen2.pkl and work/bgn.pkl
#          exist) or of group 'out' (--layers out: the derived layers, which already hold the widening); fields.boundary.name,
#          sections.name_pattern (features whose name matches are sections and are skipped).
# Outputs: work/xn_points.json = list of [x, y]; prints the number of points.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/xn_points.py [-c rcs_config.json] [--layers in|out]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json, pickle, numpy as np, geopandas as gpd, shapely, warnings
from shapely.geometry import LineString
warnings.filterwarnings('ignore')

ap = common.parser('meeting points of nodestrings and breaklines')
ap.add_argument('--layers', choices=['in', 'out'], default='in', help="layer group: 'in' original (+ widening if present), 'out' derived layers")
args = ap.parse_args()
cfg = common.load(args)
bl = gpd.read_file(cfg.layer(args.layers, 'breaklines'), fid_as_index=True); bd = gpd.read_file(cfg.layer(args.layers, 'boundary'), fid_as_index=True)
bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
newf, bgn = {}, {}
if args.layers == 'in' and os.path.exists(cfg.work('widen2.pkl')) and os.path.exists(cfg.work('bgn.pkl')):
    with open(cfg.work('widen2.pkl'), 'rb') as f: newf = pickle.load(f)['newf']
    with open(cfg.work('bgn.pkl'), 'rb') as f: bgn = pickle.load(f)
    print('widened geometry: breaklines', len(newf), 'boundaries', len(bgn))
# U = union of all breaklines (widened where moved)
U = shapely.union_all([LineString(newf[f]) if f in newf else g for f, g in bl.geometry.items()])
pts = []
for k, n, g in zip(bd.index, bd[cfg.f('boundary', 'name')], bd.geometry):
    if cfg.is_section(n): continue                    # sections are not obstacles
    l = LineString(bgn[k]) if k in bgn else LineString(shapely.get_coordinates(g))
    pts += shapely.get_coordinates(l.intersection(U)).tolist()
with open(cfg.work('xn_points.json'), 'w') as f: json.dump(pts, f)
print('xn points', len(pts))
