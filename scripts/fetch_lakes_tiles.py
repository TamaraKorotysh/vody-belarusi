# All named water polygons in the Belarus area, tile by tile -> data/lake_tiles/w_i_j.json
# (used to pick the next largest lakes; small queries survive the overloaded public servers better)
import json, os, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
os.makedirs(os.path.join(root, "data", "lake_tiles"), exist_ok=True)
lats = [51.2, 52.0, 52.8, 53.6, 54.4, 55.2, 56.2]; lons = [23.1, 24.8, 26.5, 28.2, 29.9, 31.6, 32.8]
for i in range(len(lats) - 1):
    for j in range(len(lons) - 1):
        fn = os.path.join(root, "data", "lake_tiles", f"w_{i}_{j}.json")
        if os.path.exists(fn): continue
        b = f"({lats[i]},{lons[j]},{lats[i+1]},{lons[j+1]})"
        q = f'[out:json][timeout:180];(way["natural"="water"]["name"]{b};relation["natural"="water"]["name"]{b};);out geom;'
        data = urllib.parse.urlencode({"data": q}).encode(); ok = False
        for attempt in range(6):
            for h in HOSTS:
                try:
                    d = urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=200).read()
                    json.loads(d); open(fn, "wb").write(d); ok = True; break
                except Exception as e: print(fn[-12:], attempt, h[8:30], str(e)[:50], flush=True)
            if ok: break
            time.sleep(10)
        print(fn[-12:], "ok" if ok else "FAILED", flush=True)
print("done")
