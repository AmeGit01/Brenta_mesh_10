# next_bed.py - cap the bankpoint search before another bed
# Purpose: for each section, if a DIFFERENT bed polygon (another channel, e.g. an old river branch) lies just beyond the bank on one
#          side, cap the bankpoint search distance (keys maxL / maxR of sec_in.json) so that the search stops a margin before that bed edge.
# Inputs : work/graph.pkl (graph.py: faces and region names; the face class 'bed' comes from cfg.face_class), work/sec_in.json
#          (section data: x, y, nx, ny, tL, tR, cL, cR, stream, s). Parameters: cfg['params']['next_bed'].
# Output : work/sec_in.json is OVERWRITTEN in place, adding maxL/maxR where a cap applies; prints each cap and the total count.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/next_bed.py [-c rcs_config.json]   (idempotent: a cap is only lowered)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import json, numpy as np

cfg = common.load(common.parser('cap the bankpoint search before the bed of another channel').parse_args())
P = cfg['params']['next_bed']
RAY = P['ray_range']          # ray length each side of the centre point (m)
MARGIN = P['margin_before_edge']   # the search stops this far before the other bed (m)
SKIP = P['own_toe_skip']      # hits closer than toe + SKIP belong to the own bed edge (m)
WIN = P['search_past_toe']    # bank.py searches at most this far past the toe (m)
EXTRA = P['window_margin']    # plus this margin: only a bed edge inside the window matters (m)
fc, rows = geom.load_graph(cfg)
# tb: outline segments (x0,y0,x1,y1) of the union of all faces of class 'bed'; Rb answers ray-vs-segment first-hit queries.
tb = geom.boundary_segs(fc, rows, lambda n: cfg.face_class(n) == 'bed'); Rb = geom.Rays(tb)
S = json.load(open(cfg.work('sec_in.json'))); n = 0
# For each section: ray from the centerpoint o along the normal d (both directions); h = signed distances of all hits with bed edges.
for s in S:
    o = np.array([s['x'], s['y']]); d = np.array([s['nx'], s['ny']]); h = Rb.hits(o, d, RAY)
    # sg=+1 left side (key maxL, toe distance tL), sg=-1 right side (key maxR, toe tR); v = ascending distances of hits on this side
    # lying beyond the own toe (+ SKIP, to skip the section's own bed edge).
    for sg, k, tk in ((1, 'maxL', 'tL'), (-1, 'maxR', 'tR')):
        v = np.sort(h[h * sg > 0] * sg); v = v[v > s[tk] + SKIP]
        # Only a bed edge inside the search window past the toe matters.
        if len(v) and v[0] - MARGIN < s[tk] + WIN + EXTRA:
            # lim = maximum distance from the centerpoint allowed for the bankpoint: MARGIN before the other bed.
            lim = float(v[0] - MARGIN)
            if lim < s.get(k, 1e9): s[k] = lim; n += 1; print(' next-bed cap', s['stream'][0], round(s['s']), k, round(lim, 2), 'toe', round(s[tk], 2))
json.dump(S, open(cfg.work('sec_in.json'), 'w')); print('caps', n)
