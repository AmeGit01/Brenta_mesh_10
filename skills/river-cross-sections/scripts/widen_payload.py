# widen_payload.py - turn the result of the bank widening (apply_widen.py) into a write3.py payload.
# Purpose: the widened breaklines (work/widen2.pkl, key newf) and the extended nodestrings (work/bgn.pkl) must be written into the derived
#          layers before the sections are placed on them by the near-node step. This script only converts: it checks that every fid exists
#          in the derived layers, that no locked line is touched, and prints the counts. Nothing is written to the layers.
# Inputs : work/widen2.pkl and work/bgn.pkl (apply_widen.py); derived breaklines and boundary layers (to check the fids); locked lines.
# Outputs: payload JSON (argument, default work/widen_payload.json) = {"bl": {fid: [[x, y], ...]}, "bd": {fid: [[x, y], ...]}}.
# Run    : cd <WD>; <geo python> <skill>/scripts/widen_payload.py [-c rcs_config.json] [work/widen_payload.json]
#          then: <ogr python> <skill>/scripts/write3.py work/widen_payload.json <tag>
import os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import numpy as np

ap = common.parser('convert the widening result into a write3.py payload')
ap.add_argument('out', nargs='?', default=None, help='output payload (default work/widen_payload.json)')
args = ap.parse_args(); cfg = common.load(args)
import geom
out = args.out or cfg.work('widen_payload.json')
with open(cfg.work('widen2.pkl'), 'rb') as f: W = pickle.load(f)
bgn = {}
if os.path.exists(cfg.work('bgn.pkl')):
    with open(cfg.work('bgn.pkl'), 'rb') as f: bgn = pickle.load(f)
bl = geom.read(cfg.layer('out', 'breaklines')); bd = geom.read(cfg.layer('out', 'boundary'))
newf = W['newf']
miss_bl = sorted(int(k) for k in newf if int(k) not in bl.index); miss_bd = sorted(int(k) for k in bgn if int(k) not in bd.index)
if miss_bl or miss_bd:
    raise SystemExit(f'fids not found in the derived layers: breaklines {miss_bl}, boundary {miss_bd} (were the derived layers created from the same originals?)')
locked = cfg.locked_lines() & {int(k) for k in newf}
if locked:
    raise SystemExit(f'the widening changes locked lines {sorted(locked)}: stop and check widening.never_move / locked.mat_ids')
P = {'bl': {str(int(k)): np.asarray(v, float)[:, :2].tolist() for k, v in newf.items()},
     'bd': {str(int(k)): np.asarray(v, float)[:, :2].tolist() for k, v in bgn.items()}}
with open(out, 'w') as f: json.dump(P, f)
print(f'breaklines changed {len(P["bl"])}, nodestrings changed {len(P["bd"])} -> {out}')
