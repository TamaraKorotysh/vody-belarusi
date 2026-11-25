# Landmarks drawn on the diorama, outlines from OpenStreetMap: the Mikashevichi granite quarry and the Soligorsk potash salt heaps.
# Writes data/landmarks.json (lon, lat). Run from the data folder.
import json, urllib.request, urllib.parse
WAYS = {382237114: ("quarry", "Микашевичский гранитный карьер", "Мікашэвіцкі гранітны кар'ер", 150),   # depth, m (RUPP Granit, about 150 m today)
        222768274: ("heap", "Солеотвал 1-го рудоуправления", "Солеадвал 1-га рудаўпраўлення", 100),   # height, m
        41036116:  ("heap", "Солеотвал 2-го рудоуправления", "Солеадвал 2-га рудаўпраўлення", 100),
        41036117:  ("heap", "Солеотвал 3-го рудоуправления", "Солеадвал 3-га рудаўпраўлення", 100),
        223238021: ("heap", "Солеотвал 4-го рудоуправления", "Солеадвал 4-га рудаўпраўлення", 100)}
q = "[out:json][timeout:90];(way(id:%s););out geom;" % ",".join(map(str, WAYS))
E = None
for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter"):
    try:
        req = urllib.request.Request(url, urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "map-script/1.0"})
        E = json.load(urllib.request.urlopen(req, timeout=120))["elements"]; break
    except Exception as ex: print(url, ex)
out = []
for e in E:
    kind, ru, be, h = WAYS[e["id"]]
    ring = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    if ring[0] == ring[-1]: ring = ring[:-1]
    out.append({"osm": e["id"], "kind": kind, "ru": ru, "be": be, "m": h, "ring": ring})
out.sort(key=lambda o: list(WAYS).index(o["osm"]))
json.dump({"town": ["Микашевичи", 27.4874, 52.2244, "Мікашэвічы"], "marks": out}, open("landmarks.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(len(out), "outlines")
