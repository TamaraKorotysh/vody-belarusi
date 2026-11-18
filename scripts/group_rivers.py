# Turn all downloaded river ways into whole rivers: group by name + connectivity, measure, find where each flows.
import json, glob, math, numpy as np
from scipy.spatial import cKDTree
ways = {}
for fn in glob.glob("tiles/r_*.json"):
    for e in json.load(open(fn, encoding="utf8"))["elements"]:
        if e["type"] == "way" and e.get("geometry"): ways[e["id"]] = e
print("ways", len(ways))
G = json.load(open("geo_ll.json", encoding="utf8")); B = np.array(G["border"])
def inside_many(P):
    P = np.asarray(P); c = np.zeros(len(P), bool); x, y = P[:, 0], P[:, 1]
    x1, y1 = B[:, 0], B[:, 1]; x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
    for i in range(len(B)):
        if y1[i] == y2[i]: continue
        c ^= ((y1[i] > y) != (y2[i] > y)) & (x < (x2[i] - x1[i]) * (y - y1[i]) / (y2[i] - y1[i]) + x1[i])
    return c
KX = math.cos(math.radians(53.7))
def km(pts):
    a = np.asarray(pts); d = np.diff(a, axis=0); return float(np.sum(np.hypot(d[:, 0] * 111.3 * KX, d[:, 1] * 111.3)))
# group: same Russian name (fallback: name) + touching ends
key = lambda e: e["tags"].get("name:ru") or e["tags"].get("name")
parent = {}
def find(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
ends = {}
for wid, e in ways.items():
    parent[wid] = wid; g = e["geometry"]
    for p in (g[0], g[-1]):
        k = (key(e), round(p["lon"], 4), round(p["lat"], 4)); ends.setdefault(k, []).append(wid)
for k, ids in ends.items():
    for w in ids[1:]: parent[find(w)] = find(ids[0])
comps = {}
for wid in ways: comps.setdefault(find(wid), []).append(wid)
from collections import defaultdict
byname = defaultdict(list)
for root in comps: byname[key(ways[comps[root][0]])].append(root)
def cpts(root): return np.array([(p["lon"] * KX, p["lat"]) for w in comps[root] for p in ways[w]["geometry"]])
def cends(root): return np.array([(p["lon"] * KX, p["lat"]) for w in comps[root] for p in (ways[w]["geometry"][0], ways[w]["geometry"][-1])])
for nm, roots in byname.items():
    if len(roots) < 2 or not nm: continue
    changed = True
    while changed:
        changed = False
        for i in range(len(roots)):
            for j in range(i + 1, len(roots)):
                a, b = roots[i], roots[j]
                ta = cKDTree(cpts(a)); tb = cKDTree(cpts(b))
                if ta.query(cends(b))[0].min() < 0.014 or tb.query(cends(a))[0].min() < 0.014:
                    comps[a] += comps.pop(b); roots.pop(j); changed = True; break
            if changed: break
CUR = set(json.load(open("curated_names.json", encoding="utf8")))
rivers = []
allpts = []; owner = []
for root, ids in comps.items():
    e0 = ways[ids[0]]; name = key(e0)
    lines = [[(p["lon"], p["lat"]) for p in ways[w]["geometry"]] for w in ids]
    total = sum(km(l) for l in lines)
    pts = np.vstack(lines); ins = inside_many(pts); kin = total * ins.mean()
    rivers.append({"ru": name, "be": e0["tags"].get("name:be") or e0["tags"].get("name"), "km": total, "kin": kin, "lines": lines, "ids": ids})
for ri, r in enumerate(rivers):
    for l in r["lines"]:
        for p in l[::2]: allpts.append(p); owner.append(ri)
tree = cKDTree(np.array(allpts) * [KX, 1]); owner = np.array(owner)
# mouth: a way end that no other way of this river continues from = downstream sink; nearest other river there
for ri, r in enumerate(rivers):
    starts = {(round(l[0][0], 4), round(l[0][1], 4)) for l in r["lines"]}
    sinks = [l[-1] for l in r["lines"] if (round(l[-1][0], 4), round(l[-1][1], 4)) not in starts]
    mouth = None
    for s in sinks:
        idx = tree.query_ball_point([s[0] * KX, s[1]], 0.012)
        others = [owner[i] for i in idx if owner[i] != ri]
        if others:
            o = max(others, key=lambda k: rivers[k]["km"]); mouth = rivers[o]["ru"]; break
    if mouth == r["ru"]: mouth = None
    if mouth and mouth.startswith("протока "): mouth = {"протока Старая Птичь": "Птичь"}.get(mouth, mouth)
    r["mouth"] = mouth
keep = [r for r in rivers if r["kin"] >= 35 and r["ru"] not in CUR]
FIXMOUTH = {"Россь": "Неман", "Стыр": "Припять"}
RENAME = {"Стыр": "Стырь", "Нарочанка": "Нарочь (река)"}
for r in keep:
    r["mouth"] = FIXMOUTH.get(r["ru"], r["mouth"])
    for o in keep:
        if o["mouth"] == r["ru"] and r["ru"] in RENAME: o["mouth"] = RENAME[r["ru"]]
for r in keep: r["ru"] = RENAME.get(r["ru"], r["ru"])
osh = [r for r in keep if r["ru"] == "Ошмянка"]
if len(osh) == 2:
    a, b = sorted(osh, key=lambda r: -r["kin"]); a["lines"] += b["lines"]; a["km"] += b["km"]; a["kin"] += b["kin"]; a["mouth"] = "Вилия"; keep.remove(b)
# unique ids for repeated names
cnt = {}
for r in keep: cnt[r["ru"]] = cnt.get(r["ru"], 0) + 1
used = set(CUR) - set(RENAME.values())
for r in sorted(keep, key=lambda r: -r["kin"]):
    rid = r["ru"]
    if rid in used: rid = f'{r["ru"]} (приток: {r["mouth"]})' if r["mouth"] else f'{r["ru"]} ({round(r["kin"])} км)'
    while rid in used: rid += "·"
    used.add(rid); r["id"] = rid
# Belarusian spellings corrected after «Блакітная кніга Беларусі»
BE_FIX = {"Добысна": "Добасна", "Берёзовка": "Бярозаўка", "Лукомка": "Лукомка"}
out = [{"id": r["id"], "ru": r["ru"], "be": BE_FIX.get(r["ru"], r["be"]), "km": round(r["km"]), "kin": round(r["kin"]), "mouth": r["mouth"], "lines": [[[round(x, 5), round(y, 5)] for x, y in l] for l in r["lines"]]} for r in keep]
json.dump(out, open("rivers_auto.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print(len(rivers), "groups;", len(out), "kept")
for r in sorted(out, key=lambda r: -r["kin"])[:400]: print(f'{r["id"]:40s} {r["kin"]:4d} км  -> {r["mouth"]}')
