# prep_write.py - collect everything to write into one payload for write3.py
# Purpose: collect into a JSON payload (format of write3.py, logical keys) everything the derived layers need after the near-node rule and the
#          region-point choice: changed breaklines (bl), the new section set (secs), the centerlines of the reaches (cl), centerpoints (cp),
#          bankpoints (bp) and region-point changes (reg_drop, reg_new). Bankpoints moved by hand (moved > 1e-6 m) get kind and rule
#          cfg['bankpoint_values']['manual'] with z null (write3.py reads the DTM cell). Nothing is written to the layers here.
# Inputs : argument = near-nodes JSON (default work/near_nodes.json); cfg layer ('out','breaklines') (current breaklines); work/secs_new.json
#          (assemble.py: reach, nome, s, s_asta, cx, cy, coords, sides); work/regions2.json (regions2.py); the source centerlines of
#          cfg['params']['prep_write']['centerline_sources'] (file, line name, cut rule per reach); reach codes and centerline names
#          from cfg['reaches'].
# Output : work/write_payload.json (or -o) = dict(bl, secs, cl, cp, bp, reg_drop, reg_new); prints the counts and the length of the centerlines.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/prep_write.py [-c rcs_config.json] [near_nodes.json] [-o payload.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import json, numpy as np, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
from shapely.ops import substring

ap = common.parser('collect the write3.py payload')
ap.add_argument('fix', nargs='?', help='fixed breaklines JSON (key F); default work/near_nodes.json')
ap.add_argument('-o', '--out', help='payload file (default work/write_payload.json)')
args = ap.parse_args()
cfg = common.load(args)
P = cfg['params']['prep_write']
MOVED = P['manual_threshold']        # a bankpoint farther than this from the section vertex was moved by hand (m)
CHG = P['changed_threshold']         # a breakline is changed if a coordinate differs by more than this (m)
MAN = cfg['bankpoint_values']['manual']
# F = new breaklines (near_nodes.json)
F = {int(k): v for k, v in json.load(open(args.fix or cfg.work('near_nodes.json')))['F'].items()}
bl = geom.read(cfg.layer('out', 'breaklines'))
# O = current breaklines (arrays); blchg = breaklines whose coordinates changed
O = {int(f): shapely.get_coordinates(g) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
blchg = {f: c for f, c in F.items() if len(c) != len(O[f]) or np.abs(np.array(c) - O[f]).max() > CHG}
# secs = new sections, R = region decisions
secs = json.load(open(cfg.work('secs_new.json'))); R = json.load(open(cfg.work('regions2.json')))
# lines = centerlines of the reaches, cut from the configured source lines
fN = cfg.f('centerline', 'name'); cache = {}
def source(file, name):
    """source centerline `name` (field cfg.f('centerline','name')) of the layer `file`"""
    if file not in cache: cache[file] = geom.read(cfg.path(file), False)
    g = cache[file]; return g[g[fN] == name].geometry.iloc[0]
lines = []
for rc in cfg.reaches():
    code = rc['code']; src = P['centerline_sources'][code]; RS = [s for s in secs if s['reach'] == code]
    A = source(src['file'], src['line'])
    # start chainage on the source line and end chainage
    a = 0.0 if src['start'] == 'zero' else RS[0]['s_asta']
    z = RS[-1]['s'] if src['end'] == 'last_section_s' else A.length
    lines.append(dict(name=rc['centerline'], reach=code, coords=shapely.get_coordinates(substring(A, a, z)).tolist(), s0=a if src['s0_from_start'] else None))
# cp = centerpoints, bp = bankpoints, sx = sections
cp = []; bp = []; sx = []
# centerpoints per reach: dist_next = distance along s to the next section (None for the last)
for rc in cfg.reaches():
    R_ = [s for s in secs if s['reach'] == rc['code']]
    for i, s in enumerate(R_):
        cp.append(dict(name=s['nome'], reach=rc['code'], s=s['s'], x=s['cx'], y=s['cy'], dist_next=(R_[i + 1]['s'] - s['s']) if i + 1 < len(R_) else None))
# bankpoints named <section>_<tag> (tag = side suffix of the bankpoint names)
for s in secs:
    sx.append(dict(name=s['nome'], coords=s['coords']))
    for sd in s['sides']:
        # man = bankpoint moved by hand
        man = sd['moved'] > MOVED
        bp.append(dict(name=f"{s['nome']}_{sd['tag']}", section=s['nome'], s=s['s'], x=sd['x'], y=sd['y'], z=None if man else sd['z'],
                       dist_cp=float(np.hypot(sd['x'] - s['cx'], sd['y'] - s['cy'])), kind=MAN if man else sd['tipo'], rule=MAN if man else sd['regola'], prom=None if man else sd['prom']))
# region points: the new ones get their fid from write3.py (current maximum + 1, in this order)
reg_new = [dict(x=p['x'], y=p['y'], name=p['name'], mat_id=p['mat_id'], max_area=p['max_area'], hole=p['hole']) for p in R['new']]
# save
out = args.out or cfg.work('write_payload.json')
json.dump(dict(bl={str(f): c for f, c in blchg.items()}, secs=sx, cl=lines, cp=cp, bp=bp, reg_drop=R['drop'], reg_new=reg_new), open(out, 'w'))
# reports
print('breaklines changed', len(blchg), 'sections', len(sx), 'cp', len(cp), 'bp', len(bp), 'reg drop', len(R['drop']), 'new', len(reg_new), 'manual bp', sum(b['kind'] == MAN for b in bp))
print('centerlines', [(l['name'], round(LineString(l['coords']).length, 1)) for l in lines])
