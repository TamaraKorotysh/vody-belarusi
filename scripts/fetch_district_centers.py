# Administrative centres of all districts (admin_level=6) of Belarus from OpenStreetMap -> data/district_centers.json
import json, os, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
Q = """[out:json][timeout:180];
area["ISO3166-1"="BY"]["admin_level"="2"]->.by;
rel(area.by)["boundary"="administrative"]["admin_level"="6"]->.d;
.d out tags;
node(r.d:"admin_centre")->.c;
node(r.d:"label")->.l;
(.c;.l;);
out;"""
data = urllib.parse.urlencode({"data": Q}).encode()
for attempt in range(5):
    for h in HOSTS:
        try:
            d = urllib.request.urlopen(urllib.request.Request(h, data=data, headers={"User-Agent": "river-map-builder/1.0"}), timeout=240).read()
            js = json.loads(d); break
        except Exception as e:
            print(h, str(e)[:80], flush=True); js = None
    if js: break
    time.sleep(15)
rels = [e for e in js["elements"] if e["type"] == "relation"]
nodes = {e["id"]: e for e in js["elements"] if e["type"] == "node"}
out = []
for n in nodes.values():
    t = n.get("tags", {})
    out.append({"ru": t.get("name:ru") or t.get("name"), "be": t.get("name:be") or t.get("name"), "lat": n["lat"], "lon": n["lon"],
                "place": t.get("place"), "pop": t.get("population")})
json.dump(out, open(os.path.join(root, "data", "district_centers.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
print(len(rels), "districts;", len(out), "centres")
