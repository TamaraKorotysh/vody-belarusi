import json, math, os
PROC=os.path.join(os.path.dirname(os.path.abspath(__file__)),"process.py")
exec(open(PROC,encoding="utf8").read().split("def path(")[0].split("LON0,LAT1")[0])
src=open(PROC,encoding="utf8").read()
exec(src[src.index("def dp("):src.index("def path(")])
exec(src[src.index("def stitch("):src.index("g=lambda")])
def chain(ways):  # join head->tail only, keeping flow direction
    ways=[w[:] for w in ways]; out=[]
    while ways:
        r=ways.pop(0); grown=True
        while grown:
            grown=False
            for i,w in enumerate(ways):
                if w[0]==r[-1]: r+=w[1:]; ways.pop(i); grown=True; break
                if w[-1]==r[0]: r=w+r[1:]; ways.pop(i); grown=True; break
        out.append(r)
    return out
g=lambda geom:[(p["lon"],p["lat"]) for p in geom]
R={}
import os
src2=json.load(open("rivers2.json",encoding="utf8"))["elements"] if os.path.exists("rivers2.json") else []
for e in json.load(open("rivers.json",encoding="utf8"))["elements"]+[dict(x,_new=1) for x in src2]:
    n=e["tags"]["name:ru"]; pts=g(e["geometry"]); lons=[p[0] for p in pts]; lats=[p[1] for p in pts]
    if n=="Березина" and min(lons)<27.6: continue
    if n=="Свислочь" and min(lons)<26.5: continue
    if e.get("_new") and n=="Нарочь":
        if not (26.0<min(lons) and max(lons)<27.2 and min(lats)>54.4): continue
        n="Нарочь (река)"
    if n=="Лесная" and not (max(lons)<24.6 and max(lats)<52.9): continue
    if n=="Случь" and min(lats)<51.4: continue
    if n=="Оболь": continue
    R.setdefault(n,[]).append(pts)
# main canals (scripts/fetch_canals.py) are drawn like rivers
if os.path.exists("canals.json"):
    for n,els in json.load(open("canals.json",encoding="utf8")).items():
        for e in els:
            if e["type"]=="way" and e.get("geometry"): R.setdefault(n,[]).append(g(e["geometry"]))
# canals found through Nominatim (scripts/fetch_nominatim.py canals) when Overpass had none
if os.path.exists("nom_canals.json"):
    have=set(json.load(open("canals.json",encoding="utf8"))) if os.path.exists("canals.json") else set()
    for n,v in json.load(open("nom_canals.json",encoding="utf8")).items():
        if n in have: continue
        gj=v["geojson"]; lines=[gj["coordinates"]] if gj["type"]=="LineString" else gj["coordinates"] if gj["type"]=="MultiLineString" else []
        for l in lines: R.setdefault(n,[]).append([tuple(p) for p in l])
rnd=lambda ln:[[round(x,5),round(y,5)] for x,y in ln]
feats=[]
for n,ws in R.items():
    lines=[rnd(dp(l,0.0004)) for l in chain(ws)]
    lines=[l for l in lines if len(l)>1]
    feats.append({"type":"Feature","properties":{"name":n,"kind":"river"},"geometry":{"type":"MultiLineString","coordinates":lines}})
if os.path.exists("rivers_auto.json"):
    for r in json.load(open("rivers_auto.json",encoding="utf8")):
        lines=[rnd(dp([tuple(p) for p in l],0.0004)) for l in chain([[tuple(p) for p in l] for l in r["lines"]])]
        lines=[l for l in lines if len(l)>1]
        if lines: feats.append({"type":"Feature","properties":{"name":r["id"],"kind":"river","auto":1},"geometry":{"type":"MultiLineString","coordinates":lines}})
names=["Нарочь","Освейское","Червоное","Лукомльское","Дривяты","Свирь","Снуды","Выгонощанское","Мядель","Езерище","Ричи","Струсто","Мястро","Долгое","Нещердо"]
L={}
lk3=json.load(open("lakes3.json",encoding="utf8"))["elements"] if os.path.exists("lakes3.json") else []
for e in json.load(open("lakes.json",encoding="utf8"))["elements"]+json.load(open("lakes2.json",encoding="utf8"))["elements"]+lk3:
    n=e["tags"].get("name:ru",""); key=next((k for k in names if k in n),None)
    if not key: continue
    if key=="Нарочь" and "река" in n: continue
    if key=="Долгое":
        gg=e.get("geometry") or [p for m in e.get("members",[]) for p in (m.get("geometry") or [])]
        if not gg: continue
        lo=sum(p["lon"] for p in gg)/len(gg); la=sum(p["lat"] for p in gg)/len(gg)
        if abs(lo-27.75)>0.25 or abs(la-55.2)>0.15: continue
    if e["type"]=="way": outer=[g(e["geometry"])]; inner=[]
    else:
        outer=stitch([g(m["geometry"]) for m in e["members"] if m["type"]=="way" and m.get("role")=="outer" and m.get("geometry")])
        inner=stitch([g(m["geometry"]) for m in e["members"] if m["type"]=="way" and m.get("role")=="inner" and m.get("geometry")])
    def simp(r):
        m=len(r)//2; return rnd(dp(r[:m+1],0.0002)[:-1]+dp(r[m:],0.0002))
    for o in outer:
        if len(o)>3 and o[0]==o[-1]: L.setdefault(key,[]).append([simp(o)]+[simp(i) for i in inner if len(i)>3 and i[0]==i[-1]])
# main reservoirs (scripts/fetch_reservoirs.py): per reservoir, the named water polygon, else the largest one near the centre
STEM={"Вилейское водохранилище":"Вілейск|Вилейск","Заславское водохранилище":"Заслаў|Заслав","Солигорское водохранилище":"Салігорск|Солигорск",
      "Любанское водохранилище":"Любанск","Чигиринское водохранилище":"Чыгірын|Чигирин","Водохранилище Селец":"Сялец|Селец",
      "Водохранилище Погост":"Пагост|Погост","Водохранилище Локтыши":"Лактыш|Локтыш","Зельвенское водохранилище":"Зэльвен|Зельвен",
      "Осиповичское водохранилище":"Асіповіц|Осипович","Днепровско-Брагинское водохранилище":"Брагін|Брагин"}
NOMR=json.load(open("nom_reservoirs.json",encoding="utf8")) if os.path.exists("nom_reservoirs.json") else {}
NOML={v["id"]:v for v in json.load(open("nom_lakes.json",encoding="utf8")).values() if v.get("id")} if os.path.exists("nom_lakes.json") else {}   # lakes added by fetch_lakes.py + make_lake_cards.py
for key,v in list(NOMR.items())+list(NOML.items()):   # reservoir outlines from Nominatim (scripts/fetch_nominatim.py reservoirs)
    gj=v["geojson"]; polys=[gj["coordinates"]] if gj["type"]=="Polygon" else gj["coordinates"] if gj["type"]=="MultiPolygon" else []
    def simp2(r):
        r=[tuple(p) for p in r]; m=len(r)//2; return rnd(dp(r[:m+1],0.0002)[:-1]+dp(r[m:],0.0002))
    for poly in polys:
        if len(poly[0])>3: L.setdefault(key,[]).append([simp2(poly[0])]+[simp2(h) for h in poly[1:] if len(h)>3])
if os.path.exists("reservoirs.json"):
    import re as _re
    def area(r):
        return abs(sum(r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1] for i in range(len(r)-1)))/2
    for key,els in json.load(open("reservoirs.json",encoding="utf8")).items():
        if key in NOMR: continue
        cands=[]
        for e in els:
            if e["type"]=="way":
                if not e.get("geometry"): continue
                outer=[g(e["geometry"])]; inner=[]
            elif e["type"]=="relation":
                outer=stitch([g(m["geometry"]) for m in e.get("members",[]) if m["type"]=="way" and m.get("role")=="outer" and m.get("geometry")])
                inner=stitch([g(m["geometry"]) for m in e.get("members",[]) if m["type"]=="way" and m.get("role")=="inner" and m.get("geometry")])
            else: continue
            outer=[o for o in outer if len(o)>3 and o[0]==o[-1]]
            if not outer: continue
            t=e.get("tags",{}); named=bool(_re.search(STEM[key],(t.get("name","")+" "+t.get("name:ru","")+" "+t.get("name:be",""))))
            cands.append((named,sum(area(o) for o in outer),outer,inner))
        if not cands: print("no outline:",key); continue
        named,_,outer,inner=max(cands,key=lambda c:(c[0],c[1]))
        if not named: print("unnamed outline used:",key)
        def simp(r):
            m=len(r)//2; return rnd(dp(r[:m+1],0.0002)[:-1]+dp(r[m:],0.0002))
        for o in outer: L.setdefault(key,[]).append([simp(o)]+[simp(i) for i in inner if len(i)>3 and i[0]==i[-1]])
for k,polys in L.items():
    feats.append({"type":"Feature","properties":{"name":k,"kind":"lake"},"geometry":{"type":"MultiPolygon","coordinates":polys}})
b=json.load(open("border.json",encoding="utf8"))["elements"][0]
ring=sorted(stitch([g(m["geometry"]) for m in b["members"] if m["type"]=="way" and m["role"]=="outer"]),key=len)[-1]
m=len(ring)//2; ring=rnd(dp(ring[:m+1],0.002)[:-1]+dp(ring[m:],0.002))
out={"water":{"type":"FeatureCollection","features":feats},"border":ring}
s=json.dumps(out,ensure_ascii=False,separators=(",",":")); open("geo_ll.json","w",encoding="utf8").write(s)
print(len(s),{f["properties"]["name"]:len(f["geometry"]["coordinates"]) for f in feats}, len(ring))
