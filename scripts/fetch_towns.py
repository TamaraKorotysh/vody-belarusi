import json, time, urllib.request, urllib.parse
q = '[out:json][timeout:180][bbox:51.2,23.1,56.2,32.8];node["place"~"^(city|town)$"];out;'
data = urllib.parse.urlencode({"data": q}).encode()
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
for attempt in range(8):
    for h in HOSTS:
        try:
            d = urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=240).read()
            els = json.loads(d)["elements"]
            json.dump(els, open("towns.json", "w", encoding="utf8"), ensure_ascii=False); print("ok", h, len(els), flush=True); raise SystemExit
        except SystemExit: raise
        except Exception as e: print(attempt, h, e, flush=True)
    time.sleep(15)
print("failed")
