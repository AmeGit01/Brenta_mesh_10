# gaps.py - print-only check of connectivity after the widening
# Purpose: find line ends that touched another breakline in the original data (within 1 mm) but touch nothing in the widened
#          geometry. Boundary lines are not considered.
# Inputs : work/chains.pkl (chains.py); work/widen2.pkl (apply_widen.py); config: widening.enabled.
# Outputs: none (stdout): the number of broken ends, then up to 60 tuples (fid, end 0=first/-1=last, new end xy, original neighbour fids
#          (max 4), original end xy); a final OK / **CHECK** line.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/gaps.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import pickle, shapely
from shapely.geometry import LineString, Point

args = common.parser('list the breakline ends that lost their connection after the widening').parse_args()
cfg = common.load(args)
if not cfg.get('widening', {}).get('enabled', False):
    print('widening.enabled is false: nothing to do'); sys.exit(0)
with open(cfg.work('chains.pkl'), 'rb') as f: C = pickle.load(f)
with open(cfg.work('widen2.pkl'), 'rb') as f: W2 = pickle.load(f)
# feat: original geometries; newf: widened geometries (only changed features); keys: fid list (index i = position in keys)
feat = C['feat']; newf = W2['newf']
keys = list(feat)
# lines(F): LineString for every fid using F[fid] if present else the original
def lines(F): return [LineString(F.get(k, feat[k])) for k in keys]
# old/new geometries with STRtrees
old = lines({}); new = lines(newf)
to = shapely.STRtree(old); tn = shapely.STRtree(new)
# conn(tree,ls,p,me): fids of lines (other than index me) within 1 mm of point p
def conn(tree, ls, p, me):
    idx = tree.query(Point(p), predicate='dwithin', distance=1e-3); return [keys[i] for i in idx if i != me]
# bad: ends that had a neighbour in the original geometry but none in the new one
bad = []
for i, k in enumerate(keys):
    a = feat[k]; b = newf.get(k, a)
    for e in (0, -1):
        oc = conn(to, old, a[e], i); nc = conn(tn, new, b[e], i)
        if oc and not nc: bad.append((k, e, [round(float(x), 1) for x in b[e]], oc[:4], [round(float(x), 1) for x in a[e]]))
print(len(bad))
for b in bad[:60]: print(b)
print('OK' if not bad else '**CHECK** broken connections: inspect and fix the listed ends')
