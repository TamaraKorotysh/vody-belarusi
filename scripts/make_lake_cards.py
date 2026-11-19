# Cards for the lakes found by fetch_lakes.py -> cards_lakes.js; also writes each lake's map id into data/nom_lakes.json
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
N = json.load(open(os.path.join(D, "nom_lakes.json"), encoding="utf8"))
A = json.load(open(os.path.join(D, "rivers_auto.json"), encoding="utf8"))
RU = {r["be"]: r["ru"] for r in A if r.get("be")}
RU.update({"Нёман": "Неман", "Прыпяць": "Припять", "Дняпро": "Днепр", "Бярэзіна": "Березина", "Заходняя Дзвіна": "Западная Двина", "Вілія": "Вилия",
           "Друйка": "Друйка", "Дрыса": "Дриса", "Ула": "Улла", "Страча": "Страча", "Нарач": "Нарочь", "Дзісна": "Дисна", "Свольна": "Свольна", "Обаль": "Оболь",
           "Лучоса": "Лучоса", "Дрысвята": "Дрисвята", "Пціч": "Птичь", "Шчара": "Щара", "Ясельда": "Ясельда", "Мухавец": "Мухавец", "Гаўя": "Гавья"})
num = lambda x: (("%g" % x).replace(".", ",")) if x is not None else None
cards, be_cards, used = {}, {}, set()
for key, v in N.items():
    b = v["book"]; ru = (v.get("ru") or "").replace("озеро ", "").replace(" озеро", "").strip()
    be = (v.get("be") or v.get("name") or key).replace("возера ", "").replace(" возера", "").strip()
    ident = ru or be
    while ident in used: ident += " "
    used.add(ident); v["id"] = ident
    st_ru = [["Площадь", num(b["area"]) + " км²"]]; st_be = [["Плошча", num(b["area"]) + " км²"]]
    if b["depth"]: st_ru.append(["Наибольшая глубина", num(b["depth"]) + " м"]); st_be.append(["Найбольшая глыбіня", num(b["depth"]) + " м"])
    if b["vol"]: st_ru.append(["Объём воды", num(b["vol"]) + " млн м³"]); st_be.append(["Аб'ём вады", num(b["vol"]) + " млн м³"])
    bas = b.get("basin")
    if bas: st_ru.append(["Бассейн реки", RU.get(bas, bas)]); st_be.append(["Басейн ракі", bas])
    cards[ident] = {"type": "lake", "minor": True, "small": True, "be": be, "stats": st_ru, "from": ["", ""], "to": ["", ""], "name": "", "facts": []}
    be_cards[ident] = {"stats": st_be, "from": ["", ""], "to": ["", ""], "name": "", "facts": []}
json.dump(N, open(os.path.join(D, "nom_lakes.json"), "w", encoding="utf8"), ensure_ascii=False)
js = ("// Lakes added automatically: figures from «Блакітная кніга Беларусі», outlines from OpenStreetMap (scripts/make_lake_cards.py)\n"
      "Object.assign(CARDS," + json.dumps(cards, ensure_ascii=False) + ");\nObject.assign(CARDS_BE," + json.dumps(be_cards, ensure_ascii=False) + ");\n")
open(os.path.join(root, "cards_lakes.js"), "w", encoding="utf8").write(js)
print(len(cards), "lake cards;", sum(1 for c in cards if not N[[k for k in N if N[k]["id"] == c][0]].get("ru")), "without a Russian name")
