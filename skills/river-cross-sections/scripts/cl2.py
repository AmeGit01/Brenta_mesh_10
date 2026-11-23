# cl2.py - smooth the raw centerlines, resample them at exactly 1 m and measure the bank widths along the perpendiculars.
# Purpose: smooth each raw centerline (rawcl.pkl), resample it so that the ARRAY INDEX = progressive distance s in m, and at every
#          point measure the distances to the toe lines and to the top-of-bank lines along the perpendicular. Result: cltab.pkl.
# Inputs : work/graph.pkl (graph.py); work/rawcl.pkl (cl.py: keys = centerline names + 'P');
#          config params.cl2: toe_classes, top_classes (face classes whose outline is the toe / the top of bank), resample_step,
#          sigma_narrow, sigma_wide, sigma_width, width_narrow, width_wide, width_default, normal_step, ray_range,
#          report_lines (centerlines reported in blocks), report_block, report_thresholds, plot_lines.
# Outputs: work/cltab.pkl = dict(centerline name -> dict(q, t, B, SL, SR, W)); work/tab.png (plot); diagnostics on stdout.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/cl2.py [-c rcs_config.json]
# Sign convention here: n = LEFT normal of the local direction; Rays.hits gives t>0 on the left, t<0 on the right. In this script 'L'
# (tl, cl, SL) is the NEGATIVE-t side (geometrically the right side); the widening/placing scripts use L for the POSITIVE-t side.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, numpy as np, shapely, warnings
from shapely.geometry import LineString
from scipy.ndimage import gaussian_filter1d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

cfg = common.load(common.parser('smooth centerlines, resample at 1 m, measure bank widths').parse_args())
pr = cfg['params']['cl2']
faces, rows = geom.load_graph(cfg)
with open(cfg.work('rawcl.pkl'), 'rb') as f: RC = pickle.load(f)
CL = [c['name'] for c in cfg.get('centerlines', [])]
miss = [n for n in CL if n not in RC]
if not CL or miss:
    raise SystemExit(f"config/rawcl mismatch: centerlines {miss or '(section missing)'} not in work/rawcl.pkl; run cl.py with the same config")
toe, top = set(pr['toe_classes']), set(pr['top_classes'])
# tb = toe segments (bed boundary); tc = top-of-bank segments (boundary of the top classes); Rb/Rc = ray-query objects on them
tb = geom.boundary_segs(faces, rows, lambda n: cfg.face_class(n) in toe)
tc = geom.boundary_segs(faces, rows, lambda n: cfg.face_class(n) in top)
Rb, Rc = geom.Rays(tb), geom.Rays(tc)
ST, RR = pr['resample_step'], pr['ray_range']


def res(a, st=ST):
    """Resample polyline a every st metres."""
    l = LineString(a); s = np.arange(0, l.length, st); return shapely.get_coordinates(shapely.line_interpolate_point(l, s))


def w(q, i, R, step=pr['normal_step']):
    """Hits of the normal at point i with the segments of R. Tangent from the chord q[i-step]..q[i+step]; returns (hits, normal)."""
    a = q[max(i - step, 0)]; b = q[min(i + step, len(q) - 1)]; t = b - a; t /= np.hypot(*t); n = np.array([-t[1], t[0]]); h = R.hits(q[i], n, RR)
    return h, n


def smooth(q, bw):
    """Blend of a light (sigma_narrow) and a heavy (sigma_wide) Gaussian smoothing. Weight of the heavy one: 0 when the smoothed bed
    width bw <= width_narrow, 1 when >= width_wide, linear between: narrow reaches follow the channel, wide ones are straightened."""
    s0 = np.c_[gaussian_filter1d(q[:, 0], pr['sigma_narrow'], mode='nearest'), gaussian_filter1d(q[:, 1], pr['sigma_narrow'], mode='nearest')]
    s1 = np.c_[gaussian_filter1d(q[:, 0], pr['sigma_wide'], mode='nearest'), gaussian_filter1d(q[:, 1], pr['sigma_wide'], mode='nearest')]
    a = np.clip((gaussian_filter1d(bw, pr['sigma_width'], mode='nearest') - pr['width_narrow']) / (pr['width_wide'] - pr['width_narrow']), 0, 1)[:, None]
    return s0 * (1 - a) + s1 * a


def table(q):
    """Row [tl,tr,cl,cr,0,0] per point (last two columns always 0, unused); NaN row if the normal does not cross toe and top lines on
    both sides. tl/tr: nearest toe crossing on the negative/positive side; cl/cr: nearest top-of-bank crossing on each side."""
    out = np.full((len(q), 6), np.nan)
    for i in range(len(q)):
        hb, n = w(q, i, Rb); hc, _ = w(q, i, Rc)
        if len(hb) == 0 or not (hb > 0).any() or not (hb < 0).any() or len(hc) == 0 or not (hc > 0).any() or not (hc < 0).any(): continue
        tl = hb[hb < 0].max(); tr = hb[hb > 0].min(); cl = hc[hc < 0].max(); cr = hc[hc > 0].min()
        out[i] = [tl, tr, cl, cr, 0, 0]
    return out


res1 = {}
for name in CL:
    q = res(RC[name])
    # first pass widths drive the smoothing; bed width bw = tr - tl (missing -> width_default)
    t = table(q); bw = np.nan_to_num(t[:, 1] - t[:, 0], nan=pr['width_default'])
    qs = smooth(q, bw)
    # resample at exact step (index i = distance s = i * step); final table
    l = LineString(qs); ss = np.arange(0, l.length, ST); qf = shapely.get_coordinates(shapely.line_interpolate_point(l, ss)); t = table(qf)
    # B = bed width (toe-to-toe); SL/SR = toe-to-top distance on the negative/positive side; W = total width top-to-top
    B = t[:, 1] - t[:, 0]; SL = t[:, 0] - t[:, 2]; SR = t[:, 3] - t[:, 1]; W = t[:, 3] - t[:, 2]
    print(name, 'L', round(l.length, 1), 'in-bed miss', int(np.isnan(t[:, 0]).sum()), 'B p5/50/95', np.nanpercentile(B, [5, 50, 95]).round(1), 'bank L', np.nanpercentile(SL, [1, 5, 50, 95]).round(1), 'R', np.nanpercentile(SR, [1, 5, 50, 95]).round(1))
    res1[name] = dict(q=qf, t=t, B=B, SL=SL, SR=SR, W=W)
pickle.dump(res1, open(cfg.work('cltab.pkl'), 'wb'))

# report per block of the listed centerlines: percentiles and fraction of points where a bank is narrower than the thresholds
blk = pr['report_block']; th1, th2 = pr['report_thresholds']
for nm in pr['report_lines']:
    if nm not in res1: raise SystemExit(f"config error: params.cl2.report_lines names '{nm}', not a centerline")
    M = res1[nm]; n = len(M['q']); idx = np.arange(n)
    for a in range(0, n, blk):
        m = (idx >= a) & (idx < a + blk)
        r = [np.nanpercentile(M[k][m], [1, 50]).round(1).tolist() for k in ('B', 'SL', 'SR', 'W')]
        print(nm, 's', a, a + blk, r, f'frac bank<{th1:g}', round(float(np.nanmean((M['SL'][a:a + blk] < th1) | (M['SR'][a:a + blk] < th1))), 2), f'bank<{th2:g}', round(float(np.nanmean((M['SL'][a:a + blk] < th2) | (M['SR'][a:a + blk] < th2))), 2))
# diagnostic plot of the first reported line: bank widths (top) and bed/total width (bottom) along s
M = res1[pr['plot_line']]
fig, ax = plt.subplots(2, 1, figsize=(16, 6))
ax[0].plot(M['SL'], lw=.4, label='bank (t<0 side)'); ax[0].plot(M['SR'], lw=.4, label='bank (t>0 side)'); ax[0].set_ylim(0, 60); ax[0].legend(); ax[0].axhline(th2, c='k', ls=':')
ax[1].plot(M['B'], lw=.5); ax[1].plot(M['W'], lw=.5); ax[1].axhline(40, c='k', ls=':'); ax[1].set_ylim(0, 250)
plt.tight_layout(); plt.savefig(cfg.work('tab.png'), dpi=75)
