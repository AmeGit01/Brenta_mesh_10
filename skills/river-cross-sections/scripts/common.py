# common.py - shared module of the sections toolkit (NOT run directly).
# Purpose: one place for the working-folder convention and the case configuration, so that no script contains absolute paths
#          or case-specific names/numbers.
#
# Working-folder convention
#   The WORKING FOLDER (WD) is the folder that contains the case configuration file (default name: rcs_config.json).
#   Every path written in the configuration is RELATIVE to WD. Scripts are launched with the current directory = WD:
#       cd <WD> ; <python> <toolkit>/scripts/<script>.py [-c rcs_config.json] [script arguments]
#   Typical layout:  WD/rcs_config.json, WD/layers/ (original + derived GeoPackages, DTM), WD/work/ (intermediate files), WD/docs/
#
# This module only imports the standard library, so it works both in the geo interpreter (geopandas/shapely) and in the
# OGR interpreter (GDAL, no shapely). Geometry helpers that need shapely are in geom.py.
import argparse, json, os, re, sys

DEFAULT_CONFIG = 'rcs_config.json'


class Config:
    """Case configuration. cfg['a']['b'] gives raw values; the helpers below resolve paths and names."""

    def __init__(self, path):
        self.file = os.path.abspath(path)
        self.wd = os.path.dirname(self.file)          # working folder = folder of the config file
        with open(self.file) as f:
            self.raw = json.load(f)

    def __getitem__(self, k):
        return self.raw[k]

    def get(self, k, default=None):
        return self.raw.get(k, default)

    # ---- paths (all relative to WD)
    def path(self, rel):
        """Absolute path of a path given relative to WD (an absolute path is refused: the config must stay portable)."""
        if os.path.isabs(rel):
            raise SystemExit(f'config error: absolute path not allowed ({rel}); write it relative to the working folder')
        return os.path.join(self.wd, rel)

    def dir(self, key):
        """Folder from cfg['paths'][key] (layers, work, docs, mesh), created for 'work' if missing."""
        p = self.path(self.raw['paths'][key])
        if key == 'work':
            os.makedirs(p, exist_ok=True)
        return p

    def work(self, name):
        """Path of an intermediate file in the work folder."""
        return os.path.join(self.dir('work'), name)

    def layer(self, which, key):
        """GeoPackage path of a layer. which = 'in' (original inputs, never written) or 'out' (derived layers);
        key = breaklines | boundary | regions | centerline | centerpoints | bankpoints."""
        group = self.raw['inputs'] if which == 'in' else self.raw['outputs']
        return os.path.join(self.dir('layers'), group[key] + '.gpkg')

    def layer_name(self, which, key):
        group = self.raw['inputs'] if which == 'in' else self.raw['outputs']
        return group[key]

    def backup(self, key, tag):
        """Path of the tagged backup of a derived layer: <layer>_backup_<tag>.gpkg."""
        return os.path.join(self.dir('layers'), f"{self.raw['outputs'][key]}_backup_{tag}.gpkg")

    def dtm(self):
        return os.path.join(self.dir('layers'), self.raw['inputs']['dtm'])

    # ---- schema: logical field name -> field name in the layers
    def f(self, layer, logical):
        """Field name, e.g. cfg.f('regions','mat_id') -> 'mat_id'; cfg.f('bankpoints','kind') -> 'tipo'."""
        return self.raw['fields'][layer][logical]

    # ---- sections and reaches
    def is_section(self, name):
        return name is not None and re.fullmatch(self.raw['sections']['name_pattern'], name) is not None

    def reaches(self):
        """List of reach dicts in output order."""
        return self.raw['reaches']

    def reach(self, code):
        for r in self.raw['reaches']:
            if r['code'] == code:
                return r
        raise KeyError(code)

    def reach_of(self, section_name):
        """Reach code of a section name (the code is the prefix before the digits)."""
        return section_name[:-self.raw['sections']['digits']]

    def section_name(self, code, number):
        return f"{code}{number:0{self.raw['sections']['digits']}d}"

    # ---- face classes (from the region-point names)
    def face_class(self, name):
        """Class of a region name: the first class in cfg['face_classes']['order'] whose rule matches, else cfg default."""
        fc = self.raw['face_classes']
        n = name or ''
        for c in fc['order']:
            rule = fc['classes'][c]
            if n in rule.get('names', []) or any(n.startswith(p) for p in rule.get('prefix', [])) \
                    or any(n.endswith(s) for s in rule.get('suffix', [])):
                return c
        return fc['default']

    def fixed_classes(self):
        return list(self.raw['face_classes'].get('fixed', []))

    def editable_classes(self):
        return list(self.raw['face_classes'].get('editable', []))

    def is_fixed_class(self, c):
        """True if faces of class c keep their outline (face_classes.fixed)."""
        return c in self.fixed_classes()

    def is_editable_class(self, c):
        """True if the outline of faces of class c may move (face_classes.editable)."""
        return c in self.editable_classes()

    # ---- rules
    def min_angle(self):
        """Smallest angle (degrees) allowed inside a line and between lines (rules.min_angle_deg)."""
        return float(self.raw['rules']['min_angle_deg'])

    def near_node(self):
        """Near-node rule parameters: radius, slide_margin, max_displacement, ignore_below (rules.near_node)."""
        return self.raw['rules']['near_node']

    # ---- exceptions accepted by the user
    def exc_near_node(self):
        """Sections exempt from the near-node rule (any reason), as a set of names."""
        e = self.raw.get('exceptions', {})
        return {x['section'] for x in e.get('near_node', [])}

    def exc_angle(self):
        """Accepted acute angles: list of {where: [x, y] or [id, ...], reason, date} (exceptions.angle)."""
        return list(self.raw.get('exceptions', {}).get('angle', []))

    def exc_wall(self):
        """Sections whose near vertex belongs to a locked line (subset reported separately)."""
        e = self.raw.get('exceptions', {})
        return {x['section'] for x in e.get('locked_line', [])}

    def exc_spacing(self):
        """Consecutive section pairs exempt from the spacing rule, as a set of (a, b) tuples."""
        e = self.raw.get('exceptions', {})
        return {tuple(x['pair']) for x in e.get('spacing', [])}

    def exc_vertices(self):
        """Sections allowed more than two vertices (one part, left end first), as a set of names (exceptions.vertices)."""
        e = self.raw.get('exceptions', {})
        return {x['section'] for x in e.get('vertices', [])}

    def locked_lines(self):
        """fids of breaklines that must never be modified (file written by locked_lines.py, in the work folder)."""
        p = self.work(self.raw['locked']['lines_file'])
        if not os.path.exists(p):
            raise SystemExit(f'missing {p}: run locked_lines.py first')
        with open(p) as f:
            return set(json.load(f))


def run_together(c1, c2, tol=1e-3, length=0.5):
    """True if two polylines lie within tol of each other over more than `length` metres (a breakline laid on a section or a
    nodestring): they have no angle there. Needs shapely (geo interpreter)."""
    import shapely
    a = shapely.linestrings(c1); b = shapely.linestrings(c2)
    return a.intersection(b.buffer(tol)).length > length


def new_acute_angles(min_deg, old, new, others=None, match=0.5, tol=1e-3):
    """Acute angles (< min_deg) that an edit CREATES. Needs shapely (geo interpreter); imports geom lazily.
    old/new = {id: coords} of the touched lines before/after the edit (ids hashable, same ids in both or a subset);
    others = {id: coords} of the lines that stay as they are (they can meet the touched lines).
    Lines that run together (run_together) have no angle. An acute angle after the edit is not new if the same lines had an acute angle within `match` metres before and the
    new angle is not sharper than the old one. Returns [('spike', id, (x, y), angle) | ('meet', (id1, id2), (x, y), angle)]."""
    import numpy as np
    import geom
    others = others or {}
    def acute(touched):
        ctx = {**others, **touched}
        sp, mt = geom.acute_angles(ctx, min_deg, only=list(touched), tol=tol)
        mt = [m for m in mt if not run_together(ctx[m[0]], ctx[m[1]])]
        res = [('spike', i, tuple(np.asarray(ctx[i], float)[k, :2]), a) for i, k, a in sp]
        res += [('meet', frozenset((i, j)), (x, y), a) for i, j, x, y, a in mt]
        return res
    before = acute({i: c for i, c in old.items() if len(c) >= 2}); out = []
    for kind, ids, pt, a in acute({i: c for i, c in new.items() if len(c) >= 2}):
        if not any(k == kind and i == ids and np.hypot(pt[0] - q[0], pt[1] - q[1]) <= match and a >= b - 1e-6
                   for k, i, q, b in before):
            out.append((kind, ids, pt, a))
    return out


def parser(description):
    """argparse parser with the standard -c/--config option; scripts add their own arguments."""
    p = argparse.ArgumentParser(description=description)
    p.add_argument('-c', '--config', default=DEFAULT_CONFIG,
                   help=f'case configuration, relative to the current folder (default {DEFAULT_CONFIG}); its folder is the working folder')
    return p


def load(args):
    """Load the configuration named in args.config and print where the script is working (first line of every run)."""
    if not os.path.exists(args.config):
        raise SystemExit(f'configuration not found: {args.config} (run the script from the working folder or pass -c)')
    cfg = Config(args.config)
    print(f'# {os.path.basename(sys.argv[0])}  case {cfg.get("project", {}).get("name", "?")}  working folder {cfg.wd}')
    return cfg
