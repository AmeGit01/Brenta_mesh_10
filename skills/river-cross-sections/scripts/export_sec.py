# export_sec.py - section data of the chosen stations (input of next_bed.py, obst.py, bank.py)
# Purpose: turn the stations chosen by dp.py into a flat JSON list, one record per section, in reach order.
# Inputs : work/cands.pkl (place.py), work/dp.pkl (dp.py); config reaches[*].code and sections {digits}. Optional argument
#          --reach CODE [CODE ...] exports only those reaches.
# Outputs: work/sec_in.json = list of dicts: stream and tag (reach code), name (section name), s (m along the centerline of the reach source),
#          x, y (centre point), nx, ny (unit normal towards the LEFT end; the section runs from left to right looking downstream),
#          tL, tR (centre -> toe, left/right), cL, cR (centre -> top of bank). The record of an anchored section keeps the fields of its
#          placeholder candidate and carries the key 'anchor' (nodestring data: k, section, nodestring, s, x, y, nx, ny, tL, tR, coords),
#          so that assemble.py uses the nodestring itself as the section. Prints the number of sections per reach.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/export_sec.py [-c rcs_config.json] [--reach N V B]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json, pickle

ap = common.parser('section data of the chosen stations')
ap.add_argument('--reach', nargs='+', help='reach codes to export (default: all, in config order)')
args = ap.parse_args()
cfg = common.load(args)
with open(cfg.work('cands.pkl'), 'rb') as f: C = pickle.load(f)
with open(cfg.work('dp.pkl'), 'rb') as f: D = pickle.load(f)
codes = [r['code'] for r in cfg.reaches() if not args.reach or r['code'] in args.reach]
out = []; cnt = {}
for code in codes:
    d = D[code]; c = C[d['source']]; A = {a['k']: a for a in d['anchors']}
    for k, j in enumerate(d['idx']):
        r = dict(stream=code, tag=code, name=d['names'][k], s=float(c['ss'][j]), x=float(c['P'][j, 0]), y=float(c['P'][j, 1]),
                 nx=float(c['n'][j, 0]), ny=float(c['n'][j, 1]), tL=float(c['tL'][j]), tR=float(c['tR'][j]), cL=float(c['cL'][j]), cR=float(c['cR'][j]))
        if k in A: r['anchor'] = A[k]
        out.append(r)
    cnt[code] = len(d['idx'])
with open(cfg.work('sec_in.json'), 'w') as f: json.dump(out, f)
print('sections', len(out), cnt)
