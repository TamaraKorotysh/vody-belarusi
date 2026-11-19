# Low-poly terrain for the Belarus water diorama: irregular points -> Delaunay triangles, carved river channels and lake bowls.
import json, math, numpy as np
from scipy.spatial import Delaunay, cKDTree

D = json.load(open("d3.json", encoding="utf8"))
G = D["grid"]; nx, nz = G["nx"], G["nz"]; H = np.array(G["h"], dtype=np.float32).reshape(nz, nx)
# 1 map unit ≈ 6.95 km, so YS = 40 / 6950 exaggerates heights about 40 times
YS, BASE = 40 / 6950, 0.35
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
# ---- rivers: half widths, water level that only goes downhill
RW = {n: r["w"] for n, r in D["rivers"].items()}
AUTO = set(r["id"] for r in json.load(open("rivers_auto.json", encoding="utf8"))) if __import__("os").path.exists("rivers_auto.json") else set()
def half(n, d, Dl): return RW[n] * (.45 + .55 * min(1, d / Dl)) * .3
rivers_out = {}; cpts = []; cinfo = []   # channel centre points for distance queries
for n, r in D["rivers"].items():
    lines = []
    for line in r["lines"]:
        a = np.array(line, float)                      # x, z, d
        m = meters(a[:, 0], a[:, 1]); y = yof(m) - 0.12
        y = np.minimum.accumulate(y)                   # never flows uphill
        for _ in range(4): y = np.r_[y[0], (y[:-2] + y[1:-1] + y[2:]) / 3, y[-1]]
        lines.append(np.c_[a, y])
        for (x, z, d, yy) in np.c_[a, y]:
            cpts.append((x, z)); cinfo.append((half(n, d, r["D"]), yy))
    rivers_out[n] = {"w": r["w"], "D": r["D"], "lines": [[[round(v, 3) for v in p] for p in l] for l in lines]}
cpts = np.array(cpts); cinfo = np.array(cinfo); ctree = cKDTree(cpts)

# ---- lakes: level and shore
lakes_out = {}; lake_polys = []
for n, polys in D["lakes"].items():
    outer = np.array(polys[0][0], float)
    lvl = float(np.percentile(yof(meters(outer[:, 0], outer[:, 1])), 25)) - 0.05
    lakes_out[n] = {"level": round(lvl, 3), "polys": polys}
    for p in polys: lake_polys.append((np.array(p[0], float), lvl, [np.array(h, float) for h in p[1:]]))

# ---- points
pts = []
SP = 0.21   # base point spacing (0.72 before): about twice as many terrain triangles overall
gx, gz = np.meshgrid(np.arange(bx.min() - 1, bx.max() + 1, SP), np.arange(bz.min() - 1, bz.max() + 1, SP * 0.866))
gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * SP / 2
P = np.c_[gx.ravel(), gz.ravel()] + rng.uniform(-0.3, 0.3, (gx.size, 2)) * SP
dist, ci = ctree.query(P)
P = P[dist > cinfo[ci, 0] + .32]                     # channels get their own points: keep clear of each river by its own width
P = P[inside(P[:, 0], P[:, 1])]
pts.append(P)
# denser band around rivers
for n, r in rivers_out.items():
    for l in r["lines"]:
        a = np.array(l)
        for k in range(0, len(a), 1):
            x, z, d, yy = a[k]
            p0 = a[max(0, k - 1)]; p1 = a[min(len(a) - 1, k + 1)]
            tx, tz = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(tx, tz) or 1; tx /= L; tz /= L
            hw = half(n, d, r["D"])
            if k % 2 == 0:
                for off in ((0, -(hw + .16), hw + .16, -(hw + .6), hw + .6) if n not in AUTO else (0, -(hw + .14), hw + .14)):
                    pts.append(np.array([[x - tz * off, z + tx * off]]))
pts.append(resample(border, 0.7))
for ring, lvl, holes in lake_polys:
    pts.append(resample(ring, 0.45));
    for h in holes: pts.append(resample(h, 0.45))
P = np.vstack(pts)
# drop exact duplicates / near-duplicates
_, keep = np.unique(np.round(P / 0.12).astype(int), axis=0, return_index=True); P = P[np.sort(keep)]
P = P[inside(P[:, 0], P[:, 1]) | (cKDTree(border).query(P)[0] < 0.05)]
print("points", len(P))

# ---- heights
m = meters(P[:, 0], P[:, 1]); y = yof(m)
d, idx = ctree.query(P); hw = cinfo[idx, 0]; wl = cinfo[idx, 1]
bank = wl + 0.1
t = np.clip((d - hw * 0.6) / (hw + .65 - hw * 0.6), 0, 1); t = t * t * (3 - 2 * t)
carved = np.where(d < hw * 0.6, wl - 0.22, (wl - 0.22) * (1 - t) + np.maximum(y, bank) * t)
near = d < hw + .7
y = np.where(near, np.minimum(np.maximum(carved, np.where(d > hw + .2, bank, -9)), np.maximum(y, bank)), y)
y = np.where((d > hw * 0.6) & (d < hw + .3), np.maximum(y, wl + 0.06), y)
y = np.where(d < hw * 0.6, wl - 0.22, y)
for ring, lvl, holes in lake_polys:
    ins = inside(P[:, 0], P[:, 1], ring[:, 0], ring[:, 1])
    for h in holes: ins &= ~inside(P[:, 0], P[:, 1], h[:, 0], h[:, 1])
    y[ins] = lvl - 0.3
    sd = cKDTree(ring).query(P)[0]; shore = (~ins) & (sd < 0.05); y[shore] = np.maximum(lvl + 0.06, np.minimum(y[shore], lvl + 0.25))

tri = Delaunay(P).simplices
c = P[tri].mean(axis=1)
ok = inside(c[:, 0], c[:, 1])
e = np.max(np.stack([np.hypot(*(P[tri[:, a]] - P[tri[:, b]]).T) for a, b in ((0, 1), (1, 2), (2, 0))]), axis=0)
tri = tri[ok & (e < 3.5)]
print("triangles", len(tri))
out = {"pts": np.round(np.c_[P[:, 0], y, P[:, 1]], 3).ravel().tolist(), "m": np.round(m).astype(int).tolist(), 
       "border": D["border"], "borderY": np.round(yof(meters(bx, bz)), 3).tolist(),
       "rivers": rivers_out, "lakes": lakes_out, "cities": D["cities"]}
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
        Q = np.vstack(bp + ([ip] if len(ip) else []))
        if len(Q) < 4: continue   # a sliver of a multipolygon: nothing to triangulate
        try: tr = Delaunay(Q).simplices
        except Exception: continue   # a flat sliver of a multipolygon
        cc = Q[tr].mean(axis=1)
        ok = inside(cc[:, 0], cc[:, 1], ring[:, 0], ring[:, 1])
        for h in holes: ok &= ~inside(cc[:, 0], cc[:, 1], h[:, 0], h[:, 1])
        base = sum(len(a) for a in allp); allp.append(Q); alltri.append(tr[ok] + base)
    if not allp: drop.append(n); continue   # nothing big enough to draw
    Q = np.vstack(allp); T = np.vstack(alltri)
    lk["pts"] = np.round(Q, 3).ravel().tolist(); lk["tri"] = T.ravel().tolist(); del lk["polys"]
    print(n, len(Q), len(T))
for n in drop: print("lake too small to draw:", n); lakes_out.pop(n)
out["lakes"] = lakes_out
s = json.dumps(out, ensure_ascii=False, separators=(",", ":")); open("lp.json", "w", encoding="utf8").write(s); print("bytes", len(s))
