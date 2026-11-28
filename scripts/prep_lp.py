# Low-poly terrain for the Belarus water diorama: irregular points -> Delaunay triangles, carved river channels and lake bowls.
import json, math, numpy as np
from scipy.spatial import Delaunay, cKDTree

D = json.load(open("d3.json", encoding="utf8"))
G = D["grid"]; nx, nz = G["nx"], G["nz"]; H = np.array(G["h"], dtype=np.float32).reshape(nz, nx)
# 1 map unit ≈ 6.95 km, so YS = 20 / 6950 exaggerates heights 20 times (lp_template.html reads it back as L.ys)
YS, BASE = 20 / 6950, 0.35
def meters(x, z):
    fx = (np.asarray(x) - G["x0"]) / G["step"]; fz = (np.asarray(z) - G["z0"]) / G["step"]
    i = np.clip(np.floor(fx).astype(int), 0, nx - 2); j = np.clip(np.floor(fz).astype(int), 0, nz - 2)
    a = np.clip(fx - i, 0, 1); b = np.clip(fz - j, 0, 1)
    return H[j, i] * (1 - a) * (1 - b) + H[j, i + 1] * a * (1 - b) + H[j + 1, i] * (1 - a) * b + H[j + 1, i + 1] * a * b
def yof(m): return BASE + np.maximum(0, m - 75) * YS

border = np.array(D["border"], dtype=float)
bx, bz = border[:, 0], border[:, 1]
def inside(xs, zs, px=bx, pz=bz):
    xs = np.asarray(xs, float); zs = np.asarray(zs, float); c = np.zeros(xs.shape, bool)
    x2, z2 = np.roll(px, -1), np.roll(pz, -1)
    for i in range(len(px)):
        dz = z2[i] - pz[i]
        if dz == 0: continue
        c ^= ((pz[i] > zs) != (z2[i] > zs)) & (xs < (x2[i] - px[i]) * (zs - pz[i]) / dz + px[i])
    return c
def resample(ring, step, closed=True):
    ring = np.asarray(ring, float)
    if closed: ring = np.vstack([ring, ring[:1]])
    seg = np.hypot(*np.diff(ring, axis=0).T); L = np.r_[0, np.cumsum(seg)]
    s = np.arange(0, L[-1], step)
    return np.c_[np.interp(s, L, ring[:, 0]), np.interp(s, L, ring[:, 1])]

rng = np.random.default_rng(5)

# ---- landmarks (data/landmarks.json, from scripts/fetch_landmarks.py): the Mikashevichi granite quarry, the Soligorsk salt heaps
def proj(lon, lat): K, CX, CY = 16, 28.0, 53.7; return ((lon - CX) * math.cos(math.radians(CY)) * K, (CY - lat) * K)
import os
LM = json.load(open("landmarks.json", encoding="utf8")) if os.path.exists("landmarks.json") else {"marks": []}
if LM.get("town") and not any(c[0] == LM["town"][0] for c in D["cities"]):
    n_, lon_, lat_, be_ = LM["town"]; D["cities"].append([n_, *[round(v, 2) for v in proj(lon_, lat_)], 3, be_])
for mk in LM["marks"]:
    mk["xz"] = np.array([proj(lo, la) for lo, la in mk["ring"]])
    mk["rim"] = resample(mk["xz"], .02 if mk["kind"] == "quarry" else .015)
# ---- rivers: widths as on a physical map of Belarus, water level that only goes downhill
# 1 map unit = 6.95 km. Full width at the mouth: Dnieper about 2.2 km, the other big rivers 1.4-1.9 km, their main tributaries
# 0.6-1.1 km, small rivers 0.3-0.7 km by length (a map line, not the real 50-400 m, which would be invisible on the overview).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mouths import lead_into
AUTO = set(r["id"] for r in json.load(open("rivers_auto.json", encoding="utf8"))) if os.path.exists("rivers_auto.json") else set()
# the lower Horyn at Davyd-Haradok with the Vetlitsa and the Lva is drawn by hand in lp_template.html from these exact lines: leave them as they are
KEEP = {"Горынь", "Ветлица", "Льва"}
MOUTH_OF = lead_into(D["rivers"], D["lakes"], D["border"], skip=KEEP)     # every other tributary now reaches the middle of its recipient
KM = 6.95
def full_km(n, r):
    if n in AUTO: return float(np.clip(.22 + .029 * r["D"], .28, .7))
    if r["w"] < .29: return .4                                   # canals
    return .42 + (r["w"] - .3) * 1.87
HM = {n: full_km(n, r) / KM / 2 for n, r in D["rivers"].items()}   # half width at the mouth, map units
HMIN = .016                                                     # narrowest water: about 220 m across
def taper(d, Dl): return .35 + .65 * min(1, d / Dl)
def half(n, d, Dl): return max(HMIN, HM[n] * taper(d, Dl))
# a tributary's mouth is narrower than the river it flows into
for n, (t, kind) in MOUTH_OF.items():
    if kind != "river": continue
    e = np.array(D["rivers"][n]["lines"][max(range(len(D["rivers"][n]["lines"])), key=lambda i: D["rivers"][n]["lines"][i][-1][2])][-1][:2])
    pts = [p for l in D["rivers"][t]["lines"] for p in l]; q = min(pts, key=lambda p: (p[0] - e[0]) ** 2 + (p[1] - e[1]) ** 2)
    rec = half(t, q[2], D["rivers"][t]["D"])
    HM[n] = max(HM[n] * .6, min(HM[n], .7 * rec))
rivers_out = {}; cpts = []; cinfo = []   # channel centre points for distance queries
for n, r in D["rivers"].items():
    lines = []
    for line in r["lines"]:
        a = np.array(line, float)                      # x, z, d
        m = meters(a[:, 0], a[:, 1]); y = yof(m) - 0.12
        y = np.minimum.accumulate(y)                   # never flows uphill
        for _ in range(4): y = np.r_[y[0], (y[:-2] + y[1:-1] + y[2:]) / 3, y[-1]]
        lines.append(np.c_[a, y])
    rivers_out[n] = {"lines": lines}
# at the mouth the tributary's water comes down to its recipient's level (a lake's surface or the river's water there)
LAKE_LVL = {}
for n, polys in D["lakes"].items():
    outer = np.array(polys[0][0], float); LAKE_LVL[n] = float(np.percentile(yof(meters(outer[:, 0], outer[:, 1])), 25)) - 0.05
# ---- lakes a river flows through (Palik and Medzozol on the Berezina, the Vileyka, Soligorsk, Chigirinka... reservoirs).
# The lake's surface is the river's water where it leaves the lake, the river comes down to it before the lake, and inside the
# lake there is no ribbon: the river's line is cut a little inside each shore (CUTS, applied when lp.json is written) and the lake's
# water gets a corridor as wide as the river along its course (CORR), so a lake narrower than the river still takes it whole.
CUTS = {}; CORR = {}
def river_half(n, d, Dn): return max(HMIN, HM[n] * (.35 + .65 * min(1, d / Dn)))   # riverHalfWidth() in the template
for ln, polys in D["lakes"].items():
    for poly in polys:
        ring = np.array(poly[0], float); holes = [np.array(h, float) for h in poly[1:]]; lo, hi = ring.min(0) - .05, ring.max(0) + .05
        for n, ro in rivers_out.items():
            Dn = max(l[-1, 2] for l in ro["lines"])
            for li, a in enumerate(ro["lines"]):
                if not ((a[:, :2] > lo) & (a[:, :2] < hi)).all(1).any(): continue
                S = np.r_[0, np.cumsum(np.hypot(*np.diff(a[:, :2], axis=0).T))]
                s = np.arange(0, S[-1], .01); f = np.c_[[np.interp(s, S, a[:, c]) for c in range(4)]].T
                ins = inside(f[:, 0], f[:, 1], ring[:, 0], ring[:, 1])
                for h in holes: ins &= ~inside(f[:, 0], f[:, 1], h[:, 0], h[:, 1])
                if not ins.any() or ins[0] or ins[-1]: continue        # a source or a mouth in the lake: not flowing through
                # stretches inside the lake; a short way out and back in (a narrow neck of the lake) counts as inside
                e = np.flatnonzero(np.diff(ins.astype(int))); runs = [[s[e[k] + 1], s[e[k + 1]]] for k in range(0, len(e), 2)]
                merged = [runs[0]]
                for r0, r1 in runs[1:]:
                    if r0 - merged[-1][1] < .3: merged[-1][1] = r1
                    else: merged.append([r0, r1])
                merged = [r for r in merged if r[1] - r[0] > .1]       # a river just touching a corner of the lake stays as it is
                if not merged: continue
                lvl = float(np.interp(merged[-1][1], s, f[:, 3]))
                LAKE_LVL[ln] = min(LAKE_LVL.get(ln, 9), lvl) if ln in CORR else lvl
                for r0, r1 in merged:
                    inn = (S >= r0) & (S <= r1); a[inn, 3] = lvl
                    up = S < r0; a[up, 3] = np.minimum(a[up, 3], lvl + (r0 - S[up]) / .11 * .012)   # eases down to the lake, never a step
                    m_ = (s >= r0) & (s <= r1)
                    CORR.setdefault(ln, []).append(np.c_[f[m_, :2], [river_half(n, d, Dn) + .012 for d in f[m_, 2]]])
                CUTS.setdefault((n, li), []).extend(merged)
                print("flows through", ln, ":", n, [[round(v, 2) for v in r] for r in merged], "level", round(lvl, 3))
for n in sorted(MOUTH_OF, key=lambda k: -D["rivers"][k]["D"]):
    t, kind = MOUTH_OF[n]; Ls = rivers_out[n]["lines"]; li = max(range(len(Ls)), key=lambda i: Ls[i][-1, 2]); a = Ls[li]
    if kind == "lake": ty = LAKE_LVL[t] + .01
    else:
        q = np.vstack(rivers_out[t]["lines"]); ty = q[np.argmin((q[:, 0] - a[-1, 0]) ** 2 + (q[:, 1] - a[-1, 1]) ** 2), 3] + .005
    k = np.arange(len(a))[::-1]                        # points back from the mouth
    a[:, 3] = np.minimum(a[:, 3], ty + k * .012)       # eases down over the last stretch, never a step
for n, r in D["rivers"].items():
    lines = rivers_out[n]["lines"]
    for a in lines:
        # distance queries need the centre line, not just its vertices 1 km apart: the channels are only a few hundred metres wide
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(a[:, :2], axis=0).T))]
        s = np.arange(0, L[-1] + 1e-9, .02) if L[-1] > 0 else np.array([0.])
        fine = np.c_[[np.interp(s, L, a[:, c]) for c in range(4)]].T
        for (x, z, d, yy) in fine:
            cpts.append((x, z)); cinfo.append((half(n, d, r["D"]), yy))
    rivers_out[n] = {"w": r["w"], "hm": round(HM[n], 4), "D": round(max(l[-1, 2] for l in lines), 3),
                     "lines": [[[round(v, 3) for v in p] for p in l] for l in lines]}
    r["D"] = rivers_out[n]["D"]
cpts = np.array(cpts); cinfo = np.array(cinfo); ctree = cKDTree(cpts)

# ---- lakes: level and shore
lakes_out = {}; lake_polys = []
for n, polys in D["lakes"].items():
    outer = np.array(polys[0][0], float)
    lvl = LAKE_LVL[n]                                  # the shore heights, or the river where a river flows through
    lakes_out[n] = {"level": round(lvl, 3), "polys": polys}
    for p in polys: lake_polys.append((np.array(p[0], float), lvl, [np.array(h, float) for h in p[1:]]))

# ---- points
pts = []
SP = 0.165   # base point spacing (0.72 before): about twice as many terrain triangles overall
gx, gz = np.meshgrid(np.arange(bx.min() - 1, bx.max() + 1, SP), np.arange(bz.min() - 1, bz.max() + 1, SP * 0.866))
gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * SP / 2
P = np.c_[gx.ravel(), gz.ravel()] + rng.uniform(-0.3, 0.3, (gx.size, 2)) * SP
dist, ci = ctree.query(P)
P = P[dist > cinfo[ci, 0] + .24]                     # channels get their own points: keep clear of each river by its own width
P = P[inside(P[:, 0], P[:, 1])]
pts.append(P)
# ---- river channels: the terrain follows the ribbon lp_template.html draws.
# Vertices exactly on both edges of the ribbon (just below its water), on every row of the ribbon and between rows, the bed on
# each row, the bank right outside the edge and the valley side further out. These points skip the near-duplicate thinning below:
# at 0.12 apart it used to drop 39% of the bed and bank points of narrow rivers, and the triangles left then lay across the water
# at the height of the banks. Without vertices on the edge, a bed-to-bank triangle of a wide river also rose above the water
# before the edge of the ribbon.
RP, RK, RW = [], [], []     # point, kind (1 bed, 2 ribbon edge, 3 bank, 4 valley side), water level of its ribbon there
def ribbon_half(r, d): return max(HMIN, r["hm"] * (.35 + .65 * min(1, d / r["D"])))   # riverHalfWidth() in the template
for n, r in rivers_out.items():
    if n in KEEP: continue                      # the template draws and carves these by hand
    for l in r["lines"]:
        a = np.array(l); rows = a[[i for i in range(len(a)) if i % 2 == 0 or i == len(a) - 1]]   # riverRows() in the template
        nb = len(rows)
        if nb < 2: continue
        ix = np.arange(nb); t = rows[np.minimum(ix + 1, nb - 1), :2] - rows[np.maximum(ix - 1, 0), :2]
        t /= np.maximum(np.hypot(*t.T), 1e-9)[:, None]; nrm = np.c_[-t[:, 1], t[:, 0]]
        E = np.array([ribbon_half(r, p[2]) for p in rows]) + .012          # drawnHalf()
        for i in range(nb):
            RP.append(rows[i, :2]); RK.append(1); RW.append(rows[i, 3])                  # the bed
            if i % 2 == 0:
                for s in (-1, 1): RP.append(rows[i, :2] + s * nrm[i] * (E[i] + .12)); RK.append(4); RW.append(rows[i, 3])
            if i == nb - 1: break
            seg = np.hypot(*(rows[i + 1, :2] - rows[i, :2]))
            k = max(2, math.ceil(seg / max(.1, 3 * max(E[i], E[i + 1]))))   # edge points on the rows and between them, a little further apart than the ribbon is wide
            for j in range(k):
                f = j / k; wl_ = rows[i, 3] * (1 - f) + rows[i + 1, 3] * f
                nr = nrm[i] * (1 - f) + nrm[i + 1] * f; nr /= np.hypot(*nr) or 1
                for s in (-1, 1):
                    e = (rows[i, :2] + s * nrm[i] * E[i]) * (1 - f) + (rows[i + 1, :2] + s * nrm[i + 1] * E[i + 1]) * f   # on the ribbon's straight edge
                    RP.append(e); RK.append(2); RW.append(wl_)
                    RP.append(e + s * nr * .016); RK.append(3); RW.append(wl_)
        for s in (-1, 1): RP.append(rows[-1, :2] + s * nrm[-1] * E[-1]); RK.append(2); RW.append(rows[-1, 3])
RP = np.array(RP); RK = np.array(RK); RW = np.array(RW)
_, keep = np.unique(np.round(RP / .004).astype(int), axis=0, return_index=True); keep = np.sort(keep)   # only true duplicates
RP, RK, RW = RP[keep], RK[keep], RW[keep]
# the hand-drawn lower Horyn and its tributaries keep the old sparse band
for n in KEEP:
    r = rivers_out[n]
    for l in r["lines"]:
        a = np.array(l)
        for k in range(0, len(a), 1):
            x, z, d, yy = a[k]
            p0 = a[max(0, k - 1)]; p1 = a[min(len(a) - 1, k + 1)]
            tx, tz = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(tx, tz) or 1; tx /= L; tz /= L
            hw = half(n, d, r["D"])
            if k % 2 == 0:
                for off in (0, -(hw + .025), hw + .025) + ((-(hw + .13), hw + .13) if k % 4 == 0 else ()):   # bed, the bank right at the water's edge, the valley side
                    pts.append(np.array([[x - tz * off, z + tx * off]]))
pts.append(resample(border, 0.7))
# lake shores: points close along the shore itself, a row just outside it (still at shore height) and one a little further out,
# and a row just inside under the water. Like the channel points they skip the near-duplicate thinning: with the shore alone
# every 0.45, the bed of the lake and the land beyond were joined by long steep slivers that stood out around every lake.
LP = []
for ring, lvl, holes in lake_polys:
    for rg in [ring] + holes:
        e = resample(rg, .09)
        if len(e) < 4: continue
        tg = np.roll(e, -1, axis=0) - np.roll(e, 1, axis=0); nr = np.c_[-tg[:, 1], tg[:, 0]]; nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-12
        probe = e + nr * .02; wet = inside(probe[:, 0], probe[:, 1], ring[:, 0], ring[:, 1])
        for h in holes: wet &= ~inside(probe[:, 0], probe[:, 1], h[:, 0], h[:, 1])
        nr[wet] *= -1                                   # every normal points out of the water
        LP += [e, e + nr * .035, (e + nr * .13)[::2], (e - nr * .05)[::2]]
LP = np.vstack(LP) if LP else np.zeros((0, 2))
_, keep = np.unique(np.round(LP / .03).astype(int), axis=0, return_index=True); LP = LP[np.sort(keep)]
if len(RP): LP = LP[cKDTree(RP).query(LP)[0] > .02]   # the river channels win where a river meets a lake
for mk in LM["marks"]:
    if mk["kind"] != "quarry": continue
    for i, a in enumerate(pts): pts[i] = a[~inside(a[:, 0], a[:, 1], mk["xz"][:, 0], mk["xz"][:, 1]) & (cKDTree(mk["rim"]).query(a)[0] > .03)]
    ok = ~inside(RP[:, 0], RP[:, 1], mk["xz"][:, 0], mk["xz"][:, 1]) & (cKDTree(mk["rim"]).query(RP)[0] > .03); RP, RK, RW = RP[ok], RK[ok], RW[ok]
    if len(LP): LP = LP[~inside(LP[:, 0], LP[:, 1], mk["xz"][:, 0], mk["xz"][:, 1]) & (cKDTree(mk["rim"]).query(LP)[0] > .03)]
P = np.vstack(pts)
# drop exact duplicates / near-duplicates (not the channel or shore points, see above), and anything sitting right on one of those
_, keep = np.unique(np.round(P / 0.12).astype(int), axis=0, return_index=True); P = P[np.sort(keep)]
P = P[cKDTree(RP).query(P)[0] > .006]
if len(LP): P = np.vstack([P[cKDTree(LP).query(P)[0] > .03], LP])
KIND = np.r_[np.zeros(len(P), int), RK]; WL = np.r_[np.zeros(len(P)), RW]; P = np.vstack([P, RP])
QRIM = [mk["rim"] for mk in LM["marks"] if mk["kind"] == "quarry"]   # the quarry rim exactly: the template cuts the terrain there and fits the pit in
if QRIM: P = np.vstack([P] + QRIM); n_ = sum(len(q) for q in QRIM); KIND = np.r_[KIND, np.zeros(n_, int)]; WL = np.r_[WL, np.zeros(n_)]
ok = inside(P[:, 0], P[:, 1]) | (cKDTree(border).query(P)[0] < 0.05); P, KIND, WL = P[ok], KIND[ok], WL[ok]
print("points", len(P), "of them on river channels", int((KIND > 0).sum()))

# ---- heights
m = meters(P[:, 0], P[:, 1]); y = yof(m)
d, idx = ctree.query(P); hw = cinfo[idx, 0]; wl = cinfo[idx, 1]
bank = wl + 0.06
E = hw + .012                                        # edge of the drawn water ribbon (see lp_template.html)
t = np.clip((d - E) / .4, 0, 1); t = t * t * (3 - 2 * t)
carved = np.where(d < hw * 0.6, wl - 0.22, bank * (1 - t) + np.maximum(y, bank) * t)
near = d < E + .45
y = np.where(near, np.minimum(np.maximum(carved, np.where(d > E + .008, bank, -9)), np.maximum(y, bank)), y)
y = np.where((d > E + .008) & (d < hw + .2), np.maximum(y, bank), y)   # banks start right beyond the ribbon
y = np.where(d < hw * 0.6, wl - 0.22, y)
for ring, lvl, holes in lake_polys:
    ins = inside(P[:, 0], P[:, 1], ring[:, 0], ring[:, 1])
    for h in holes: ins &= ~inside(P[:, 0], P[:, 1], h[:, 0], h[:, 1])
    y[ins] = lvl - 0.3
    sd = cKDTree(np.vstack([resample(rg, .01) for rg in [ring] + holes])).query(P)[0]; shore = (~ins) & (sd < 0.05);   # distance to the shore line, not just its vertices y[shore] = np.maximum(lvl + 0.06, np.minimum(y[shore], lvl + 0.25))
# last word: under a river's ribbon the ground is always below its water, even where a lake bowl or shore lifted it
y = np.where(d < hw * 0.6, np.minimum(y, wl - 0.22), y)
y = np.where(d < E, np.minimum(y, wl - 0.03), y)
# the ribbon's own vertices: its edge just under the water (the water surface wobbles by up to .025), its bed deep
y = np.where(KIND == 2, np.minimum(y, WL - 0.03), y)
y = np.where(KIND == 1, np.minimum(y, WL - 0.22), y)
# and any point under any ribbon, not just the nearest river's: banks of a tributary inside its recipient, two rivers side by side
for i, near_ in enumerate(ctree.query_ball_point(P, .2)):
    if not near_: continue
    near_ = np.array(near_); dd = np.hypot(*(cpts[near_] - P[i]).T); under = dd < cinfo[near_, 0] + .012 - 1e-3
    if under.any(): y[i] = min(y[i], cinfo[near_[under], 1].min() - 0.03)

# ---- landmark meshes, built on iso-distance contours inside the outline: a terraced pit and salt heaps.
# The pit has absolute heights; a heap has heights above the ground, the template adds the terrain under it.
def contour(ring, d, step):
    """points about d inside the outline: the dense edge pushed inward along its normals, kept where the true distance is d"""
    e = resample(ring, step * .5); t = np.roll(e, -1, axis=0) - np.roll(e, 1, axis=0); nrm = np.c_[-t[:, 1], t[:, 0]]
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    out = []
    for sgn in (1, -1):
        q = e + sgn * d * nrm; ok = inside(q[:, 0], q[:, 1], ring[:, 0], ring[:, 1])
        if ok.mean() > .5: out = q[ok]; break
    if not len(out): return np.zeros((0, 2))
    dd = cKDTree(resample(ring, .003)).query(out)[0]; out = out[np.abs(dd - d) < .2 * d + .002]
    if len(out) < 3: return np.zeros((0, 2))
    keep = [0]                                                  # thin to the step
    tr = cKDTree(out); taken = np.zeros(len(out), bool); taken[0] = True
    for i in range(1, len(out)):
        if not any(taken[j] for j in tr.query_ball_point(out[i], step * .8)): taken[i] = True
    return out[taken]
marks_out = []; PIT = []
for mk in LM["marks"]:
    ring, rim = mk["xz"], mk["rim"]; HM_ = mk["m"] * YS; edge = cKDTree(resample(ring, .003))
    if mk["kind"] == "quarry":
        # an amphitheatre of benches down to a floor 800 m in: seven benches about 100 m wide with short walls between them;
        # the depth (about 150 m) is exaggerated only 5 times here, the relief's 20 would make it a shaft
        NB, W, A = 7, .0143, .0045; HM_ = mk["m"] * 5 / 6950
        lv = [(0., 0.)] + [lev for k in range(NB) for lev in ((k * W + A, (k + 1) / NB), ((k + 1) * W, (k + 1) / NB))][:-1]
    else:
        lv = [(0., 0.)]                                          # a heap is a pile: straight slopes up to a sharp crest along its middle
    rings_ = [(rim, 0.)] + [(contour(ring, d, .007), f) for d, f in lv[1:]]
    x0, z0 = ring.min(axis=0); x1, z1 = ring.max(axis=0); sp = .018
    gx, gz = np.meshgrid(np.arange(x0, x1, sp), np.arange(z0, z1, sp * .866)); gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * sp / 2
    ip = np.c_[gx.ravel(), gz.ravel()] + rng.uniform(-.2, .2, (gx.size, 2)) * sp
    if mk["kind"] == "heap": sp = .011
    if mk["kind"] == "heap":
        gx, gz = np.meshgrid(np.arange(x0, x1, sp), np.arange(z0, z1, sp * .866)); gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * sp / 2
        ip = np.c_[gx.ravel(), gz.ravel()] + rng.uniform(-.2, .2, (gx.size, 2)) * sp
    ip = ip[inside(ip[:, 0], ip[:, 1], ring[:, 0], ring[:, 1])]; ip = ip[edge.query(ip)[0] > lv[-1][0] + .008]
    Q = np.vstack([r for r, f in rings_] + [ip]); F = np.concatenate([np.full(len(r), f) for r, f in rings_] + [np.full(len(ip), 1.)])
    tr = Delaunay(Q).simplices; cc = Q[tr].mean(axis=1); tr = tr[inside(cc[:, 0], cc[:, 1], ring[:, 0], ring[:, 1])]
    if mk["kind"] == "quarry":
        ry = yof(meters(rim[:, 0], rim[:, 1])); _, ni = cKDTree(rim).query(Q, k=8); base = ry[ni].mean(axis=1); base[:len(rim)] = ry
        yy = base - F * HM_; PIT.append(ry)
        marks_out.append({"kind": "quarry", "ru": mk["ru"], "be": mk["be"], "ring": np.round(ring, 3).tolist(), "y0": round(float(ry.mean()), 3), "d": round(HM_, 3),
                          "pts": np.round(np.c_[Q[:, 0], yy, Q[:, 1]], 3).ravel().tolist(), "tri": tr.ravel().tolist()})
    else:
        dq = edge.query(Q)[0]; dq[:len(rim)] = 0; top = dq.max()
        # the crest rises and dips into a few peaks along the ridge, as the stackers pour them
        peak = .8 + .2 * np.cos(Q[:, 0] * 41 + 1.3) * np.cos(Q[:, 1] * 37 + .4)
        hh = HM_ * np.minimum(dq / (top * .92), 1) * peak
        marks_out.append({"kind": "heap", "ru": mk["ru"], "be": mk["be"], "ring": np.round(ring, 3).tolist(), "h": round(HM_, 3),
                          "pts": np.round(np.c_[Q[:, 0], hh, Q[:, 1]], 3).ravel().tolist(), "tri": tr.ravel().tolist()})
# the quarry rim points close the terrain at the pit's own rim heights; the template cuts the triangles spanned by rim points alone
o = len(P) - sum(len(r) for r in QRIM); pit_range = [o, sum(len(r) for r in QRIM)]
for ry in PIT: y[o:o + len(ry)] = ry; o += len(ry)

tri = Delaunay(P).simplices
c = P[tri].mean(axis=1)
ok = inside(c[:, 0], c[:, 1])
e = np.max(np.stack([np.hypot(*(P[tri[:, a]] - P[tri[:, b]]).T) for a, b in ((0, 1), (1, 2), (2, 0))]), axis=0)
tri = tri[ok & (e < 3.5)]
print("triangles", len(tri))
# a river's line is cut a little inside each shore of a lake it flows through: the lake's water carries it there
for (n, li), runs in CUTS.items():
    a = np.array(rivers_out[n]["lines"][li]); S = np.r_[0, np.cumsum(np.hypot(*np.diff(a[:, :2], axis=0).T))]
    at = lambda u: [round(float(np.interp(u, S, a[:, c])), 3) for c in range(4)]
    pieces = []; start = 0.
    for r0, r1 in sorted(runs):
        pieces.append((start, r0 + .03)); start = r1 - .03
    pieces.append((start, S[-1]))
    rivers_out[n]["cut"] = rivers_out[n].get("cut", []) + [li]
    rivers_out[n]["lines"][li] = [[at(u0)] + [list(p) for p, sv in zip(rivers_out[n]["lines"][li], S) if u0 < sv < u1] + [at(u1)] for u0, u1 in pieces]
for n, ro in rivers_out.items():
    if "cut" not in ro: continue
    ls = []
    for li, l in enumerate(ro["lines"]): ls += l if li in ro["cut"] else [l]
    ro["lines"] = ls; del ro["cut"]
out = {"pts": np.round(np.c_[P[:, 0], y, P[:, 1]], 3).ravel().tolist(), "m": np.round(m).astype(int).tolist(), 
       "border": D["border"], "borderY": np.round(yof(meters(bx, bz)), 3).tolist(),
       "rivers": rivers_out, "lakes": lakes_out, "cities": D["cities"], "ys": YS, "marks": marks_out, "pit": pit_range}
s = json.dumps(out, ensure_ascii=False, separators=(",", ":")); open("lp.json", "w", encoding="utf8").write(s); print("bytes", len(s))

# ---- lake water surfaces: their own irregular triangles
drop = []
for n, lk in lakes_out.items():
    allp = []; alltri = []
    for poly in lk["polys"]:
        ring = np.array(poly[0], float); holes = [np.array(h, float) for h in poly[1:]]
        per = float(np.sum(np.hypot(*np.diff(np.vstack([ring, ring[:1]]), axis=0).T))); stp = min(0.22, per / 12)   # small lakes still get a dozen shore points
        bp = [resample(ring, stp)] + [resample(h, stp) for h in holes]
        x0, z0 = ring.min(axis=0); x1, z1 = ring.max(axis=0)
        gx, gz = np.meshgrid(np.arange(x0, x1, .3), np.arange(z0, z1, .26))
        ip = np.c_[gx.ravel(), gz.ravel()] + rng.uniform(-.09, .09, (gx.size, 2))
        ins = inside(ip[:, 0], ip[:, 1], ring[:, 0], ring[:, 1])
        for h in holes: ins &= ~inside(ip[:, 0], ip[:, 1], h[:, 0], h[:, 1])
        ip = ip[ins]
        if len(ip): ip = ip[cKDTree(np.vstack(bp)).query(ip)[0] > .14]
        # a river flowing through: the water also covers its course as wide as the river (see CORR above)
        cor = [c for c in CORR.get(n, []) if ((c[:, :2] > ring.min(0) - .3) & (c[:, :2] < ring.max(0) + .3)).all(1).any()]
        ce = []
        for c in cor:
            if len(c) < 2: continue
            tg = np.gradient(c[:, :2], axis=0); tg /= np.maximum(np.hypot(*tg.T), 1e-9)[:, None]; nr = np.c_[-tg[:, 1], tg[:, 0]]
            k = np.unique(np.r_[np.arange(0, len(c), max(1, int(c[:, 2].mean() / .01))), len(c) - 1])   # about as far apart as the river is half wide
            ce += [c[k, :2] + nr[k] * c[k, 2:3] * .999, c[k, :2] - nr[k] * c[k, 2:3] * .999, c[k[::2], :2]]
        Q = np.vstack(bp + ([ip] if len(ip) else []) + ce)
        if len(Q) < 4: continue   # a sliver of a multipolygon: nothing to triangulate
        try: tr = Delaunay(Q).simplices
        except Exception: continue   # a flat sliver of a multipolygon
        cc = Q[tr].mean(axis=1)
        ok = inside(cc[:, 0], cc[:, 1], ring[:, 0], ring[:, 1])
        for h in holes: ok &= ~inside(cc[:, 0], cc[:, 1], h[:, 0], h[:, 1])
        if cor:
            C = np.vstack(cor); dc, ic = cKDTree(C[:, :2]).query(cc); ok |= dc < C[ic, 2]
        base = sum(len(a) for a in allp); allp.append(Q); alltri.append(tr[ok] + base)
    if not allp: drop.append(n); continue   # nothing big enough to draw
    Q = np.vstack(allp); T = np.vstack(alltri)
    lk["pts"] = np.round(Q, 3).ravel().tolist(); lk["tri"] = T.ravel().tolist(); del lk["polys"]
    if n in CORR: lk["flow"] = np.round(np.vstack([c[::5] for c in CORR[n]]), 3).ravel().tolist()   # the river's course across: x, z, half width
    print(n, len(Q), len(T))
for n in drop: print("lake too small to draw:", n); lakes_out.pop(n)
out["lakes"] = lakes_out
s = json.dumps(out, ensure_ascii=False, separators=(",", ":")); open("lp.json", "w", encoding="utf8").write(s); print("bytes", len(s))
