# Outlines of the main reservoirs of Belarus from OpenStreetMap -> data/reservoirs.json
# One small bounding-box query per reservoir (a country-wide name search times out on the public servers).
import json, os, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
# id -> approximate centre (lat, lon), taken from the book's location notes
RES = {"Вилейское водохранилище": (54.53, 27.10), "Заславское водохранилище": (54.00, 27.37), "Солигорское водохранилище": (52.85, 27.58),
       "Любанское водохранилище": (52.86, 27.93), "Чигиринское водохранилище": (53.28, 29.55), "Водохранилище Селец": (52.60, 24.88),
       "Водохранилище Погост": (52.28, 26.38), "Водохранилище Локтыши": (52.72, 26.72), "Зельвенское водохранилище": (53.13, 24.84),
       "Осиповичское водохранилище": (53.33, 28.60), "Днепровско-Брагинское водохранилище": (52.05, 30.62)}
out = {}
fn = os.path.join(root, "data", "reservoirs.json")
if os.path.exists(fn): out = json.load(open(fn, encoding="utf8"))
for name, (la, lo) in RES.items():
    if name in out: continue
    d = .22
    b = f"({la-d},{lo-d},{la+d},{lo+d})"
    q = f'[out:json][timeout:60];(way["water"="reservoir"]{b};relation["water"="reservoir"]{b};way["landuse"="reservoir"]{b};relation["landuse"="reservoir"]{b};);out geom;'
    data = urllib.parse.urlencode({"data": q}).encode(); js = None
    for attempt in range(4):
        for h in HOSTS:
            try:
                js = json.loads(urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=90).read()); break
            except Exception as e: print(name, h, str(e)[:60], flush=True)
        if js: break
        time.sleep(10)
    if not js: print(name, "FAILED"); continue
    out[name] = js["elements"]; json.dump(out, open(fn, "w", encoding="utf8"), ensure_ascii=False)
    tags = [(e["type"], e.get("tags", {}).get("name"), e.get("tags", {}).get("water")) for e in js["elements"] if e.get("tags", {}).get("name")]
    print(name, len(js["elements"]), tags[:6], flush=True)
