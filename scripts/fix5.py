# fix5.py  (stage 2, 2026-11-17; previous: assemble.py, next: check5.py / check_geom.py / regions2.py)
# Purpose: enforce the 5 m rule on the breaklines: no breakline vertex at a distance in (1 mm, 5 m) from a crossing between a
#          section (or a nodestring) and a breakline. Crossings never move: they are inserted as vertices; T-junctions are made
#          explicit first; special cases: breakline 1225 laid on section N15050 (region point 485), breaklines 987 laid on N11750 and 988
#          slid to 5.05 m from the crossings (source strip). Then, per crossing, vertices within 5 m are removed, junctions moved onto the
#          crossing, or junctions slid along their lines. Every operation is validated (see ok_change): network deviation <= TOL=2 m,
#          no new crossings, no self-intersection, region points not brought closer than min(previous, 1 m), vertices on nodestrings never moved.
# Inputs : (cwd = WD) in/breaklines_50m.gpkg, in/boundary_50m.gpkg, in/regioni_ponti_50m.gpkg, secs_new.json (assemble.py).
# Output : WD/fix5.json = dict(F = fid -> list of vertices of every breakline, log = operations done, unres = unresolved crossings, XS = section crossings);
#          prints counts (T-junction vertices, crossings, removed/moved/slid/unresolved, changed features).
# Run    : cd WD ; python3 fix5.py      (Anaconda python3; relative paths: the working directory MUST be WD)
# Units  : metres.
# 5 m rule: no breakline vertex between 0 and 5 m from a section/breakline crossing.
# Crossings never move: they are inserted as fixed vertices; only breakline vertices are removed or moved onto a crossing.
# imports (pickle is imported but not used in this script); warnings silenced
import json, pickle, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
# R6: point -> (x,y) rounded to 1e-6 m, hashable key identifying a vertex
R6=lambda p:(round(float(p[0]),6),round(float(p[1]),6))
# bl = current breaklines, bd = boundary layer (nodestrings + sections) of the 50 m layers
bl=gpd.read_file('in/breaklines_50m.gpkg',fid_as_index=True); bd=gpd.read_file('in/boundary_50m.gpkg',fid_as_index=True)
# secs = new sections (assemble.py)
secs=json.load(open('secs_new.json'))
# F: fid -> list of (x,y) vertices of every breakline; it is modified in place by all the steps below
F={int(f):[tuple(map(float,p)) for p in shapely.get_coordinates(g)] for f,g in bl.geometry.items() if g is not None and not g.is_empty}
# orig: untouched copy of the coordinates (arrays), used to detect changed features at the end
orig={f:np.array(v) for f,v in F.items()}
# LOCK = breaklines bounding the wall regions (mat_id 11, list from prep_inputs_nvb.py): kept exactly as they are,
# no vertex inserted, moved or removed; lockv = their vertices, added to the fixed set below
LOCK=set(json.load(open('mat11_lines.json')))
lockv={(round(float(p[0]),6),round(float(p[1]),6)) for f in LOCK if f in F for p in F[f]}
# SEC = (name, LineString) of the new sections
SEC=[(s['nome'],LineString(s['coords'])) for s in secs]
# NS = non-section nodestrings (bridges, boundaries, ...): names not like S/V + 5 digits (old-style); (in/boundary_50m.gpkg still has the old S/V sections; a layer with N/B sections would wrongly put them in NS)
NS=[(n,LineString(shapely.get_coordinates(g))) for n,g in zip(bd.nome,bd.geometry) if not(n[0] in 'SV' and n[1:6].isdigit())]
# nsverts = vertices of the nodestrings (never moved)
nsverts={R6(p) for _,l in NS for p in l.coords}
# 1) insert every crossing (sections and other nodestrings) as a vertex of the breakline
# insert_crossings(lines): for each (name, line) and each breakline crossing it, add the crossing point as a vertex of the breakline;
# returns the list (line name, fid, point). Breaklines laid on the line (1225, 987) are skipped: overlap, not a crossing.
def insert_crossings(lines):
    out=[]
    for nm,l in lines:
        for f in list(F):
            g=LineString(F[f])
            if not g.intersects(l): continue
            if f in LOCK: out.append((nm,f,tuple(map(float,shapely.get_coordinates(g.intersection(l))[0])))); continue   # record the crossing, do not insert it
            # skip the breakline laid exactly on the line (both ends on it)
            if g.hausdorff_distance(l.intersection(g.buffer(1e-6)))<1e-6 and g.length>0.01 and l.distance(shapely.Point(F[f][0]))<1e-6 and l.distance(shapely.Point(F[f][-1]))<1e-6:
                continue      # breakline laid on the section (1225, 987): overlap, not a crossing
            # p = crossing point
            for p in shapely.get_coordinates(g.intersection(l)):
                # ex = existing vertex (of any breakline) at the same place within 1e-6: reuse it, avoiding float-noise copies
                ex=[q for c2 in F.values() for q in c2 if abs(q[0]-p[0])<1e-6 and abs(q[1]-p[1])<1e-6]
                if ex: p=np.array(ex[0])      # reuse an existing vertex (T-junction) instead of a float-noise copy
                # insert p after the nearest segment unless a vertex of this line already coincides (<1e-7)
                c=F[f]; d=[shapely.distance(shapely.Point(p),LineString(c[i:i+2])) for i in range(len(c)-1)]; i=int(np.argmin(d))
                if min(np.hypot(p[0]-q[0],p[1]-q[1]) for q in c)>1e-7: c.insert(i+1,(float(p[0]),float(p[1])))
                out.append((nm,f,(float(p[0]),float(p[1]))))
    return out
# T-junctions first: every line end lying on the inside of another line becomes a vertex of that line,
# so that removing vertices can never detach a line and merge two regions
# add_tjunctions(only): for each line, every end of another line lying on it (within 1e-6) becomes a vertex of it; returns the number of vertices added
def add_tjunctions(only=None):
    # ends = (fid, end point) for every line end; ET = point index
    ends=[(g,c[i]) for g,c in F.items() if len(c)>=2 for i in (0,-1)]
    ET=shapely.STRtree([shapely.Point(e) for _,e in ends]); n=0
    for f in (only if only is not None else list(F)):
        if len(F[f])<2 or f in LOCK: continue
        l=LineString(F[f])
        for i in ET.query(l.buffer(1e-6)):
            g,e=ends[i]
            if g==f or min(abs(e[0]-q[0])+abs(e[1]-q[1]) for q in F[f])<1e-9 or l.distance(shapely.Point(e))>1e-6: continue
            c=F[f]; d=[LineString(c[j:j+2]).distance(shapely.Point(e)) for j in range(len(c)-1)]; j=int(np.argmin(d)); c.insert(j+1,tuple(e)); n+=1
    return n
# make all T-junctions explicit at the start
print('T-junction vertices added (start)',add_tjunctions())
# point 485: breakline 1225 (bed | source_brenta_nuovo) is laid exactly on section N15050 (ex S15120):
# its ends slide along the toe lines on which they lie, to the crossings of the section with those lines.
# sec15 = section N15050; e = new ends of 1225: each old end p lies on host toe lines; slide it to the crossing of the host with the section
sec15=dict(SEC)['N15050']; e=[]
for p in F[1225][0],F[1225][-1]:
    host=[f for f in F if f!=1225 and LineString(F[f]).distance(shapely.Point(p))<1e-3]
    x=[q for f in host for q in shapely.get_coordinates(LineString(F[f]).intersection(sec15))]
    e.append(tuple(map(float,x[0]))); print('1225 end',p,'on',host,'->',e[-1],'shift',round(float(np.hypot(p[0]-x[0][0],p[1]-x[0][1])),3))
# 1225 now lies on the section (2 vertices)
F[1225]=e
# N11750 (ex S11804) crosses the source strip source_3_brenta_3 bounded by 987 (upstream) and 988 (downstream):
# 987 is laid on the section (as for 485); 988 slides downstream along the toe lines to 5.05 m from the crossings.
# sec11 = section N11750; cross_on(f,l) = first crossing point of breakline f with line l; hosts(p,excl) = breaklines through p other than excl
sec11=dict(SEC)['N11750']
def cross_on(f,l): return tuple(map(float,shapely.get_coordinates(LineString(F[f]).intersection(l))[0]))
def hosts(p,excl): return [f for f in F if f not in excl and LineString(F[f]).distance(shapely.Point(p))<1e-3]
# newend: old end of 987 (rounded) -> crossing of its host with the section
newend={}
# 987 ends move onto the crossings of their host lines with N11750
for p in (F[987][0],F[987][-1]):
    h=[f for f in hosts(p,{987,988}) if LineString(F[f]).intersects(sec11)][0]; newend[R6(p)]=cross_on(h,sec11)
# apply to every vertex shared with the old 987 ends, then drop consecutive duplicate vertices
for f in list(F):     # move 987 ends (and every vertex shared with them) onto the crossings
    F[f]=[newend.get(R6(q),q) for q in F[f]]
# remove consecutive duplicates created by the move
for g in list(F):
    if g in LOCK: continue
    F[g]=[q for i,q in enumerate(F[g]) if i==0 or R6(q)!=R6(F[g][i-1])]
# 988 ends slide downstream along their host line until at least 5.05 m from the crossing C
for p in (F[988][0],F[988][-1]):
    # h = host line, line = its geometry, C = crossing with sec11; t0/tc = positions along the host of the end and of C; sg = direction away from C
    h=[f for f in hosts(p,{987,988}) if f!=987][0]; line=LineString(F[h]); C=np.array(cross_on(h,sec11))
    t0=line.project(shapely.Point(p)); tc=line.project(shapely.Point(C)); sg=1 if t0>tc else -1; t=t0
    # advance by 1 cm until the distance from C is >= 5.05 m
    while np.hypot(*(np.array(line.interpolate(t).coords[0])-C))<5.05: t+=sg*0.01
    # q = new end position; every vertex equal to the old end is replaced by q
    q=tuple(map(float,line.interpolate(t).coords[0])); k=R6(p)
    for f in list(F): F[f]=[q if R6(v)==k else v for v in F[f]]
    # (nothing to do: a T-junction on a host without a vertex there leaves the host unchanged)
    if R6(q) not in {R6(v) for v in F[h]}:     # T-junction on a line without a vertex there: keep the host line unchanged
        pass
    print('988 end',p,'->',q,'on',h)
# XS = section x breakline crossings, XN = nodestring x breakline crossings (both inserted as vertices)
XS=insert_crossings(SEC); XN=insert_crossings(NS)
# same[name] = crossings of the same section: they are section nodes, ignored as 'near' vertices
same=collections.defaultdict(set)
for nm,_,p in XS: same[nm].add(R6(p))
# NSU = union of the nodestrings; onns = breakline vertices lying on a nodestring
NSU=shapely.union_all([l for _,l in NS])
onns={R6(p) for c in F.values() for p in c if NSU.distance(shapely.Point(p))<1e-6}
# fixed = vertices that must never move: all crossings, nodestring vertices, vertices on nodestrings
fixed={R6(p) for _,_,p in XS+XN}|nsverts|onns|lockv
# RP = region points; RPT = spatial index
RP=[g for g in gpd.read_file('in/regioni_ponti_50m.gpkg').geometry if g is not None]; RPT=shapely.STRtree(RP)
# TOL = maximum change of the line network caused by one operation
TOL=2.0   # maximum change of the line network caused by one operation (m)
# ok_change(old,new): validate one operation. old/new: {fid: coords} of the touched features; returns (ok, reason).
# Checks: deviation of the network <= TOL; region points (within 1 m) not closer than min(previous distance, 1 m); new lines simple;
# no new crossing with other lines; touched features do not start crossing each other.
def ok_change(old,new):
    # old/new: {feature: coords} for the features touched by one operation
    # A/B = union of the old/new touched lines; d = largest distance of a point (every 0.25 m) of one from the other
    A=shapely.union_all([LineString(c) for c in old.values() if len(c)>=2]); B=shapely.union_all([LineString(c) for c in new.values() if len(c)>=2])
    d=max([B.distance(shapely.Point(q)) for c in old.values() if len(c)>=2 for q in LineString(c).segmentize(0.25).coords]+[A.distance(shapely.Point(q)) for c in new.values() if len(c)>=2 for q in LineString(c).segmentize(0.25).coords]+[0])
    if d>TOL: return False,'deviation %.2f m'%d
    # region points must not get closer than 1 m (or than before, if already closer)
    for i in RPT.query(B.buffer(1.0)):        # region points must not get closer than 1 m (or than before, if already closer)
        dn=B.distance(RP[i]); do=A.distance(RP[i])
        if dn<min(do,1.0)-1e-6: return False,'too close to region point (%.2f m)'%dn
    # others = untouched breaklines; T = index
    others=[LineString(F[g]) for g in F if g not in new and len(F[g])>=2]
    T=shapely.STRtree(others)
    # every new line must be simple and must not cross untouched lines unless the old one already did
    for g,c in new.items():
        if len(c)<2: continue
        l=LineString(c)
        if not l.is_simple: return False,'self-intersection'
        for i in T.query(l,predicate='crosses'):
            if len(old.get(g,[]))<2 or not LineString(old[g]).crosses(others[i]): return False,'new crossing'
    # the touched features must not start crossing each other
    for g1 in new:          # the touched features must not start crossing each other
        for g2 in new:
            if g1<g2 and len(new[g1])>=2 and len(new[g2])>=2 and LineString(new[g1]).crosses(LineString(new[g2])) and not LineString(old[g1]).crosses(LineString(old[g2])): return False,'new crossing'
    return True,''
# counts
print('section crossings',len(XS),'nodestring crossings',len(XN))
# snap_all: empty placeholder, never used
def snap_all():   # vertices are compared by rounded key; make every occurrence identical
    pass
# index(): occ = vertex key -> [(fid, position)], nb = vertex key -> set of neighbouring vertex keys along the lines
def index():
    occ=collections.defaultdict(list); nb=collections.defaultdict(set)
    for f,c in F.items():
        for i,p in enumerate(c):
            occ[R6(p)].append((f,i))
            if i: nb[R6(p)].add(R6(c[i-1])); nb[R6(c[i-1])].add(R6(p))
    return occ,nb
# log = operations done; unres = crossings left unresolved; moved_to = crossings that already received a moved junction
log=[]; unres=[]; moved_to=set()
# main loop over every section crossing C (section nm, breakline f); kC = its key; skip = vertices to ignore
for nm,f,C in XS:
    kC=R6(C); skip=set()
    # repeat (max 40 times): take the nearest vertex within (1e-3, 5) m that is not a crossing of the same section
    for it in range(40):
        occ,nb=index()
        # near = vertices at distance (1 mm, 5 m) from C, sorted by distance
        allv=np.array([k for k in occ]); d=np.hypot(allv[:,0]-C[0],allv[:,1]-C[1])
        near=[tuple(allv[i]) for i in np.argsort(d) if 1e-3<d[i]<5.0]
        near=[k for k in near if k in occ and k not in same[nm] and k not in skip]
        if not near: break
        # k = nearest offending vertex, dist = its distance
        k=near[0]; dist=float(np.hypot(k[0]-C[0],k[1]-C[1]))
        # a vertex of a nodestring crossing cannot be moved: report it
        if k in fixed: unres.append((nm,f,round(dist,3),'crossing of a nodestring',k)); skip.add(k); continue
        # o = occurrences of k; interior = it is an inner vertex of exactly one line
        o=occ[k]; interior=len(o)==1 and 0<o[0][1]<len(F[o[0][0]])-1
        # plain inner vertex: remove it if ok_change accepts
        if interior:                       # plain vertex of one line: remove it (if the change is acceptable)
            g,i=o[0]; new=F[g][:i]+F[g][i+1:]; okc,why=ok_change({g:F[g]},{g:new})
            if not okc: unres.append((nm,f,round(dist,3),'removal rejected: '+why,k)); skip.add(k); continue
            F[g]=new; log.append((nm,'del',g,round(dist,3)))
            continue
        # (junction or end)
        # junction / feature end: move it onto the crossing, but only if it is connected to C by a path of removable vertices
        # search (DFS) a path from C to k through removable vertices closer than 5 m; if found, those are removed and k is moved onto C
        path=None; stack=[(kC,[kC])]; seen={kC}
        while stack:
            v,pth=stack.pop()
            for w in nb[v]:
                if w in seen or np.hypot(w[0]-C[0],w[1]-C[1])>=5.0: continue
                if w==k: path=pth+[w]; break
                ow=occ[w]
                if w not in fixed and len(ow)==1 and 0<ow[0][1]<len(F[ow[0][0]])-1: seen.add(w); stack.append((w,pth+[w]))
            if path: break
        # only one junction can be moved onto the same crossing
        if kC in moved_to: unres.append((nm,f,round(dist,3),'second junction near the same crossing',k)); skip.add(k); continue
        # no path of removable vertices: leave for the sliding step
        if path is None: unres.append((nm,f,round(dist,3),'vertex of another line',k,[g for g,_ in occ[k]])); skip.add(k); continue
        # touched = features involved; new = their modified copies
        touched={g for w in path[1:-1] for g,_ in occ[w]}|{g for g,_ in occ[k]}
        new={g:list(F[g]) for g in touched}
        # remove the intermediate path vertices
        for w in path[1:-1]:
            (g,i),=occ[w]; new[g]=[p for p in new[g] if R6(p)!=w]
        # move the junction vertex k onto the crossing C
        for g,_ in occ[k]:
            new[g]=[C if R6(p)==k else p for p in new[g]]
        # drop consecutive duplicate vertices
        for g in new: new[g]=[p for i,p in enumerate(new[g]) if i==0 or R6(p)!=R6(new[g][i-1])]
        # validate and apply
        okc,why=ok_change({g:F[g] for g in touched},new)
        if not okc: unres.append((nm,f,round(dist,3),'move rejected: '+why,k)); skip.add(k); continue
        F.update(new)
        log.append((nm,'move',k,round(dist,3))); moved_to.add(kC)
# allX = all section crossing points (used by slide)
allX=np.array([p for _,_,p in XS])
# (T-junctions on the changed lines)
# T-junctions: an end of one line lying on the inside of another (changed) line becomes a shared vertex,
# so that float noise of inserted vertices cannot turn a touch into a crossing
# chg_now = breaklines changed so far; ends/ET = line ends and their index; nT = vertices added
chg_now=[f for f in F if f in orig and (len(F[f])!=len(orig[f]) or np.abs(np.array(F[f])-orig[f]).max()>1e-9)]
ends=[(g,c[i]) for g,c in F.items() if len(c)>=2 for i in (0,-1)]
ET=shapely.STRtree([shapely.Point(e) for _,e in ends]); nT=0
for f in chg_now:
    if f in LOCK: continue
    l=LineString(F[f])
    for i in ET.query(l.buffer(1e-6)):
        g,e=ends[i]
        if g==f or min(abs(e[0]-q[0])+abs(e[1]-q[1]) for q in F[f])<1e-9 or l.distance(shapely.Point(e))>1e-6: continue
        c=F[f]; d=[LineString(c[j:j+2]).distance(shapely.Point(e)) for j in range(len(c)-1)]; j=int(np.argmin(d)); c.insert(j+1,tuple(e)); nT+=1
# count
print('T-junction vertices added',nT)
# slide(k): for a junction/end k (not an inner vertex) slide it along its lines (for T-junctions only the two most collinear features = the toe chain)
# by 0.01..6 m (stopping at the first position) until it is >= 5.05 m from every section crossing; validated with ok_change.
# Returns (distance slid, position) or None; (0.0,'gone') if the vertex no longer exists.
def slide(k):
    # fs = occurrences of the vertex
    occ,nb=index(); fs=occ[k]
    if not fs: return (0.0,'gone')     # already removed while fixing another crossing
    # inner vertex: cannot slide
    if any(0<i<len(F[g])-1 for g,i in fs): return None
    # T-junction: choose the pair of features with the most opposite directions (min dot product)
    if len(fs)>2:                   # T-junction: slide only along the two most collinear features (the toe chain)
        dirs=[]
        for g,i in fs:
            c=F[g]; j=1 if i==0 else len(c)-2; v=np.array(c[j])-np.array(c[i]); dirs.append(v/np.hypot(*v))
        pr=min(((a,b) for a in range(len(fs)) for b in range(a+1,len(fs))),key=lambda ab: float(np.dot(dirs[ab[0]],dirs[ab[1]])))
        chain=[fs[pr[0]],fs[pr[1]]]
    else: chain=fs
    # best = (t, point) with the smallest slide along any feature of the chain
    best=None
    for g,i in chain:
        c=F[g]; j=1 if i==0 else len(c)-2; a=np.array(c[i]); b=np.array(c[j]); L=np.hypot(*(b-a))
        if R6(c[j]) in fixed: L=L-0.01
        for t in np.arange(0.01,min(L,6.0),0.01):
            q=a+(b-a)*t/L
            if np.hypot(*(allX-q).T).min()>=5.05:
                # no admissible position
                if best is None or t<best[0]: best=(t,tuple(map(float,q)))
                break
    if best is None: return None
    # move every occurrence to q and validate
    q=best[1]; new={g:list(F[g]) for g,_ in fs}
    for g,i in fs: new[g][i]=q
    okc,why=ok_change({g:F[g] for g,_ in fs},new)
    if not okc: return None
    F.update(new); return best
# second pass over the unresolved crossings: slide junctions that are not fixed vertices
still=[]
for u in unres:
    if (u[3] in ('vertex of another line','second junction near the same crossing') or u[3].startswith('move rejected') or u[3].startswith('removal rejected')) and R6(u[4]) not in fixed:
        r=slide(R6(u[4]))
        if r: log.append((u[0],'slide',u[4],round(r[0],2))); continue
    still.append(u)
# keep the still unresolved ones
unres=still
# summary: removed/moved/slid counts and the unresolved list
print('removed',sum(l[1]=='del' for l in log),'moved',sum(l[1]=='move' for l in log),'slid',[(l[0],l[3]) for l in log if l[1]=='slide'],'unresolved',len(unres))
for u in unres: print(' unresolved',u)
# first definition of chg (kept: line is superseded by the next one)
chg={f:F[f] for f in F if len(F[f])!=len(orig[f]) or np.abs(np.array(F[f])-orig[f]).max()>1e-9 if len(F[f])==len(orig[f])} 
# chg = features whose coordinates differ from the original
chg={f:F[f] for f in F if len(F[f])!=len(orig[f]) or np.abs(np.array(F[f])-orig[f]).max()>1e-9}
print('features changed',len(chg),'collapsed',[f for f in F if len(F[f])<2])
# save the result
json.dump(dict(F={str(f):v for f,v in F.items()},log=log,unres=unres,XS=XS),open('fix5.json','w'))
