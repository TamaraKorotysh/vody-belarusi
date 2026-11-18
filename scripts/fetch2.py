import urllib.request, urllib.parse, json, time, sys
HOSTS=["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]
RIV=["Щара","Ясельда","Мухавец","Горынь","Случь","Стырь","Уборть","Лань","Друть","Ипуть","Беседь","Проня","Ведрич","Дисна","Улла","Оболь","Лучоса","Нарочь","Котра","Зельвянка","Нарев","Лесная","Оресса","Гайна"]
LAK=["Свирь","Снуды","Выгонощанское","Мядель","Езерище","Ричи","Струсто","Мястро","Долгое","Нещердо"]
def q(body):
    data=urllib.parse.urlencode({"data":"[out:json][timeout:280][bbox:51.0,23.0,56.4,33.0];("+body+");out geom qt;"}).encode()
    for attempt in range(4):
        for h in HOSTS:
            try:
                r=urllib.request.urlopen(urllib.request.Request(h,data=data,headers={"User-Agent":"river-map-builder/1.0"}),timeout=300).read()
                return json.loads(r)["elements"]
            except Exception as e: print(h,e,flush=True)
        time.sleep(10)
    raise SystemExit("failed")
out=[]
for i in range(0,len(RIV),6):
    part=RIV[i:i+6]
    out+=q("".join(f'way["waterway"="river"]["name:ru"="{n}"];' for n in part)); print("rivers",part,len(out),flush=True)
json.dump({"elements":out},open("rivers2.json","w",encoding="utf8"),ensure_ascii=False)
lk=[]
for i in range(0,len(LAK),5):
    part=LAK[i:i+5]
    body="".join(f'nwr["natural"="water"]["name:ru"~"^(озеро )?{n}( озеро)?$"];' for n in part)
    lk+=q(body); print("lakes",part,len(lk),flush=True)
json.dump({"elements":lk},open("lakes3.json","w",encoding="utf8"),ensure_ascii=False)
print("done")
