# dx_dev_fig.py  (stage 4, 2026-11-19; read-only, after dx_dev.py)
# Purpose: figures for the step analysis of docs/Brenta_analisi_passo_50m.md.
#   fig01_schema_dx.png        sketch: what dx_c, dx_avg, dx_min, dx_max are (analysis 1) and how dx_dev_abs is built (analysis 2);
#                              synthetic geometry, distances computed with the same sampling as dx_dev.py
#   fig02_dx_avg_rami.png      dx_avg of every pair along the reaches (nominal chainage from the section name), mean line
#   fig03_diff_avg_c_rami.png  dx_avg - dx_c along the reaches
#   fig04_diff_avg_c_angolo.png dx_avg - dx_c against the angle between the two sections
#   fig05_dx_dev_istogramma.png histogram of dx_dev (analysis 1) per reach
#   fig06_dx_dev_geometria.png dx_dev against width*tan(angle)/dx_avg (geometric predictor)
#   fig07_dx_avg_ordinati.png  dx_avg sorted ascending (analysis 2): the leftmost pairs set the CFL time step
#   fig08_sensibilita.png      dx_dev_abs of the whole model after removing the k shortest pairs, k = 0..20
# Inputs : argv[1] = pair CSV written by dx_dev.py (docs/Brenta_dx_dev_50m.csv); argv[2] = output folder (docs/figures).
# Output : the PNG files above (150 dpi). Exception pairs (column eccezione = 1) are drawn as hollow grey markers.
# Reaches: taken from the column ramo of the CSV, in order of appearance (2026-11-24: V and B; before, N, V and B).
# Run    : ~/anaconda3/bin/python3 scripts/dx_dev_fig.py docs/Brenta_dx_dev_50m.csv docs/figures      (Anaconda python3)
import sys, os, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
CSV, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
NS = 201                                                   # samples per section, as in dx_dev.py
# palette (reference categorical slots 1-3, validated all-pairs) and neutral inks
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#6250d6']
INK, INK2, MUTED, GRID, EXC = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df', '#7a7975'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'axes.axisbelow': True, 'figure.facecolor': 'white', 'axes.facecolor': 'white', 'legend.frameon': False,
                     'axes.titlesize': 10, 'axes.titlecolor': INK, 'axes.titlelocation': 'left'})
df = pd.read_csv(CSV)
CODES = list(dict.fromkeys(df.ramo)); COL = dict(zip(CODES, PAL)); NAME = {R: 'ramo ' + R for R in CODES}
num = lambda c: c.str.extract(r'(\d+)$')[0].astype(int)
df['km'] = (num(df.sez_monte) + num(df.sez_valle)) / 2 / 1000   # nominal chainage of the pair midpoint
df['pred'] = df.larg_m * np.tan(np.radians(df.ang_gradi)) / df.dx_avg
df['coppia'] = df.sez_monte + '–' + df.sez_valle
exc = df.eccezione == 1
def save(fig, name): fig.savefig(f'{OUT}/{name}', dpi=150, bbox_inches='tight'); plt.close(fig); print('written', name)
def samp(l): return [l.interpolate(t, normalized=True) for t in np.linspace(0, 1, NS)]
def pairdist(la, lb):                                        # same definition as dx_dev.py
    d = [lb.distance(p) for p in samp(la)] + [la.distance(p) for p in samp(lb)]
    return float(np.mean(d)), float(la.distance(lb)), float(np.max(d))
def dabs(v): v = np.asarray(v); return (v.mean() - v.min()) / v.mean()

# ---------------------------------------------------------------- fig01: sketch of the two analyses
BOX = dict(boxstyle='round,pad=0.15', fc='white', ec='none')
fig = plt.figure(figsize=(12, 5.6)); gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.1], height_ratios=[1.25, 1], wspace=0.12, hspace=0.45)
# (a) one pair of sections: centre line through both, sampled distances, dx_min, dx_max, dx_c
ax = fig.add_subplot(gs[:, 0]); ax.set_aspect('equal'); ax.grid(False); ax.axis('off')
th = np.radians(28); c2 = np.array([47.0, 3.0]); h = 16
A = LineString([(0, -h), (0, h)])                                              # section k
B = LineString([tuple(c2 + h * np.array([np.sin(th), -np.cos(th)])), tuple(c2 + h * np.array([-np.sin(th), np.cos(th)]))])  # section k+1
xs = np.linspace(-12, 62, 200); cl = 0.0045 * xs * (xs - c2[0]) + c2[1] * xs / c2[0]          # centre line through (0,0) and c2
ax.plot(xs, cl, color=MUTED, lw=1.2, ls=(0, (6, 3)), zorder=1)
ax.text(xs[-1], cl[-1] + 1.2, "linea d'asse", color=INK2, fontsize=8, ha='right', zorder=6)
pa, pb = samp(A), samp(B)
for p in pa[::25]: q = nearest_points(B, p)[0]; ax.plot([p.x, q.x], [p.y, q.y], color='#9ec5f4', lw=0.8, zorder=2)
for p in pb[::25]: q = nearest_points(A, p)[0]; ax.plot([p.x, q.x], [p.y, q.y], color='#9ec5f4', lw=0.8, zorder=2)
for L_, lab, xy, ha in ((A, 'sezione k', (0, h + 1.5), 'center'), (B, 'sezione k+1', (B.coords[0][0] + 1, B.coords[0][1] - 3.5), 'center')):
    x, y = L_.xy; ax.plot(x, y, color=INK, lw=2.2, solid_capstyle='round', zorder=3); ax.text(*xy, lab, color=INK, fontsize=9, ha=ha)
avg, mn, mx = pairdist(A, B)
p, q = nearest_points(A, B); ax.annotate('', (q.x, q.y), (p.x, p.y), arrowprops=dict(arrowstyle='<->', color='#eb6834', lw=1.6), zorder=4)
ax.text((p.x + q.x) / 2 + 4, p.y + 1.8, f'dx_min = {mn:.1f} m', color=INK, ha='center', fontsize=8.5, bbox=BOX, zorder=6)
d = [B.distance(t) for t in pa]; j = int(np.argmax(d)); p = pa[j]; q = nearest_points(B, p)[0]
ax.annotate('', (q.x, q.y), (p.x, p.y), arrowprops=dict(arrowstyle='<->', color='#6250d6', lw=1.6), zorder=4)
rot = np.degrees(np.arctan2(q.y - p.y, q.x - p.x)); mid = np.array([(p.x + q.x) / 2, (p.y + q.y) / 2]) + 3.0 * np.array([np.sin(np.radians(rot)), -np.cos(np.radians(rot))])
ax.text(*mid, f'dx_max = {mx:.1f} m', color=INK, ha='center', va='center', rotation=rot, fontsize=8.5, bbox=BOX, zorder=6)
sel = (xs >= 0) & (xs <= c2[0]); sc = np.sum(np.hypot(np.diff(xs[sel]), np.diff(cl[sel])))
ax.plot([0, c2[0]], [0, c2[1]], 'o', color=INK, ms=4.5, zorder=5)
ax.text(21, 5.5, f'dx_c = {sc:.1f} m tra i due punti neri,\nlungo la linea d\'asse', color=INK2, ha='center', fontsize=8, bbox=BOX, zorder=6)
ax.set_title('(a) Analisi 1: una coppia di sezioni', fontsize=10, fontweight='bold', color=INK)
ax.text(-13, -h - 7, f'dx_avg = media delle distanze campionate\n(linee azzurre, nei due versi) = {avg:.1f} m\n\n'
        f'dx_dev = (dx_avg − dx_min) / dx_avg = {(avg - mn) / avg:.3f}', color=INK, fontsize=8.5, va='top')
ax.set_xlim(-14, 66); ax.set_ylim(-h - 22, h + 5)
# (b) a reach with a bend: sections normal to the centre line every 50 m, then the series of dx_avg,i
axp = fig.add_subplot(gs[0, 1]); axp.set_aspect('equal'); axp.grid(False); axp.axis('off')
R, w, step, ANG = 60.0, 34.0, 50.0, np.radians(75)
def cl_pt(s):                                                  # straight 150 m, arc of radius R turning ANG to the left, straight
    a1 = 150.0; a2 = a1 + R * ANG
    if s <= a1: return np.array([s, 0.0]), np.array([1.0, 0.0])
    if s <= a2:
        t = (s - a1) / R; return np.array([a1 + R * np.sin(t), R - R * np.cos(t)]), np.array([np.cos(t), np.sin(t)])
    p0 = np.array([a1 + R * np.sin(ANG), R - R * np.cos(ANG)]); dv = np.array([np.cos(ANG), np.sin(ANG)]); return p0 + (s - a2) * dv, dv
S = np.arange(0, 400.1, step); secs = []
cs = np.array([cl_pt(s)[0] for s in np.linspace(-15, 415, 400)]); axp.plot(cs[:, 0], cs[:, 1], color=MUTED, lw=1.2, ls=(0, (6, 3)))
for s in S:
    p, t = cl_pt(s); n = np.array([-t[1], t[0]]); L_ = LineString([tuple(p - n * w / 2), tuple(p + n * w / 2)]); secs.append(L_)
    x, y = L_.xy; axp.plot(x, y, color=INK, lw=1.8, solid_capstyle='round')
dxa = np.array([pairdist(a, b)[0] for a, b in zip(secs[:-1], secs[1:])]); low = dxa <= dxa.min() + 0.05
for i in range(len(dxa)):
    p, t = cl_pt(S[i] + step / 2); n = np.array([-t[1], t[0]]); tx = p - n * (w / 2 + 8)
    axp.text(*tx, f'{i + 1}', color='#eb6834' if low[i] else INK2, ha='center', va='center', fontsize=8.5, fontweight='bold' if low[i] else 'normal')
xy = np.vstack([np.array(s_.coords) for s_ in secs]); axp.set_xlim(xy[:, 0].min() - 12, xy[:, 0].max() + 20); axp.set_ylim(xy[:, 1].min() - 14, xy[:, 1].max() + 6)
axp.set_title('(b) Analisi 2: un tratto con una curva (i numeri sono le coppie i)', fontsize=10, fontweight='bold', color=INK)
axb = fig.add_subplot(gs[1, 1]); i = np.arange(1, len(dxa) + 1); mu = dxa.mean()
axb.vlines(i, dxa.min() - 2, dxa, color=GRID, lw=1); axb.plot(i[~low], dxa[~low], 'o', color='#2a78d6', ms=6.5, mec='white', mew=1.2, zorder=3)
axb.plot(i[low], dxa[low], 'o', color='#eb6834', ms=7.5, mec='white', mew=1.2, zorder=4)
axb.axhline(mu, color=INK2, lw=1, ls=(0, (4, 2))); axb.text(len(dxa) + 0.5, mu + 0.25, f'media {mu:.1f} m', va='bottom', fontsize=8, color=INK2)
axb.text(len(dxa) + 0.5, dxa.min(), f'min {dxa.min():.1f} m', va='center', fontsize=8, color=INK2)
axb.set_xlim(0.5, len(dxa) + 2.6); axb.set_xticks(i); axb.set_xlabel('coppia i'); axb.set_ylabel('dx_avg,i (m)')
axb.set_ylim(dxa.min() - 2, dxa.max() + 2)
axb.set_title(f'dx_dev_abs = (media − min) / media = {dabs(dxa):.3f};   dt(min) / dt(media) = 1 − dx_dev_abs = {1 - dabs(dxa):.3f}', fontsize=8.5, color=INK)
save(fig, 'fig01_schema_dx.png')

# ---------------------------------------------------------------- helpers for the along-reach small multiples
def along(col, ylabel, name, ref=None, label_n=4, fmt='{:+.1f}'):
    fig, axs = plt.subplots(len(CODES), 1, figsize=(10, 2.2 * len(CODES)), sharey=True, gridspec_kw=dict(hspace=0.45), squeeze=False); axs = axs[:, 0]
    for ax, R in zip(axs, CODES):
        d = df[df.ramo == R]; e = d.eccezione == 1
        ax.plot(d.km[~e], d[col][~e], 'o', ms=3.2, color=COL[R], mec='none', alpha=0.9)
        ax.plot(d.km[e], d[col][e], 'o', ms=4.5, mfc='white', mec=EXC, mew=1.1)
        if ref == 'mean': m = d[col].mean(); ax.axhline(m, color=INK2, lw=0.9, ls=(0, (4, 2))); ax.text(1.005, m, f'media\n{m:.2f}', transform=ax.get_yaxis_transform(), fontsize=7.5, color=INK2, va='center')
        elif ref is not None: ax.axhline(ref, color=INK2, lw=0.9)
        far = d.reindex((d[col] - (d[col].mean() if ref == 'mean' else 0)).abs().sort_values(ascending=False).index)[:label_n].sort_values('km')
        span, last, dy = d.km.max(), -1e9, 0                                   # stack labels of points closer than 6% of the reach length
        for _, r in far.iterrows():
            dy = dy - 10 if r.km - last < 0.06 * span else 0; last = r.km
            ax.annotate(f"{r.coppia}  {fmt.format(r[col])}", (r.km, r[col]), xytext=(7, dy), textcoords='offset points', fontsize=7,
                        color=INK2, va='center', arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.5) if dy else None)
        ax.set_title(NAME[R] + f'  ({len(d)} coppie)'); ax.set_xlim(-0.2, d.km.max() + 0.6)
    axs[-1].set_xlabel('progressiva nominale della coppia (km, dal nome delle sezioni)'); axs[len(axs) // 2].set_ylabel(ylabel)
    axs[0].plot([], [], 'o', mfc='white', mec=EXC, label='coppia con una sezione in eccezione'); axs[0].legend(loc='lower right', fontsize=7.5)
    save(fig, name)
along('dx_avg', 'dx_avg (m)', 'fig02_dx_avg_rami.png', ref='mean', fmt='{:.2f} m')
along('diff_avg_c', 'dx_avg − dx_c (m)', 'fig03_diff_avg_c_rami.png', ref=0, fmt='{:+.2f} m')

# ---------------------------------------------------------------- fig04: dx_avg - dx_c against the angle
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for R in CODES:
    d = df[(df.ramo == R) & ~exc]; ax.plot(d.ang_gradi, d.diff_avg_c, 'o', ms=3.5, color=COL[R], mec='none', alpha=0.85, label=NAME[R])
ax.plot(df.ang_gradi[exc], df.diff_avg_c[exc], 'o', ms=5, mfc='white', mec=EXC, mew=1.1, label='eccezione')
for _, r in df.nsmallest(5, 'diff_avg_c').iterrows(): ax.annotate(r.coppia, (r.ang_gradi, r.diff_avg_c), xytext=(5, 0), textcoords='offset points', fontsize=7, color=INK2, va='center')
ax.axhline(0, color=INK2, lw=0.9); ax.set_xlabel('angolo tra le due sezioni (°)'); ax.set_ylabel('dx_avg − dx_c (m)'); ax.legend(fontsize=8, loc='lower left')
save(fig, 'fig04_diff_avg_c_angolo.png')

# ---------------------------------------------------------------- fig05: histogram of dx_dev per reach
fig, axs = plt.subplots(1, len(CODES), figsize=(3.4 * len(CODES), 3.2), sharey=False, gridspec_kw=dict(wspace=0.25), squeeze=False); axs = axs[0]; bins = np.arange(0, 0.26, 0.01)
for ax, R in zip(axs, CODES):
    d = df[df.ramo == R]
    ax.hist([d.dx_dev[d.eccezione == 0], d.dx_dev[d.eccezione == 1]], bins=bins, stacked=True, color=[COL[R], '#d6d5d0'], edgecolor='white', linewidth=0.8)
    md = d.dx_dev.median(); ax.axvline(md, color=INK2, lw=0.9, ls=(0, (4, 2))); ax.text(0.97, 0.95, f'mediana (tratteggio) {md:.3f}', transform=ax.transAxes, ha='right', va='top', fontsize=7.5, color=INK2)
    ax.set_title(NAME[R] + f'  ({len(d)} coppie)'); ax.set_xlabel('dx_dev'); ax.set_xlim(0, 0.26)
axs[0].set_ylabel('numero di coppie'); axs[-1].bar([0], [0], color='#d6d5d0', label='eccezioni'); axs[-1].legend(fontsize=7.5, loc='center right')
save(fig, 'fig05_dx_dev_istogramma.png')

# ---------------------------------------------------------------- fig06: dx_dev against the geometric predictor
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for R in CODES:
    d = df[(df.ramo == R) & ~exc]; ax.plot(d.pred, d.dx_dev, 'o', ms=3.5, color=COL[R], mec='none', alpha=0.85, label=NAME[R])
ax.plot(df.pred[exc], df.dx_dev[exc], 'o', ms=5, mfc='white', mec=EXC, mew=1.1, label='eccezione')
for _, r in df.nlargest(4, 'dx_dev').iterrows(): ax.annotate(r.coppia, (r.pred, r.dx_dev), xytext=(5, 0), textcoords='offset points', fontsize=7, color=INK2, va='center')
rho = np.corrcoef(df.pred, df.dx_dev)[0, 1]
ax.set_xlabel('larghezza · tan(angolo) / dx_avg'); ax.set_ylabel('dx_dev'); ax.legend(fontsize=8, loc='lower right')
ax.text(0.02, 0.95, f'correlazione = {rho:.2f}', transform=ax.transAxes, fontsize=8.5, color=INK, va='top')
save(fig, 'fig06_dx_dev_geometria.png')

# ---------------------------------------------------------------- fig07: sorted dx_avg (analysis 2)
fig, ax = plt.subplots(figsize=(8.5, 4.2))
s = df.sort_values('dx_avg').reset_index(drop=True); s['rank'] = np.arange(1, len(s) + 1); e = s.eccezione == 1
ax.plot(s['rank'][~e], s.dx_avg[~e], 'o', ms=2.6, color='#2a78d6', mec='none', label='coppia')
ax.plot(s['rank'][e], s.dx_avg[e], 'o', ms=4.5, mfc='white', mec=EXC, mew=1.1, label='coppia con una sezione in eccezione')
mu_all, mu_ne = df.dx_avg.mean(), df.dx_avg[~exc].mean()
ax.axhline(mu_all, color=INK2, lw=0.9, ls=(0, (4, 2))); ax.text(len(s) + 5, mu_all + 0.15, f'media {mu_all:.2f} m', fontsize=7.5, color=INK2, va='bottom', ha='right')
for _, r in s.head(4).iterrows(): ax.annotate(f"{r.coppia}  {r.dx_avg:.2f} m", (r['rank'], r.dx_avg), xytext=(8, -2), textcoords='offset points', fontsize=7, color=INK2, va='center')
ax.set_xlim(-10, len(s) + 60); ax.set_xlabel('coppie ordinate per dx_avg crescente'); ax.set_ylabel('dx_avg (m)'); ax.legend(fontsize=8, loc='lower right')
save(fig, 'fig07_dx_avg_ordinati.png')

# ---------------------------------------------------------------- fig08: sensitivity to the k shortest pairs
fig, ax = plt.subplots(figsize=(7.5, 3.8)); K = np.arange(0, 21)
for lab, v, c, va in (('tutte le coppie', np.sort(df.dx_avg.values), '#2a78d6', 'bottom'), ('senza eccezioni', np.sort(df.dx_avg[~exc].values), '#eb6834', 'top')):
    y = [dabs(v[k:]) for k in K]; ax.plot(K, y, '-o', color=c, lw=2, ms=4.5, mec='white', mew=1, label=lab)
    ax.text(K[-1] + 0.4, y[-1], f'{y[-1]:.3f}', fontsize=7.5, color=INK2, va=va); ax.text(-0.5, y[0], f'{y[0]:.3f}', fontsize=7.5, color=INK2, va='center', ha='right')
ax.set_xlim(-2.5, 22.5); ax.set_ylim(0, None); ax.set_xticks([0, 1, 2, 3, 5, 10, 15, 20])
ax.set_xlabel('k = coppie più corte tolte'); ax.set_ylabel('dx_dev_abs (intero modello)'); ax.legend(fontsize=8)
save(fig, 'fig08_sensibilita.png')
