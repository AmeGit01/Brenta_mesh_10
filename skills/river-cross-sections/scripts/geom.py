# geom.py - shared geometry helpers of the sections toolkit (NOT run directly; needs shapely 2.x, numpy, geopandas).
# Derived from the Brenta core.py: the work-folder variable read from sys.argv is replaced by the Config object of common.py,
# and the face classification by name comes from the configuration (cfg.face_class).
import pickle, collections, warnings
import numpy as np, shapely, shapely.ops, geopandas as gpd
from shapely.geometry import LineString
warnings.filterwarnings('ignore')


def read(path, fid_index=True):
    """GeoDataFrame of a GeoPackage, indexed by fid (default)."""
    return gpd.read_file(path, fid_as_index=fid_index)


def coords(g):
    """(N,2) plan coordinates of any geometry (Z/M dropped)."""
    return shapely.get_coordinates(g)[:, :2]


def load_graph(cfg):
    """Read work/graph.pkl (graph.py). Returns (faces, rows): faces = list of Polygons of the planar graph;
    rows = list of dicts {face, fid, nome, mat, area} for the faces that contain a region point."""
    with open(cfg.work('graph.pkl'), 'rb') as f:
        G = pickle.load(f)
    return G['faces'], G['rows']


def ring_segs(poly):
    """All segments of the exterior and interior rings of poly as an (N,4) array [x0,y0,x1,y1]."""
    out = []
    for r in [poly.exterior] + list(poly.interiors):
        a = shapely.get_coordinates(r)
        out.append(np.c_[a[:-1], a[1:]])
    return np.vstack(out)


def key(s):
    """Direction-independent id of a segment [x0,y0,x1,y1]: end points rounded to 1e-4 m and ordered."""
    a = (round(s[0], 4), round(s[1], 4)); b = (round(s[2], 4), round(s[3], 4))
    return (a, b) if a < b else (b, a)


def boundary_segs(faces, rows, pred):
    """Segments of the outer boundary of the union of the faces whose region name satisfies pred(name):
    a segment shared by two selected faces is dropped. Returns an (M,4) array."""
    cnt = collections.Counter(); keep = {}
    for r in rows:
        if pred(r['nome']):
            for s in ring_segs(faces[r['face']]):
                k = key(s); cnt[k] += 1; keep[k] = s
    return np.array([keep[k] for k, v in cnt.items() if v == 1])


class Rays:
    """First-hit queries of straight lines against a fixed set of segments (STRtree for the candidates)."""

    def __init__(self, segs):
        self.s = segs
        self.t = shapely.STRtree(shapely.linestrings(segs.reshape(-1, 2, 2)))

    def hits(self, o, d, L):
        """Signed distances t (sorted) of the intersections of the line o + t*d (d unit vector) with the segments, |t| <= L.
        Callers use d = left normal of the centerline: t > 0 left bank, t < 0 right bank."""
        ray = LineString([o - d * L, o + d * L]); idx = self.t.query(ray)
        if len(idx) == 0:
            return np.array([])
        S = self.s[idx]; p = S[:, :2]; r = S[:, 2:] - p
        den = d[0] * r[:, 1] - d[1] * r[:, 0]; m = np.abs(den) > 1e-12
        if not m.any():
            return np.array([])
        p = p[m]; r = r[m]; den = den[m]; w = p - o
        t = (w[:, 0] * r[:, 1] - w[:, 1] * r[:, 0]) / den; u = (w[:, 0] * d[1] - w[:, 1] * d[0]) / den
        return np.sort(t[(u >= -1e-9) & (u <= 1 + 1e-9) & (np.abs(t) <= L)])


# ---- angle rule: edited lines must not create angles sharper than cfg rules.min_angle_deg (default 30 degrees)
def _unit(v):
    n = np.hypot(v[0], v[1])
    return v / n if n > 0 else v


def vertex_angles(c):
    """Interior angles (degrees, 0..180; 180 = straight) at the inner vertices of a polyline c (N,2). A small value is a spike."""
    c = np.asarray(c, float)[:, :2]
    out = []
    for i in range(1, len(c) - 1):
        a = _unit(c[i - 1] - c[i]); b = _unit(c[i + 1] - c[i])
        out.append((i, float(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))))
    return out


def _dirs_at(c, p, tol):
    """Directions leaving point p along polyline c: one if p is an end vertex, two if p is inside the line."""
    c = np.asarray(c, float)[:, :2]; d = []
    for i in range(len(c) - 1):
        a, b = c[i], c[i + 1]; ab = b - a; L2 = ab @ ab
        if L2 == 0:
            continue
        t = np.clip((p - a) @ ab / L2, 0, 1)
        if np.hypot(*(a + t * ab - p)) <= tol:
            if t > 1e-12 or i == 0 and np.hypot(*(a - p)) > tol:
                d.append(_unit(a - p)) if np.hypot(*(a - p)) > tol else None
            if t < 1 - 1e-12 or i == len(c) - 2 and np.hypot(*(b - p)) > tol:
                d.append(_unit(b - p)) if np.hypot(*(b - p)) > tol else None
    # remove duplicates (a vertex shared by two consecutive segments gives the same direction twice)
    u = []
    for v in d:
        if not any(np.allclose(v, w, atol=1e-9) for w in u):
            u.append(v)
    return u


def meeting_angles(c1, c2, tol=1e-3):
    """Angles (degrees) between two polylines where they meet (crossing, T-junction or shared end vertex).
    For every meeting point, the smallest angle between a direction leaving the point along c1 and one along c2.
    Returns a list of (x, y, angle). A crossing gives an angle in 0..90, a junction of two line ends 0..180."""
    l1 = shapely.linestrings(np.asarray(c1)[:, :2]); l2 = shapely.linestrings(np.asarray(c2)[:, :2])
    inter = l1.intersection(l2)
    if inter.is_empty:
        if l1.distance(l2) > tol:
            return []
        pts = [shapely.ops.nearest_points(l1, l2)[0]]
    else:
        pts = [g for g in getattr(inter, 'geoms', [inter])]
    out = []
    for g in pts:
        if g.geom_type != 'Point':          # overlapping stretch: no angle (collinear)
            continue
        p = np.array([g.x, g.y]); d1 = _dirs_at(c1, p, tol); d2 = _dirs_at(c2, p, tol)
        if d1 and d2:
            a = min(float(np.degrees(np.arccos(np.clip(u @ v, -1, 1)))) for u in d1 for v in d2)
            out.append((float(p[0]), float(p[1]), a))
    return out


def acute_angles(lines, min_deg=30.0, only=None, tol=1e-3):
    """Angles sharper than min_deg in a set of lines {id: coords}.
    only = ids of the lines to examine (e.g. the edited ones); None = all. Returns (spikes, meetings):
    spikes   = [(id, vertex index, angle)] inside a line;
    meetings = [(id1, id2, x, y, angle)] between two lines (id1 in only)."""
    import shapely.ops  # noqa: F401  (nearest_points)
    ids = list(lines); sel = ids if only is None else [i for i in ids if i in set(only)]
    spikes = [(i, k, a) for i in sel for k, a in vertex_angles(lines[i]) if a < min_deg]
    geoms = [shapely.linestrings(np.asarray(lines[i])[:, :2]) for i in ids]; tree = shapely.STRtree(geoms)
    meetings = []; seen = set()
    for i in sel:
        gi = shapely.linestrings(np.asarray(lines[i])[:, :2])
        for j in tree.query(gi.buffer(tol)):
            k = ids[j]
            if k == i or (k, i) in seen:
                continue
            seen.add((i, k))
            for x, y, a in meeting_angles(lines[i], lines[k], tol):
                if a < min_deg:
                    meetings.append((i, k, x, y, a))
    return spikes, meetings
