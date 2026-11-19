# Match the OSM small rivers (data/rivers_auto.json) to entries of «Блакітная кніга Беларусі» (text of the PDF).
# Usage: python scripts/book_rivers.py <book.txt>   -> data/book_auto.json
import json, re, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(sys.argv[1], encoding="utf8").read().replace("\f", "\n")
t = re.sub(r"\s+", " ", t)
auto = json.load(open(os.path.join(root, "data", "rivers_auto.json"), encoding="utf8"))
UP = "А-ЯЁІЎ"
def norm(s): return s.upper().replace(" ", "").replace("Ё", "Е").replace("Ў", "У").replace("Й", "И").replace("'", "").replace("’", "").replace("ʼ", "")
# all river entries: HEADING, [other names,] рака ў ..., левы/правы прыток ...
ent = []
for m in re.finditer(r"(?<![" + UP + r"])([" + UP + r"][" + UP + r"\-ʼ' ]{1,30}?), ((?:[^.,]{1,40}, ){0,4})рака ((?:[^.]|(?<= р)\.|(?<=Зах)\.|(?<=воз)\.|(?<=бас)\.|\.(?! [А-ЯЁІЎ]))*?)(?<! р)(?<!Зах)(?<!воз)(?<!бас)\. (?=(.{0,900}))", t):
    head, alt, where, rest = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
    km = re.search(r"Даўжыня ?([\d ]+(?:,\d+)?) км", rest[:300])
    if not km: continue
    bas = re.search(r"Пл\. вадазбору ([\d ]+(?:,\d+)?) (тыс\. )?км", rest[:400])
    q = re.search(r"Сярэднегадавы расход вады ў вусці (?:каля )?([\d,]+) м", rest[:500])
    side = re.search(r"(левы|правы) прыток (?:р\. )?([" + UP + r"][а-яёіўʼ'\.\- ]+?)(?: \(|\.|,|$)", where)
    keys = {norm(head)} | {norm(head.split(" ")[-1])} | {norm(a) for a in alt.split(",") if a.strip()}
    ent.append({"keys": keys, "head": norm(head), "km": float(km.group(1).replace(" ", "").replace(",", ".")),
                "basin": (bas.group(1).replace(" ", "") + (" тыс." if bas.group(2) else "")) if bas else None,
                "q": q.group(1) if q else None, "side": side.group(1) if side else None,
                "into": side.group(2).strip() if side else None, "where": where[:120]})
print("book river entries:", len(ent))
byhead = {}
for e in ent:
    for k in e.pop("keys"): byhead.setdefault(k, []).append(e)
out = {}; miss = []
for r in auto:
    cands = byhead.get(norm(r["be"] or ""), [])
    if not cands: miss.append(r["id"]); continue
    mb = {"СОЖ": "САЖ"}.get(norm(r.get("mouth_be") or "")[:3], norm(r.get("mouth_be") or "")[:3])
    def score(e):
        s = -abs(e["km"] - r["kin"]) / max(r["kin"], 1)
        if mb and e["into"] and norm(e["into"]).startswith(mb): s += 1
        return s
    best = max(cands, key=score)
    if abs(best["km"] - r["km"]) / max(best["km"], 1) > .6 and not (mb and best["into"] and norm(best["into"]).startswith(mb)):
        miss.append(r["id"] + " (?)"); continue
    def stem_ok(e):   # the book gives the mouth in the genitive: compare the stem without the case ending
        into = norm(e["into"].replace("-", "")); mo = norm(r.get("mouth_be") or "")
        if mo.startswith("ЗАХ"): return into.startswith("ЗАХ")
        if {mo[:3], into[:3]} <= {"СОЖ", "САЖ"}: return True
        k = min(3, max(2, len(mo) - 1)); return into[:k] == mo[:k]
    if mb and best["into"] and not stem_ok(best):
        miss.append(r["id"] + " (другое устье)"); continue
    out[r["id"]] = best
json.dump(out, open(os.path.join(root, "data", "book_auto.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
print("matched", len(out), "of", len(auto)); print("not found:", miss)
