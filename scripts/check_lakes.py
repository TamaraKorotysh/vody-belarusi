# Check the lakes added by fetch_lakes.py: the outline must lie in (or near) the district the book names.
# Prints suspicious lakes; with --drop removes them from data/nom_lakes.json.
import json, math, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
N = json.load(open(os.path.join(D, "nom_lakes.json"), encoding="utf8"))
C = json.load(open(os.path.join(D, "district_centers.json"), encoding="utf8"))
V = set("аеёіоуыэюяиaeiou")
skel = lambda s: "".join(ch for ch in s.lower().replace("ў", "у") if ch.isalpha() and ch not in V and ch not in "ьъ'")
def centre(adj):          # «Аршанскім» -> Орша: compare consonant skeletons
    adj = adj.replace("Гродзен", "Гродн");
    a = skel(adj); best, score = None, 1
    for c in C:
        k = skel(c["be"]); n = 0
        while n < min(len(a), len(k)) and a[n] == k[n]: n += 1
        if n > score or (n == score and best and len(k) < len(skel(best["be"]))): best, score = c, n
    return best
def centroid(gj):
    r = gj["coordinates"][0] if gj["type"] == "Polygon" else gj["coordinates"][0][0]
    return sum(p[0] for p in r) / len(r), sum(p[1] for p in r) / len(r)
bad, seen = [], {}
for k, v in N.items():
    lo, la = centroid(v["geojson"]); b = v["book"]
    if v["osm"] in seen: bad.append((k, "same outline as " + seen[v["osm"]])); continue
    seen[v["osm"]] = k
    if b.get("district"):
        c = centre(b["district"])
        if c:
            d = math.hypot((c["lon"] - lo) * 111.3 * math.cos(math.radians(la)), (c["lat"] - la) * 111.3)
            if d > 60: bad.append((k, f'{b["district"]} р-н, but {round(d)} km from {c["be"]}'))
        else: bad.append((k, "district not recognised: " + b["district"]))
for x in bad: print(" ", x)
print(len(bad), "suspicious of", len(N))
if "--drop" in sys.argv:
    for k, why in bad:
        if not why.startswith("district not recognised"): N.pop(k, None)
    json.dump(N, open(os.path.join(D, "nom_lakes.json"), "w", encoding="utf8"), ensure_ascii=False); print("left", len(N))
