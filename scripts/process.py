import json, math
LON0,LAT1=22.9,56.45; KX=math.cos(math.radians(53.7)); K=160
def P(lon,lat): return ((lon-LON0)*KX*K,(LAT1-lat)*K)
def inext(lon,lat): return 22.9<=lon<=33.1 and 51.0<=lat<=56.45
def dp(pts,eps):
    if len(pts)<3: return pts
    keep=[0]*len(pts); keep[0]=keep[-1]=1; st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop(); (x1,y1),(x2,y2)=pts[a],pts[b]; dx,dy=x2-x1,y2-y1; L=math.hypot(dx,dy) or 1e-9
        mi,md=-1,0
        for i in range(a+1,b):
            d=abs(dy*(pts[i][0]-x1)-dx*(pts[i][1]-y1))/L
            if d>md: mi,md=i,d
        if md>eps: keep[mi]=1; st+= [(a,mi),(mi,b)]
    return [p for p,k in zip(pts,keep) if k]
def path(lines,eps,close=False):
    out=[]
    for ln in lines:
        s=dp(ln,eps)
        if len(s)<2: continue
        out.append("M"+"L".join(f"{x:.1f},{y:.1f}" for x,y in s)+("Z" if close else ""))
    return "".join(out)
def stitch(ways):
    ways=[w[:] for w in ways if len(w)>1]; rings=[]
    while ways:
        r=ways.pop(0); changed=True
        while changed and r[0]!=r[-1]:
            changed=False
            for i,w in enumerate(ways):
                if w[0]==r[-1]: r+=w[1:]
                elif w[-1]==r[-1]: r+=w[::-1][1:]
                elif w[-1]==r[0]: r=w+r[1:]
                elif w[0]==r[0]: r=w[::-1]+r[1:]
                else: continue
                ways.pop(i); changed=True; break
        rings.append(r)
    return rings
g=lambda geom:[(p["lon"],p["lat"]) for p in geom]
proj=lambda ln:[P(*q) for q in ln]
# border
b=json.load(open("border.json",encoding="utf8"))["elements"][0]
outer=[g(m["geometry"]) for m in b["members"] if m["type"]=="way" and m["role"]=="outer"]
rings=stitch(outer); rings.sort(key=len,reverse=True)
border=path([proj(rings[0])],0.5,True)
# rivers
R={}
for e in json.load(open("rivers.json",encoding="utf8"))["elements"]:
    n=e["tags"]["name:ru"]; pts=g(e["geometry"])
    lons=[p[0] for p in pts]
    if n=="Березина" and min(lons)<27.6: continue
    if n=="Свислочь" and min(lons)<26.5: continue
    # split at extent
    seg=[];
    for q in pts:
        if inext(*q): seg.append(q)
        else:
            if len(seg)>1: R.setdefault(n,[]).append(proj(seg))
            seg=[]
    if len(seg)>1: R.setdefault(n,[]).append(proj(seg))
rivers={n:path(stitch(v),0.7) for n,v in R.items()}
# lakes
Lk={}
for e in json.load(open("lakes.json",encoding="utf8"))["elements"]:
    n=e["tags"].get("name:ru","")
    key=next((k for k in ["Нарочь","Освейское","Червоное","Лукомльское","Дривяты"] if k in n),None)
    if not key: continue
    if e["type"]=="way": rs=[g(e["geometry"])]
    else: rs=stitch([g(m["geometry"]) for m in e["members"] if m["type"]=="way" and m.get("geometry")])
    for r in rs:
        pr=proj(r); area=abs(sum(pr[i][0]*pr[i-1][1]-pr[i-1][0]*pr[i][1] for i in range(len(pr))))/2
        Lk.setdefault(key,[]).append((area,pr,n))
lakes={}
for k,v in Lk.items():
    v.sort(key=lambda t:-t[0]); print(k,[ (round(a,1),n) for a,_,n in v[:4]])
    a,pr,_=v[0]; xs=[p[0] for p in pr]; ys=[p[1] for p in pr]
    lakes[k]={"d":path([pr],0.25,True),"c":[round(sum(xs)/len(xs),1),round(sum(ys)/len(ys),1)]}
print({n:len(d) for n,d in rivers.items()}, len(border))
w=round(10.2*KX*K); h=round(5.45*K)
json.dump({"w":w,"h":h,"border":border,"rivers":rivers,"lakes":lakes},open("geo.json","w",encoding="utf8"),ensure_ascii=False)
# city points
cities={"Минск":(27.56,53.90),"Брест":(23.69,52.10),"Гродно":(23.83,53.68),"Гомель":(30.98,52.43),"Могилёв":(30.33,53.90),"Витебск":(30.20,55.19),"Полоцк":(28.80,55.49),"Пинск":(26.10,52.11),"Бобруйск":(29.22,53.14),"Борисов":(28.50,54.23),"Мозырь":(29.25,52.05),"Орша":(30.42,54.51)}
json.dump({k:[round(c,1) for c in P(*v)] for k,v in cities.items()},open("cities.json","w",encoding="utf8"),ensure_ascii=False)