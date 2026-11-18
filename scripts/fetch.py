import urllib.request, urllib.parse, sys
H="https://overpass.kumi.systems/api/interpreter"
rivers="Днепр|Западная Двина|Неман|Припять|Березина|Сож|Западный Буг|Вилия|Птичь|Свислочь"
qs={
"rivers.json":f'[out:json][timeout:600][bbox:51.0,23.0,56.4,33.0];way["waterway"="river"]["name:ru"~"^({rivers})$"];out geom qt;',
"lakes.json":'[out:json][timeout:600][bbox:51.0,23.0,56.4,33.0];(way["natural"="water"]["name:ru"~"Нарочь|Освейское|Червоное|Лукомльское|Дривяты"];relation["natural"="water"]["name:ru"~"Нарочь|Освейское|Червоное|Лукомльское|Дривяты"];);out geom qt;'}
for out,q in qs.items():
    req=urllib.request.Request(H,data=urllib.parse.urlencode({"data":q}).encode(),headers={"User-Agent":"river-map-builder/1.0"})
    d=urllib.request.urlopen(req,timeout=650).read(); open(out,"wb").write(d); print(out,len(d),flush=True)
