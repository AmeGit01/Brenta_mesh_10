# snap_near_nodes.py - near-node rule by MOVING the near breakline vertex onto the crossing (no new vertex is created)
# Purpose: where a section crosses a breakline and a breakline vertex lies closer than rules.near_node.radius to the crossing, BASEmesh
#          would create tiny or stretched elements between the crossing node and that vertex. This script fixes it by moving that
#          vertex exactly onto the crossing: the breakline then passes through the crossing at one of its own vertices, the section still
#          crosses it at the same point, and no vertex is added. Lines that share the vertex (junction node, T-junctions ending on it)
#          move with it, so no connection is lost. It is the preferred fix; fix_near_nodes.py (insert the crossing as a vertex and remove
#          or slide the vertices around it) remains for the cases this one cannot solve.
#          Per crossing (same definition as verify3.py): the near vertices are the vertices of any breakline within (ignore_below, radius)
#          of the crossing, excluding the crossings of the same section; unlike verify3.py, vertices closer than ignore_below (1 mm) are
#          also moved (only a vertex within 1e-6 m counts as the crossing itself): they would give sub-millimetre mesh edges.
#          * the nearest near vertex lying on the CROSSED breakline is moved onto the crossing;
#          * other near vertices on the crossed breakline are deleted if they are plain inner vertices (not shared, not ends);
#          * near vertices on OTHER lines cannot be moved onto the crossing (it would connect two lines): they are reported.
#          A move is accepted only if: the vertex is not on a nodestring or a section (another crossing), no locked line (locked.mat_ids)
#          is touched, it is not the end of a line that lies on another line (T-junction: it would detach), every changed line stays
#          simple, no new crossing between lines appears, no region point lies in the area swept by the moved segments and none gets
#          closer than min(previous, rules.regions.clearance), and no new angle sharper than rules.min_angle_deg appears.
# Inputs : derived breaklines and boundary (sections and nodestrings) and regions layers; locked lines (cfg.locked_lines());
#          rules.near_node {radius, ignore_below}, rules.min_angle_deg, rules.regions.clearance; exceptions.near_node / locked_line
#          (sections listed there are skipped unless --all).
# Outputs: payload JSON (argument, default work/snap_payload.json) = {"bl": {fid: [[x, y], ...]}} for write3.py; prints every move,
#          every deletion, the rejected and the unresolved cases with the reason. Nothing is written to the layers.
# Run    : cd <working folder>; <geo python> <skill>/scripts/snap_near_nodes.py [-c rcs_config.json] [--all] [payload.json]
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import numpy as np, shapely
from shapely.geometry import LineString, Point, Polygon
from scipy.spatial import cKDTree

ap = common.parser('near-node rule: move the near breakline vertex onto the crossing')
ap.add_argument('out', nargs='?', default=None); ap.add_argument('--all', action='store_true', help='also treat the sections listed as exceptions')
args = ap.parse_args(); cfg = common.load(args)
R = cfg['rules']['near_node']['radius']
MIN_ANG = cfg['rules']['min_angle_deg']; CLEAR = cfg['rules']['regions']['clearance']
EXC = set() if args.all else (cfg.exc_near_node() | cfg.exc_wall())
LOCK = cfg.locked_lines(); EPS = 1e-9
COINC = 1e-6   # a vertex closer than this to the crossing IS the crossing; anything farther (even 0.1 mm) is moved onto it,
               # because a vertex a fraction of a millimetre off the crossing gives mesh edges of that length
bl = geom.read(cfg.layer('out', 'breaklines')); bd = geom.read(cfg.layer('out', 'boundary')); rg = geom.read(cfg.layer('out', 'regions'))
fN = cfg.f('boundary', 'name')
F = {int(f): geom.coords(g).copy() for f, g in bl.geometry.items() if g is not None and not g.is_empty}
SEC = {n: geom.coords(g) for n, g in zip(bd[fN], bd.geometry) if cfg.is_section(n)}
NS = {n: geom.coords(g) for n, g in zip(bd[fN], bd.geometry) if not cfg.is_section(n)}
NSL = shapely.STRtree([LineString(c) for c in list(NS.values()) + list(SEC.values())])   # nodestrings + sections
RP = np.array([[p.x, p.y] for p in rg.geometry if p is not None])
F0 = {f: c.copy() for f, c in F.items()}

def lines_at(p, tol=EPS):
    """(fid, vertex index) of every breakline vertex at point p."""
    return [(f, k) for f, c in F.items() for k in np.nonzero(np.hypot(*(c - p).T) <= tol)[0]]

def on_nodestring_or_section(p):
    return any(LineString(g.coords).distance(Point(p)) < 1e-6 for g in NSL.geometries[NSL.query(Point(p).buffer(1e-6))])

def is_t_end(f, k):
    """True if vertex k of line f is an end lying on the interior of another breakline (T-junction)."""
    c = F[f]
    if k not in (0, len(c) - 1): return False
    p = Point(c[k])
    return any(g != f and LineString(F[g]).distance(p) < 1e-6 and not any(np.hypot(*(F[g] - c[k]).T) <= EPS) for g in F)

# ---- crossings (section x breakline), as in verify3.py
lines = {f: LineString(c) for f, c in F.items()}; keys = list(lines); T = shapely.STRtree([lines[f] for f in keys])
crossings = []
for nm, sc in SEC.items():
    if nm in EXC: continue
    l = LineString(sc)
    on = [keys[i] for i in T.query(l, predicate='intersects') if l.distance(Point(F[keys[i]][0])) < 1e-6 and l.distance(Point(F[keys[i]][-1])) < 1e-6]
    hit = [keys[i] for i in T.query(l, predicate='intersects') if keys[i] not in on]
    pts = [(f, p) for f in hit for p in geom.coords(l.intersection(lines[f]))]
    for f, p in pts: crossings.append((nm, f, p, [q for _, q in pts]))
print(f'crossings {len(crossings)} (sections listed as exceptions skipped: {sorted(EXC) if EXC else "none"})')

moves, dels, rejected, unresolved = [], [], [], []
for nm, f, p, own in crossings:
    allv = np.vstack(list(F.values())); kd = cKDTree(allv)
    near = [j for j in kd.query_ball_point(p, R) if np.hypot(*(allv[j] - p)) > COINC and all(np.hypot(*(allv[j] - q)) > 1e-6 for q in own)]
    if not near: continue
    near_pts = sorted({tuple(allv[j]) for j in near}, key=lambda q: np.hypot(q[0] - p[0], q[1] - p[1]))
    on_f = [q for q in near_pts if np.hypot(*(F[f] - q).T).min() <= EPS]
    other = [q for q in near_pts if q not in on_f]
    for q in other:
        unresolved.append((nm, f, round(float(np.hypot(q[0] - p[0], q[1] - p[1])), 2), 'vertex on another line', [g for g, _ in lines_at(np.array(q))]))
    if not on_f: continue
    # already a vertex at the crossing? then nothing to move, only deletions
    has_at_p = np.hypot(*(F[f] - p).T).min() <= COINC
    targets = on_f if has_at_p else on_f[1:]
    if not has_at_p:
        q = np.array(on_f[0]); at = lines_at(q); why = None
        if any(g in LOCK for g, _ in at): why = 'locked line'
        elif on_nodestring_or_section(q): why = 'vertex on a nodestring or section'
        elif any(is_t_end(g, k) for g, k in at): why = 'end of a T-junction'
        if why is None:
            new = {g: F[g].copy() for g, _ in at}
            for g, k in at: new[g][k] = p
            old = {g: F[g] for g, _ in at}
            # swept area of every moved segment: the triangles (neighbour, old vertex, new vertex)
            swept = []
            for g, k in at:
                for nb in (k - 1, k + 1):
                    if 0 <= nb < len(F[g]):
                        tri = Polygon([F[g][nb], q, p])
                        if tri.area > 1e-9: swept.append(tri)
            NL = {g: LineString(c) for g, c in new.items()}
            ctx_ids = [keys[i] for i in T.query(Point(p).buffer(3 * R)) if keys[i] not in new]
            if not all(l2.is_simple for l2 in NL.values()): why = 'line not simple'
            elif any(any(t.contains(Point(r)) for t in swept) for r in RP[cKDTree(RP).query_ball_point(p, 3 * R)] if len(RP)): why = 'region point in the swept area'
            else:
                for g, l2 in NL.items():
                    for h in ctx_ids:
                        if l2.crosses(lines[h]) and not LineString(old[g]).crosses(lines[h]): why = f'new crossing with {h}'; break
                    if why: break
                if why is None and len(RP):
                    idx = cKDTree(RP).query_ball_point(p, 3 * R)
                    for r in RP[idx]:
                        d0 = min(LineString(old[g]).distance(Point(r)) for g in NL); d1 = min(l2.distance(Point(r)) for l2 in NL.values())
                        if d1 < min(d0, CLEAR) - 1e-9: why = f'region point closer than {CLEAR} m'; break
                if why is None:
                    others = {('bl', h): F[h] for h in ctx_ids}
                    others.update({('ns', n): c for n, c in list(SEC.items()) + list(NS.items()) if LineString(c).distance(Point(p)) < 3 * R})
                    acute = common.new_acute_angles(MIN_ANG, {('bl', g): c for g, c in old.items()}, {('bl', g): c for g, c in new.items()}, others)
                    if acute: why = f'new acute angle {round(acute[0][3], 1)} deg'
        if why:
            rejected.append((nm, f, round(float(np.hypot(*(q - p))), 2), why)); continue
        for g, c in new.items(): F[g] = c; lines[g] = LineString(c)
        T = shapely.STRtree([lines[h] for h in keys])
        moves.append((nm, f, round(float(np.hypot(*(q - p))), 3), sorted(new)))
    # remaining near vertices on the crossed line: delete plain inner vertices
    for q in targets:
        q = np.array(q); at = lines_at(q)
        if len(at) == 1 and at[0][0] == f and 0 < at[0][1] < len(F[f]) - 1 and f not in LOCK and not on_nodestring_or_section(q):
            c2 = np.delete(F[f], at[0][1], axis=0); l2 = LineString(c2)
            ctx_ids = [keys[i] for i in T.query(Point(p).buffer(3 * R)) if keys[i] != f]
            acute = common.new_acute_angles(MIN_ANG, {('bl', f): F[f]}, {('bl', f): c2}, {('bl', h): F[h] for h in ctx_ids})
            if l2.is_simple and not any(l2.crosses(lines[h]) and not lines[f].crosses(lines[h]) for h in ctx_ids) and not acute:
                F[f] = c2; lines[f] = l2; T = shapely.STRtree([lines[h] for h in keys])
                dels.append((nm, f, round(float(np.hypot(*(q - p))), 3))); continue
        unresolved.append((nm, f, round(float(np.hypot(*(q - p))), 2), 'second near vertex, cannot be deleted', [g for g, _ in at]))

changed = {f: F[f] for f in F if F[f].shape != F0[f].shape or np.abs(F[f] - F0[f]).max() > 0}
out = args.out or cfg.work('snap_payload.json')
json.dump({'bl': {str(f): c.tolist() for f, c in changed.items()}}, open(out, 'w'))
print(f'1. vertices moved onto the crossing: {len(moves)} (max move {max([m[2] for m in moves], default=0)} m)')
for m in moves: print('   move', m)
print(f'2. near vertices deleted: {len(dels)}', dels)
print(f'3. moves rejected: {len(rejected)}'); [print('   reject', r) for r in rejected]
print(f'4. unresolved: {len(unresolved)}'); [print('   open', u) for u in unresolved]
print(f'breaklines changed {len(changed)} -> {out}')
