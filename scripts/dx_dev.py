# dx_dev.py  (stage 4, 2026-11-18; read-only analysis, after verify3.py)
# Purpose: statistics of the step dx between consecutive sections of the same reach, at two levels.
#   Per pair i (sections k, k+1 of the same reach):
#     dx_avg  = mean distance between the two sections: each section is sampled at NS equally spaced points, the distance of every point
#               from the other section (segment) is taken, and dx_avg is the mean over the points of both sections (symmetric);
#     dx_min  = minimum distance between the two segments; dx_max = maximum of the sampled distances;
#     dx_c    = distance along the centre line (difference of s_m, i.e. dist_next); diff_avg_c = dx_avg - dx_c;
#     ang     = angle between the two sections (degrees); larg = mean length of the two sections.
#   ANALYSIS 1 (local, one value per pair): dx_dev = (dx_avg - dx_min) / dx_avg  -> 0 for parallel sections, grows when they converge.
#   ANALYSIS 2 (global, one value per set of pairs: reach N, V, B and all together):
#     dx_dev_abs = (mean_i dx_avg_i - min_i dx_avg_i) / mean_i dx_avg_i  (>= 0). It measures how much the shortest step is below the mean
#     step; in an explicit 1D scheme the time step from the CFL condition (dt <= CFL*dx/(|u|+c)) is set by the shortest dx, so
#     dt(min dx)/dt(mean dx) = 1 - dx_dev_abs (same velocity). The same quantity is also given for the series dx_c and dx_min
#     (dx_dev_abs_c, dx_dev_abs_min), together with the per-pair relative step e_i = (dx_avg_i - mean)/mean, the sensitivity to the k
#     shortest pairs and the list of the shortest pairs.
# Exceptions (user, 2026-11-18): N16000 and B00000, B00100, B00150, B00200, B00300, B00400, B00450, B00500 (5 m rule, the Borgo ones
#          because of vertices of the locked wall lines); N01900-N01950, B11200-B11250, B00250-B00300-B00350 (spacing). A pair is excluded when
#          at least one of its two sections is an exception section. Every table is given with all pairs and without exceptions.
# Inputs : argv[1] = layers folder (boundary_50m.gpkg, centerpoints_50m.gpkg); argv[2] = output CSV of the pairs (e.g. docs/Brenta_dx_dev_50m.csv).
# Output : the CSV (one row per pair: sez_monte, sez_valle, ramo, dx_c, dx_avg, diff_avg_c, dx_min, dx_max, dx_dev, ang_gradi, larg_m, e_avg_ramo, eccezione)
#          and Markdown tables printed to stdout (analysis 1, analysis 2, shortest pairs, sensitivity).
# Run    : python3 scripts/dx_dev.py layers docs/Brenta_dx_dev_50m.csv      (Anaconda python3)
import sys, csv, re, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
L,OUT=sys.argv[1],sys.argv[2]; NS=201
EXC={'N16000','N01900','N01950','B11200','B11250','B00250','B00300','B00350',
     'B00000','B00100','B00150','B00200','B00400','B00450','B00500'}   # last line: 5 m rule, vertices of the locked wall lines (B00300 already above)
bd=gpd.read_file(f'{L}/boundary_50m.gpkg'); cp=gpd.read_file(f'{L}/centerpoints_50m.gpkg'); S=dict(zip(cp.nome,cp.s_m))
sec=bd[bd.nome.str.match(r'^[NVB]\d{5}$')]; G={n:LineString(shapely.get_coordinates(g)[:,:2]) for n,g in zip(sec.nome,sec.geometry)}
order=list(sec.nome); rows=[]
def samp(l): return [l.interpolate(t,normalized=True) for t in np.linspace(0,1,NS)]
# ---- per-pair quantities
for a,b in zip(order[:-1],order[1:]):
    if a[0]!=b[0]: continue
    la,lb=G[a],G[b]; d=[lb.distance(p) for p in samp(la)]+[la.distance(p) for p in samp(lb)]
    avg=float(np.mean(d)); mn=float(la.distance(lb)); mx=float(np.max(d))
    u=np.diff(shapely.get_coordinates(la),axis=0)[0]; v=np.diff(shapely.get_coordinates(lb),axis=0)[0]
    ang=float(np.degrees(np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))))
    rows.append(dict(sez_monte=a,sez_valle=b,ramo=a[0],dx_c=S[b]-S[a],dx_avg=avg,diff_avg_c=avg-(S[b]-S[a]),dx_min=mn,dx_max=mx,dx_dev=(avg-mn)/avg,
                     ang_gradi=ang,larg_m=(la.length+lb.length)/2,eccezione=int(a in EXC or b in EXC)))
for R in 'NVB':
    m=np.mean([r['dx_avg'] for r in rows if r['ramo']==R])
    for r in rows:
        if r['ramo']==R: r['e_avg_ramo']=(r['dx_avg']-m)/m
cols=['sez_monte','sez_valle','ramo','dx_c','dx_avg','diff_avg_c','dx_min','dx_max','dx_dev','ang_gradi','larg_m','e_avg_ramo','eccezione']
with open(OUT,'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k:(round(r[k],4) if isinstance(r[k],float) else r[k]) for k in cols})
# sets: per reach and total, with all pairs and without exceptions
SETS=[(f"{('ramo '+R) if R else 'totale'}, {lab}",[r for r in rows if fl(r) and (R is None or r['ramo']==R)])
      for lab,fl in (('tutte',lambda r: True),('senza eccezioni',lambda r: not r['eccezione'])) for R in ('N','V','B',None)]
pair=lambda r: f"{r['sez_monte']}–{r['sez_valle']}"
# ---- ANALYSIS 1: dx_dev per pair
print('## Analisi 1: dx_dev = (dx_avg - dx_min) / dx_avg, per coppia\n')
print('| insieme | coppie | media | mediana | dev. std | 90° perc. | 95° perc. | 99° perc. | max | > 0.01 | > 0.02 | > 0.05 | > 0.10 | angolo medio (°) | larghezza media (m) |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for lab,rs in SETS:
    v=np.array([r['dx_dev'] for r in rs]); q=lambda p: np.percentile(v,p)
    print(f"| {lab} | {len(v)} | {v.mean():.4f} | {np.median(v):.4f} | {v.std():.4f} | {q(90):.4f} | {q(95):.4f} | {q(99):.4f} | {v.max():.4f} | {(v>0.01).sum()} | {(v>0.02).sum()} | {(v>0.05).sum()} | {(v>0.10).sum()} | {np.mean([r['ang_gradi'] for r in rs]):.2f} | {np.mean([r['larg_m'] for r in rs]):.1f} |")
A=np.array([r['dx_dev'] for r in rows]); W=np.array([r['larg_m'] for r in rows]); T=np.array([r['ang_gradi'] for r in rows]); X=np.array([r['dx_avg'] for r in rows])
print(f"\ncorrelation of dx_dev with: angle {np.corrcoef(A,T)[0,1]:.2f}, width {np.corrcoef(A,W)[0,1]:.2f}, width*tan(angle)/dx_avg {np.corrcoef(A,W*np.tan(np.radians(T))/X)[0,1]:.2f}")
print('\ntop 15 dx_dev:\n| coppia | dx_c | dx_avg | dx_avg - dx_c | dx_min | dx_max | dx_dev | angolo (°) | larghezza (m) | eccezione |\n|---|---|---|---|---|---|---|---|---|---|')
for r in sorted(rows,key=lambda r:-r['dx_dev'])[:15]:
    print(f"| {pair(r)} | {r['dx_c']:.2f} | {r['dx_avg']:.2f} | {r['diff_avg_c']:+.2f} | {r['dx_min']:.2f} | {r['dx_max']:.2f} | {r['dx_dev']:.4f} | {r['ang_gradi']:.1f} | {r['larg_m']:.1f} | {'sì' if r['eccezione'] else ''} |")
# ---- ANALYSIS 2: dx_dev_abs per set
def dabs(v): v=np.array(v); return (v.mean()-v.min())/v.mean()
print('\n## Analisi 2: dx_dev_abs = (media dx_avg - min dx_avg) / media dx_avg, per insieme\n')
print('| insieme | coppie | media dx_avg (m) | dev. std (m) | min dx_avg (m) | coppia del min | max dx_avg (m) | dx_dev_abs | min/media = 1 - dx_dev_abs | dx_dev_abs su dx_c | dx_dev_abs su dx_min |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for lab,rs in SETS:
    v=np.array([r['dx_avg'] for r in rs]); j=int(np.argmin(v))
    print(f"| {lab} | {len(v)} | {v.mean():.2f} | {v.std():.2f} | {v.min():.2f} | {pair(rs[j])} | {v.max():.2f} | {dabs(v):.4f} | {1-dabs(v):.3f} | {dabs([r['dx_c'] for r in rs]):.4f} | {dabs([r['dx_min'] for r in rs]):.4f} |")
print('\nper-pair relative step e = (dx_avg - media)/media, percentiles (per set):')
print('| insieme | 1° perc. | 5° perc. | 10° perc. | mediana | 90° perc. | 95° perc. | 99° perc. | e < -0.02 | e < -0.05 | e < -0.10 |\n|---|---|---|---|---|---|---|---|---|---|---|')
for lab,rs in SETS:
    v=np.array([r['dx_avg'] for r in rs]); e=(v-v.mean())/v.mean(); q=lambda p: np.percentile(e,p)
    print(f"| {lab} | {q(1):.4f} | {q(5):.4f} | {q(10):.4f} | {np.median(e):.4f} | {q(90):.4f} | {q(95):.4f} | {q(99):.4f} | {(e<-0.02).sum()} | {(e<-0.05).sum()} | {(e<-0.10).sum()} |")
print('\nsensitivity: dx_dev_abs after removing the k shortest pairs (dx_avg), total:')
print('| insieme | k=0 | k=1 | k=2 | k=3 | k=5 | k=10 |\n|---|---|---|---|---|---|---|')
for lab,rs in SETS:
    if not lab.startswith('totale'): continue
    v=np.sort([r['dx_avg'] for r in rs])
    print(f"| {lab} | "+' | '.join(f'{dabs(v[k:]):.4f}' for k in (0,1,2,3,5,10))+' |')
print('\n15 shortest pairs by dx_avg (all):\n| coppia | dx_avg (m) | e (totale) | dx_c (m) | dx_min (m) | dx_dev | angolo (°) | eccezione |\n|---|---|---|---|---|---|---|---|')
mt=np.mean([r['dx_avg'] for r in rows])
for r in sorted(rows,key=lambda r:r['dx_avg'])[:15]:
    print(f"| {pair(r)} | {r['dx_avg']:.2f} | {(r['dx_avg']-mt)/mt:.4f} | {r['dx_c']:.2f} | {r['dx_min']:.2f} | {r['dx_dev']:.4f} | {r['ang_gradi']:.1f} | {'sì' if r['eccezione'] else ''} |")
print('\n10 shortest pairs by dx_min (all): '+', '.join(f"{pair(r)} {r['dx_min']:.2f}" for r in sorted(rows,key=lambda r:r['dx_min'])[:10]))
print('\n10 longest pairs by dx_avg (all): '+', '.join(f"{pair(r)} {r['dx_avg']:.2f}" for r in sorted(rows,key=lambda r:-r['dx_avg'])[:10]))
print('\nexcluded pairs:',', '.join(pair(r) for r in rows if r['eccezione']))
print('\ndx_avg - dx_c: mean',np.mean([r['diff_avg_c'] for r in rows]).round(3),'m, min',np.min([r['diff_avg_c'] for r in rows]).round(3),'m, max',np.max([r['diff_avg_c'] for r in rows]).round(3),'m; without exceptions min',np.min([r['diff_avg_c'] for r in rows if not r['eccezione']]).round(3),'max',np.max([r['diff_avg_c'] for r in rows if not r['eccezione']]).round(3))
print('\nmean |dx_avg - dx_c|',np.mean([abs(r['dx_avg']-r['dx_c']) for r in rows]).round(3),'m, max',np.max([abs(r['dx_avg']-r['dx_c']) for r in rows]).round(3),'m')
print('written',OUT,len(rows))
