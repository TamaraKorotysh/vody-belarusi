# All named rivers in the Belarus area, downloaded in tiles so each Overpass request stays small.
import json, time, urllib.request, urllib.parse, os
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
os.makedirs("tiles", exist_ok=True)
lats = [51.2, 52.2, 53.2, 54.2, 55.2, 56.2]; lons = [23.1, 25.1, 27.1, 29.1, 31.1, 32.8]
for i in range(len(lats) - 1):
    for j in range(len(lons) - 1):
        fn = f"tiles/r_{i}_{j}.json"
        if os.path.exists(fn): continue
        bb = f"{lats[i]},{lons[j]},{lats[i+1]},{lons[j+1]}"
        q = f'[out:json][timeout:240][bbox:{bb}];way["waterway"="river"]["name"];out geom qt;'
        data = urllib.parse.urlencode({"data": q}).encode(); ok = False
        for attempt in range(6):
            for h in HOSTS:
                try:
                    d = urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=280).read()
                    json.loads(d); open(fn, "wb").write(d); ok = True; break
                except Exception as e: print(fn, attempt, h, str(e)[:60], flush=True)
            if ok: break
            time.sleep(10)
        print(fn, "ok" if ok else "FAILED", flush=True)
print("done")
