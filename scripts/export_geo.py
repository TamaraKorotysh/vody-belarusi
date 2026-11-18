import json, math
exec(open("process.py",encoding="utf8").read().split("def path(")[0].split("LON0,LAT1")[0])
src=open("process.py",encoding="utf8").read()
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
for k,polys in L.items():
    feats.append({"type":"Feature","properties":{"name":k,"kind":"lake"},"geometry":{"type":"MultiPolygon","coordinates":polys}})
b=json.load(open("border.json",encoding="utf8"))["elements"][0]
ring=sorted(stitch([g(m["geometry"]) for m in b["members"] if m["type"]=="way" and m["role"]=="outer"]),key=len)[-1]
m=len(ring)//2; ring=rnd(dp(ring[:m+1],0.002)[:-1]+dp(ring[m:],0.002))
out={"water":{"type":"FeatureCollection","features":feats},"border":ring}
s=json.dumps(out,ensure_ascii=False,separators=(",",":")); open("geo_ll.json","w",encoding="utf8").write(s)
print(len(s),{f["properties"]["name"]:len(f["geometry"]["coordinates"]) for f in feats}, len(ring))
