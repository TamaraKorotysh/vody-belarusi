# Where each river flows into, and leading every tributary right into its recipient.
# prep_lp.py uses it so that on the thin, map-scale rivers no tributary stops short of the river or lake it flows into.
#  1. recipient: the river or lake named in rivers_auto.json / the cards (if it is near), else the nearest bigger river or a lake;
#  2. if OpenStreetMap pieces of the same river were left out (a gap where it runs through a pond or a data hole), they are added back from data/tiles;
#  3. what is still missing (usually under 1-2 km) is bridged by a short smooth curve to the recipient's centre line.
# Rivers that leave Belarus (their mouth is near the border and nothing is there) are left as they are.
import json, os, re, glob, math
import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 16; CX, CY = 28.0, 53.7; KX = math.cos(math.radians(53.7))
def P(lon, lat): return ((lon - CX) * KX * K, (CY - lat) * K)

def named_mouths(rivers, lakes):
    """river name -> recipient name (a key of rivers or lakes), from the data, where it can be read."""
    out = {}
    path = os.path.join(ROOT, "data", "rivers_auto.json")
    if os.path.exists(path):
        for a in json.load(open(path, encoding="utf8")):
            if a.get("mouth"): out[a["id"]] = a["mouth"]
    for f in ("cards.js", "cards2.js", "cards_canals.js"):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p): continue
        s = open(p, encoding="utf8").read()
        for m in re.finditer(r'"([^"]+)":\s*\{[^{}]*?to:\["([^"]*)"', s):
            out.setdefault(m.group(1), m.group(2))
    res = {}
    keys = sorted(list(rivers) + list(lakes), key=len, reverse=True)
    for n, t in out.items():
        if n not in rivers: continue
        t = t.replace("Река ", "").replace("Рака ", "").replace("озеро ", "").replace(" озеро", "")
        head = re.split(r"[,—(]", t)[0].strip()
        hit = next((k for k in keys if k == head), None) or next((k for k in keys if k != n and (head.startswith(k) or k.startswith(head + " ("))), None)
        if "Заславское" in t and "Заславское водохранилище" in lakes: hit = "Заславское водохранилище"
        if hit and hit != n: res[n] = hit
    return res

def _tile_ways():
    """OpenStreetMap river ways by Russian name, in map units."""
    by = {}
    for fn in glob.glob(os.path.join(ROOT, "data", "tiles", "r_*.json")):
        for e in json.load(open(fn, encoding="utf8"))["elements"]:
            if e.get("type") != "way" or not e.get("geometry"): continue
            n = e.get("tags", {}).get("name:ru") or e.get("tags", {}).get("name")
            by.setdefault(n, {})[e["id"]] = np.array([P(p["lon"], p["lat"]) for p in e["geometry"]])
    return by

def _even(q, step=.15):
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(q, axis=0).T))]
    if L[-1] < step: return q
    t = np.linspace(0, L[-1], max(2, int(L[-1] / step) + 1))
    return np.c_[np.interp(t, L, q[:, 0]), np.interp(t, L, q[:, 1])]

def _curve(a, ta, b, steps_len=.15):
    """smooth curve from a (leaving along unit tangent ta) to b"""
    g = float(np.hypot(*(b - a)))
    if g < 1e-6: return np.zeros((0, 2))
    tb = (b - a) / g
    m0 = ta * g * .6; m1 = tb * g * .6
    n = max(2, int(g / steps_len) + 1); s = np.linspace(0, 1, n)[1:, None]
    h00 = 2 * s**3 - 3 * s**2 + 1; h10 = s**3 - 2 * s**2 + s; h01 = -2 * s**3 + 3 * s**2; h11 = s**3 - s**2
    return h00 * a + h10 * m0 + h01 * b + h11 * m1

def lead_into(rivers, lakes, border, log=print, skip=()):
    """rivers: name -> {"w","D","lines":[[x,z,d],...]} (changed in place: lines extended to the recipient).
    lakes: name -> list of polygons (rings of [x,z]). Returns name -> (recipient, kind) for every river that has one."""
    named = named_mouths(rivers, lakes)
    B = cKDTree(np.asarray(border, float))
    rp = {n: np.array([p[:2] for l in r["lines"] for p in l], float) for n, r in rivers.items()}
    rt = {n: cKDTree(a) for n, a in rp.items()}
    lr = {n: [np.asarray(poly[0], float) for poly in polys] for n, polys in lakes.items()}
    lp = {n: np.vstack(v) for n, v in lr.items()}
    lt = {n: cKDTree(a) for n, a in lp.items()}
    lcen = {n: a.mean(axis=0) for n, a in lp.items()}
    ways = None
    def dist_to(t, x):
        if t in rt: return float(rt[t].query(x)[0])
        return float(lt[t].query(x)[0])
    def mouth_of(n):
        r = rivers[n]; li = max(range(len(r["lines"])), key=lambda i: r["lines"][i][-1][2])
        return li, np.array(r["lines"][li][-1][:2], float)
    out = {}; report = {"ok": 0, "bridged": 0, "from_tiles": 0, "abroad": 0, "none": []}
    # big rivers first, so a tributary meets its recipient's final line
    for n in sorted(rivers, key=lambda k: -rivers[k]["D"]):
        if n in skip: continue
        r = rivers[n]; li, e = mouth_of(n)
        cand = []
        t = named.get(n)
        if t and dist_to(t, e) < 3.5: cand.append((0, dist_to(t, e), t))
        for o in rivers:
            if o == n or o == t: continue
            d = float(rt[o].query(e)[0])
            if d < 1.2 and rivers[o]["D"] > .6 * r["D"]: cand.append((1, d, o))
        for o in lakes:
            if o == t: continue
            d = float(lt[o].query(e)[0])
            if d < 1.2: cand.append((1, d, o))
        if not cand:
            if B.query(e)[0] < 1.2: report["abroad"] += 1
            else: report["none"].append(n)
            continue
        cand.sort(key=lambda c: (c[0], c[1])); _, gap, t = cand[0]
        # a named recipient far away while the mouth sits on the border: the river leaves the country there
        if gap > 1.0 and B.query(e)[0] < 1.0 and cand[0][0] == 0 and not any(c[1] < .5 for c in cand): report["abroad"] += 1; continue
        kind = "river" if t in rivers else "lake"; out[n] = (t, kind)
        line = [list(p) for p in r["lines"][li]]
        def end_pt(): return np.array(line[-1][:2], float)
        def tangent():
            a = np.array(line[-1][:2]); b = np.array(line[max(0, len(line) - 4)][:2]); v = a - b; L = np.hypot(*v)
            return v / L if L > 1e-6 else np.array([1.0, 0.0])
        def append(pts):
            d0 = line[-1][2]; prev = np.array(line[-1][:2])
            for q in pts:
                d0 += float(np.hypot(*(q - prev))); prev = q; line.append([round(float(q[0]), 3), round(float(q[1]), 3), round(d0, 3)])
        # 2. pieces of the same river left out of the data: follow them from the mouth towards the recipient
        if gap > .3:
            if ways is None: ways = _tile_ways()
            base = re.sub(r"\s*\(.*\)$", "", n).rstrip("·")
            pool = dict(ways.get(base, {})); added = False
            for _ in range(40):
                cur = end_pt(); g0 = dist_to(t, cur); best = None
                for wid, a in pool.items():
                    for rev in (False, True):
                        q = a[::-1] if rev else a
                        j = float(np.hypot(*(q[0] - cur)))
                        if j > .9: continue
                        gq = dist_to(t, q[-1])
                        if gq < g0 - .05 and (best is None or j + gq < best[0]): best = (j + gq, wid, q)
                if not best: break
                _, wid, q = best; pool.pop(wid)
                k = int(np.argmin([dist_to(t, x) for x in q]))   # stop where it is closest to the recipient
                seg = _even(np.vstack([cur, q[:k + 1]]))[1:]
                if len(seg): append(seg); added = True
                if dist_to(t, end_pt()) < .05: break
            if added: report["from_tiles"] += 1; gap = dist_to(t, end_pt())
        # 3. the last stretch: a smooth curve to the recipient's centre line (or a little way into the lake)
        cur = end_pt()
        if kind == "river":
            tgt = rp[t][rt[t].query(cur)[1]]
        else:
            ring_pt = lp[t][lt[t].query(cur)[1]]; c = lcen[t]; v = c - ring_pt; L = np.hypot(*v)
            tgt = ring_pt + (v / L * min(.12, L * .3) if L > 1e-6 else 0)
        g = float(np.hypot(*(tgt - cur)))
        if g > 2.6: report["none"].append(n); out.pop(n); continue
        if g > .02:
            append(_curve(cur, tangent(), tgt)); report["bridged"] += 1
        else: report["ok"] += 1
        r["lines"][li] = line
        r["D"] = round(max(r["D"], line[-1][2]), 3)
        rp[n] = np.array([p[:2] for l in r["lines"] for p in l], float); rt[n] = cKDTree(rp[n])
    log(f"mouths: {report['ok']} already in place, {report['bridged']} led into their recipient "
        f"({report['from_tiles']} with river pieces from the map data), {report['abroad']} leave Belarus, "
        f"{len(report['none'])} without a recipient nearby: {', '.join(report['none'])}")
    return out
