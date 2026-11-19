# Lines of the main canals of Belarus from OpenStreetMap -> data/canals.json (one small bounding-box query per canal)
import json, os, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
# id -> (south, west, north, east), name pattern (Russian or Belarusian OSM names)
CAN = {"Днепровско-Бугский канал": ((51.95, 24.30, 52.30, 26.20), "Дн[еяі]про[ўв]ска-Бугск"),
       "Огинский канал": ((52.45, 25.35, 52.80, 25.95), "[ОА]г[иі]нск"),
       "Августовский канал": ((53.80, 23.45, 54.00, 23.80), "[АА][ўв]густо[ўв]ск"),
       "Вилейско-Минский канал": ((53.95, 26.90, 54.55, 27.50), "В[иі]лейска?-М[иі]нск|В[иі]лейск")}
fn = os.path.join(root, "data", "canals.json"); out = json.load(open(fn, encoding="utf8")) if os.path.exists(fn) else {}
for name, ((s, w, n, e), pat) in CAN.items():
    if name in out: continue
    q = f'[out:json][timeout:90];way["waterway"="canal"]["name"~"{pat}"]({s},{w},{n},{e});out geom;'
    data = urllib.parse.urlencode({"data": q}).encode(); js = None
    for attempt in range(4):
        for h in HOSTS:
            try:
                js = json.loads(urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=120).read()); break
            except Exception as ex: print(name, h, str(ex)[:60], flush=True)
        if js: break
        time.sleep(10)
    if not js: print(name, "FAILED"); continue
    out[name] = js["elements"]; json.dump(out, open(fn, "w", encoding="utf8"), ensure_ascii=False)
    print(name, len(js["elements"]), sorted({x.get("tags", {}).get("name") for x in js["elements"]}), flush=True)
