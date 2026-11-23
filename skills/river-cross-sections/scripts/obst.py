# obst.py - cap the bankpoint search before the first obstacle beyond the toe
# Purpose: cap the bankpoint search (keys maxL/maxR of sec_in.json) a margin before the first obstacle beyond the toe. Obstacles:
#          non-section nodestrings (bridges etc., from the ORIGINAL boundary layer), inner breaklines (segments that are neither toe nor
#          top-of-bank) and the toe of another bed. An obstacle counts if it lies in (toe - margin, top-of-bank) (or beyond the own toe
#          for another bed).
# Inputs : work/graph.pkl (graph.py; face classes via cfg.face_class), work/sec_in.json, cfg layer ('in','boundary') (non-section
#          nodestrings are the features whose name is not a section name, cfg.is_section). Parameters: cfg['params']['obst'].
# Output : work/sec_in.json OVERWRITTEN with maxL/maxR lowered where a cap applies (a cap is only lowered); prints each cap and the count.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/obst.py [-c rcs_config.json]     (idempotent)
# Units  : metres along the section normal from the centre point.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import json, numpy as np, shapely

cfg = common.load(common.parser('cap the bankpoint search before the first obstacle').parse_args())
P = cfg['params']['obst']
RAY = P['ray_range']; MARGIN = P['margin_before_edge']; SKIP = P['own_toe_skip']; TOPTOL = P['top_tolerance']
# fc/rows: faces of the planar graph and their region names; tb = bed boundary segments (toe lines); tc = bed/bank/wall boundary segments
fc, rows = geom.load_graph(cfg)
tb = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) == 'bed'); tc = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) in ('bed', 'bank', 'wall'))
# skip = segment keys that are toe or top-of-bank lines: they are not 'inner' obstacles
skip = {geom.key(s) for s in tb} | {geom.key(s) for s in tc}
# inner = unique ring segments of all faces that are not toe/top-of-bank (inner breaklines)
allseg = []
for f in fc:
    for s in geom.ring_segs(f):
        if geom.key(s) not in skip: allseg.append(s)
seen = set(); inner = []
for s in allseg:
    k = geom.key(s)
    if k not in seen: seen.add(k); inner.append(s)
# bd = boundary layer; ns = coordinates of the nodestrings that are NOT sections; nseg = their segments, shape (n,4)
bd = geom.read(cfg.layer('in', 'boundary'))
ns = [shapely.get_coordinates(g) for n, g in zip(bd[cfg.f('boundary', 'name')], bd.geometry) if not cfg.is_section(n)]
nseg = np.vstack([np.c_[c[:-1], c[1:]] for c in ns])
# R = ray caster against inner breaklines + nodestrings; RB = against toe lines only (to stop before another bed)
R = geom.Rays(np.vstack([np.array(inner), nseg])); RB = geom.Rays(tb)
# S = sections of sec_in.json; n = number of caps applied
S = json.load(open(cfg.work('sec_in.json'))); n = 0
for s in S:
    # o = origin (centre point), d = unit normal (positive = left); h/hb = signed ray hit distances
    o = np.array([s['x'], s['y']]); d = np.array([s['nx'], s['ny']]); h = R.hits(o, d, RAY); hb = RB.hits(o, d, RAY)
    # for each side: sg sign, k = cap key, tk/ck = toe/top-of-bank key
    for sg, k, tk, ck in ((1, 'maxL', 'tL', 'cL'), (-1, 'maxR', 'tR', 'cR')):
        # v = obstacle distances on this side between (toe - margin) and the top of bank
        v = np.sort(h[h * sg > 0] * sg); v = v[(v > s[tk] - MARGIN) & (v < s[ck] - TOPTOL)]
        # vb = toes of other beds more than SKIP beyond the own toe
        vb = np.sort(hb[hb * sg > 0] * sg); vb = vb[vb > s[tk] + SKIP]
        # merge: the nearest obstacle sets the cap
        v = np.sort(np.r_[v, vb])
        if len(v):
            # cap = margin before the first obstacle; only if it lowers the current cap
            lim = float(v[0] - MARGIN)
            if lim < s.get(k, 1e9): s[k] = lim; n += 1; print(' obstacle cap', s['stream'][0], round(s['s']), k, round(lim, 2), 'toe', round(s[tk], 2))
# write back
json.dump(S, open(cfg.work('sec_in.json'), 'w')); print('obstacle caps', n)
