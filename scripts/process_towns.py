import json, math, re
els = json.load(open("towns.json", encoding="utf8"))
G = json.load(open("geo_ll.json", encoding="utf8")); B = G["border"]
def inside(x, y):
    c = False
    for i in range(len(B)):
        x1, y1 = B[i]; x2, y2 = B[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def pop(t):
    s = re.sub(r"[^\d]", "", (t.get("population") or "").split(";")[0])
    return int(s) if s else 0
OBL = {"Минск", "Брест", "Гродно", "Гомель", "Могилёв", "Витебск"}
seen = {}
for e in els:
    t = e.get("tags", {}); n = t.get("name:ru") or t.get("name"); p = pop(t)
    if not n or p < 20000 or not inside(e["lon"], e["lat"]): continue
    if n == "Могилев": n = "Могилёв"
    if n not in seen or p > seen[n][2]: seen[n] = (e["lon"], e["lat"], p)
for must in OBL:
    if must not in seen: print("нет областного центра:", must)
towns = sorted(seen.items(), key=lambda kv: -kv[1][2])
out = [[n, round(lo, 4), round(la, 4), 1 if n in OBL else (2 if p >= 60000 else 3)] for n, (lo, la, p) in towns]
for n, (lo, la, p) in towns: print(f"{n:16s} {p:8d}")
print(len(out), "towns")
src = open("prep3d.py", encoding="utf8").read()
m = re.search(r"cities=(\[\[.*?\]\])\n", src)
src = src.replace(m.group(1), json.dumps(out, ensure_ascii=False, separators=(",", ":")))
open("prep3d.py", "w", encoding="utf8").write(src)
