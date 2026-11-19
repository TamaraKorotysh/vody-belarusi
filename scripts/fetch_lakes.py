# The next largest lakes of «Блакітная кніга Беларусі» (data/book_lakes.json) with outlines from OpenStreetMap via Nominatim.
# A found outline is accepted only if its area agrees with the book (0.45–2.2 times) -> data/nom_lakes.json
import json, math, os, sys, time, urllib.request, urllib.parse
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 100
book = json.load(open(os.path.join(D, "book_lakes.json"), encoding="utf8"))
HAVE = {"Нарач", "Асвейскае", "Чырвонае", "Лукомскае", "Дрывяты", "Свір", "Снуды", "Выганашчанскае", "Мядзел", "Езярышча", "Рычы", "Рьічы", "Струста",
        "Мястра", "Нешчарда", "Доўгае", "Рытаўна"}
def clean(n):   # OCR marks stress with Ё/Ў: try the name as printed and without those marks
    n = n.replace(" Возера", "").strip(); return list(dict.fromkeys([n, n.replace("ё", "е").replace("Ё", "Е"), n.replace("ў", "у").replace("Ў", "У")]))
def km2(gj):
    polys = [gj["coordinates"]] if gj["type"] == "Polygon" else gj["coordinates"] if gj["type"] == "MultiPolygon" else []
    a = 0
    for p in polys:
        r = p[0]; la = math.radians(r[0][1]); kx = 111.32 * math.cos(la)
        a += abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2 * kx * 110.57
    return a
fn = os.path.join(D, "nom_lakes.json"); out = json.load(open(fn, encoding="utf8")) if os.path.exists(fn) else {}
seen = set(); tried = 0
for b in book:
    if len(out) >= WANT: break
    key = (b["area"], b["depth"])
    if key in seen or b["be"].replace(" Возера", "") in HAVE: continue
    seen.add(key)
    if any(v["book"]["area"] == b["area"] and v["book"]["depth"] == b["depth"] for v in out.values()): continue
    hit = None
    for name in clean(b["be"]):
        for q in (f"{name} возера", f"возера {name}"):
            url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "countrycodes": "by", "format": "jsonv2", "polygon_geojson": 1,
                    "polygon_threshold": 0.0002, "namedetails": 1, "limit": 6})
            try: res = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "river-map-builder/1.0"}), timeout=60).read())
            except Exception as e: print("ERR", str(e)[:50]); res = []
            time.sleep(1.1); tried += 1
            for r in res:
                gj = r.get("geojson", {})
                if gj.get("type") not in ("Polygon", "MultiPolygon"): continue
                if r.get("category") not in ("natural", "water") and r.get("type") not in ("water", "lake"): continue
                a = km2(gj)
                if b["area"] * .45 <= a <= b["area"] * 2.2: hit = (r, a); break
            if hit: break
        if hit: break
    if not hit: print("  not found:", b["be"], b["area"], flush=True); continue
    r, a = hit; nd = r.get("namedetails") or {}
    ru = nd.get("name:ru") or ""
    out[b["be"]] = {"book": b, "name": r.get("name"), "ru": ru, "be": nd.get("name:be") or r.get("name"), "osm": f'{r["osm_type"]}/{r["osm_id"]}',
                    "km2": round(a, 2), "geojson": r["geojson"]}
    json.dump(out, open(fn, "w", encoding="utf8"), ensure_ascii=False)
    print(len(out), b["be"], b["area"], "->", r.get("name"), "|", ru, round(a, 2), flush=True)
print("accepted", len(out), "requests", tried)
