# Outlines of named water objects from OpenStreetMap via Nominatim (one quick request per name, 1 request per second).
# Usage: python scripts/fetch_nominatim.py reservoirs|canals|lakes
# reservoirs/canals: fixed lists below; lakes: names from data/lake_queries.json -> data/nom_<kind>.json
import json, os, sys, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
kind = sys.argv[1]
LISTS = {
 "reservoirs": {"Вилейское водохранилище": "Вилейское водохранилище", "Заславское водохранилище": "Заславское водохранилище",
   "Солигорское водохранилище": "Солигорское водохранилище", "Любанское водохранилище": "Любанское водохранилище",
   "Чигиринское водохранилище": "Чигиринское водохранилище", "Водохранилище Селец": "водохранилище Селец Берёзовский район",
   "Водохранилище Погост": "вадасховішча Пагост", "Водохранилище Локтыши": "водохранилище Локтыши",
   "Зельвенское водохранилище": "Зельвенское водохранилище", "Осиповичское водохранилище": "Осиповичское водохранилище",
   "Днепровско-Брагинское водохранилище": "Дняпроўска-Брагінскае вадасховішча"},
 "canals": {"Днепровско-Бугский канал": "Дняпроўска-Бугскі канал", "Огинский канал": "Огинский канал",
   "Августовский канал": "Аўгустоўскі канал", "Вилейско-Минский канал": "Вілейска-Мінскі канал"},
}
items = LISTS.get(kind) or json.load(open(os.path.join(D, "lake_queries.json"), encoding="utf8"))
fn = os.path.join(D, f"nom_{kind}.json"); out = json.load(open(fn, encoding="utf8")) if os.path.exists(fn) else {}
for key, q in items.items():
    if key in out: continue
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "countrycodes": "by", "format": "jsonv2", "polygon_geojson": 1,
                                                                                 "polygon_threshold": 0.0002, "limit": 5})
    try:
        res = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "river-map-builder/1.0"}), timeout=60).read())
    except Exception as e:
        print(key, "ERR", str(e)[:60], flush=True); time.sleep(2); continue
    water = [r for r in res if r.get("category") in ("water", "waterway", "natural", "landuse") and r.get("geojson", {}).get("type") != "Point"]
    if not water: print(key, "not found:", [(r.get("category"), r.get("type"), r.get("name")) for r in res][:3], flush=True)
    else:
        r = water[0]; out[key] = {"name": r.get("name"), "type": r.get("type"), "osm": f'{r["osm_type"]}/{r["osm_id"]}', "geojson": r["geojson"]}
        print(key, "->", r.get("name"), r.get("type"), r["geojson"]["type"], flush=True)
    json.dump(out, open(fn, "w", encoding="utf8"), ensure_ascii=False)
    time.sleep(1.1)
