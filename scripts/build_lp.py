# Builds vody-belarusi.html from lp_template.html, the cards and data/lp.json. Run from any folder.
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(root, "data")
rd = lambda p: open(p, encoding="utf8").read()
t = rd(os.path.join(root, "lp_template.html"))
book = json.load(open(os.path.join(D, "book_auto.json"), encoding="utf8")) if os.path.exists(os.path.join(D, "book_auto.json")) else {}
def bk(e):
    if not e: return None
    km = e["km"]; km = int(km) if km == int(km) else km
    return {"km": km, "basin": e["basin"], "q": e["q"], "side": e["side"]}
auto = [{"id": r["id"], "ru": r["ru"], "be": r["be"], "km": r["km"], "kin": r["kin"], "mouth": r["mouth"], "mouth_be": r.get("mouth_be"), "book": bk(book.get(r["id"]))}
        for r in json.load(open(os.path.join(D, "rivers_auto.json"), encoding="utf8"))]
t = (t.replace("/*LP*/", rd(os.path.join(D, "lp.json"))).replace("/*CARDS*/", rd(os.path.join(root, "cards.js")))
      .replace("/*CARDS2*/", rd(os.path.join(root, "cards2.js"))).replace("/*CARDSBE*/", rd(os.path.join(root, "cards_be.js"))).replace("/*AUTO*/", json.dumps(auto, ensure_ascii=False)))
for fn in ("vody-belarusi.html", "index.html"):  # index.html is what GitHub Pages serves at the site root
    open(os.path.join(root, fn), "w", encoding="utf8").write(t); print("vody-belarusi.html", len(t))
