# Manual corrections after group_rivers.py + book_rivers.py, checked against «Блакітная кніга Беларусі».
# Fills mouths OpenStreetMap could not find, fixes wrong ones, and adds/removes book data where the automatic match failed.
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
A = json.load(open(os.path.join(D, "rivers_auto.json"), encoding="utf8"))
B = json.load(open(os.path.join(D, "book_auto.json"), encoding="utf8"))
# river id -> (mouth ru, mouth be)
MOUTH = {
    "Эсса": ("Лепельское озеро", "Лепельскае возера"),      # «упадае ў Лепельскае возера з Пд»
    "Шоша": ("озеро Плиса", "возера Пліса"),                # «упадае ў воз. Пліса»
    "Черница": ("Лучоса", "Лучоса"),                        # правы прыток Лучосы
    "Нища": ("Дрыса", "Дрыса"),                              # правы прыток Дрысы
    "Вяча": ("Свислочь (Заславское вдхр.)", "Свіслач (Заслаўскае вадасх.)"),  # «упадае ў Заслаўскае вадасховішча»
    "Ушача": ("Западная Двина", "Заходняя Дзвіна"),          # левы прыток Зах. Дзвіны
    "Тремля": ("Припять", "Прыпяць"),                        # левы прыток Прыпяці (OSM led it into a side channel)
    "Нератовка": ("Птичь", "Пціч"),                          # левы прыток Пцічы
    "Шеметовка": ("Мухавец", "Мухавец"),                     # правы прыток Мухаўца
    "Жигулянка": ("Ясельда", "Ясельда"),                     # левы прыток Ясельды (книга, статья о Ясельде)
    "Альзиница": ("Ушача", "Ушача"),                         # её устье у Ушачи
    "Зеха": ("Лепельское озеро", "Лепельскае возера"),       # «упадае ў Лепельскае возера з Пн»
    "Вымнянка (21 км)": ("Каспля", "Каспля"),               # левы прыток Касплі
}
# rivers whose mouth could not be established from the book or the map are left out
DROP_RIVER = ["Мутвица", "Ушача (21 км)"]
# book data for rivers the automatic match missed: km, basin, discharge, side
BOOK = {
    "Эсса": {"km": 84, "basin": "1040", "q": "7,28", "side": None},
    "Шоша": {"km": 30, "basin": "304", "q": "2", "side": None},
    "Черница": {"km": 74, "basin": "775", "q": "5", "side": "правы"},
    "Нища": {"km": 85, "basin": "1380", "q": "9,7", "side": "правы"},
}
# automatic matches that picked another river of the same name
DROP = ["Нача (приток: Лань)", "Сервеч", "Уша"]
# Belarusian name of every mouth (rivers of the map + the main rivers)
BEN = {r["ru"]: r["be"] for r in A}
BEN.update({"Неман":"Нёман","Припять":"Прыпяць","Днепр":"Дняпро","Сож":"Сож","Березина":"Бярэзіна","Западная Двина":"Заходняя Дзвіна","Вилия":"Вілія",
    "Западный Буг":"Заходні Буг","Птичь":"Пціч","Свислочь":"Свіслач","Щара":"Шчара","Ясельда":"Ясельда","Мухавец":"Мухавец","Случь":"Случ","Друть":"Друць",
    "Ипуть":"Іпуць","Беседь":"Беседзь","Проня":"Проня","Дисна":"Дзісна","Улла":"Ула","Лучоса":"Лучоса","Лань":"Лань","Гайна":"Гайна","Оресса":"Арэса",
    "Котра":"Котра","Оболь":"Обаль","Лесная":"Лясная","Горынь":"Гарынь","Уборть":"Убарць","Нарочь (река)":"Нарач","Стырь":"Стыр","Ислочь":"Іслач","Ведрич":"Ведрыч","Нарев":"Нараў","Зельвянка":"Зальвянка"})
A = [r for r in A if r["id"] not in DROP_RIVER]
for r in A: r["mouth_be"] = BEN.get(r["mouth"]) if r["mouth"] else None
# a mouth OpenStreetMap missed but the book names: turn the book's genitive («Прыпяці», «Сажа») back into a known river
RU_OF = {}
for ru, be in BEN.items():
    if be: RU_OF.setdefault(be.upper().replace("Ё", "Е").replace("Ў", "У")[:4], (ru, be))
RU_OF["САЖА"] = ("Сож", "Сож")
for r in A:
    b = B.get(r["id"])
    if not r["mouth"] and b and b.get("into"):
        k = b["into"].upper().replace("Ё", "Е").replace("Ў", "У")[:4]
        if k in RU_OF: r["mouth"], r["mouth_be"] = RU_OF[k]
for r in A:
    if r["id"] in MOUTH: r["mouth"], r["mouth_be"] = MOUTH[r["id"]]
for k, v in BOOK.items(): B[k] = dict(v, head=k.upper(), into=None, where="")
for k in DROP: B.pop(k, None)
json.dump(A, open(os.path.join(D, "rivers_auto.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(B, open(os.path.join(D, "book_auto.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
print("no mouth left:", [r["id"] for r in A if not r["mouth"]], "| book matches:", len(B))
