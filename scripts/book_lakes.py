# Lakes of «Блакітная кніга Беларусі» with their figures, largest first -> data/book_lakes.json
# Usage: python scripts/book_lakes.py data/book.txt
import json, re, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = re.sub(r"\s+", " ", open(sys.argv[1], encoding="utf8").read())
UP = "А-ЯЁІЎ"
num = lambda x: float(x.replace(" ", "").replace(",", "."))
def parse(head, alt, body):
    a = re.search(r"Пл\. ([\d ]+(?:,\d+)?) км", body[:220])
    if not a: return None
    d = re.search(r"Найбольшая глыбіня ([\d]+(?:,\d+)?) м", body[:400])
    v = re.search(r"Аб.ём вады ([\d ]+(?:,\d+)?) млн", body[:600])
    rn = re.search(r"[уў] ([А-ЯЁІЎ][а-яёіў\-]+(?:скім|цкім)) р-не", body[:120])
    bs = re.search(r"У бас\. (?:р\. |воз\. )?([А-ЯЁІЎ][а-яёіўʼ'\- ]+?)[,(.]", body[:900])
    return {"be": head.title(), "alt": alt, "area": num(a.group(1)), "depth": num(d.group(1)) if d else None, "vol": num(v.group(1)) if v else None,
            "district": rn.group(1) if rn else None, "basin": bs.group(1).strip() if bs else None}
out = []
for m in re.finditer(r"(?<![%s])([%s][%s\-ʼ' ]{1,30}?), ((?:[^.,]{1,40}, ){0,3})возера (?=(.{0,900}))" % (UP, UP, UP), t):
    r = parse(m.group(1).strip(), m.group(2).strip(", "), m.group(3)); r and out.append(r)
for m in re.finditer(r"(?<![%s])([%s][%s\-ʼ' ]{1,30}?) В[ОЙ]ЗЕРА, ((?:[^.,]{1,40}, ){0,3})(?=(.{0,900}))" % (UP, UP, UP), t):
    r = parse(m.group(1).strip(), m.group(2).strip(", "), m.group(3)); r and out.append(r)
seen = set(); res = []
for r in sorted(out, key=lambda r: -r["area"]):
    k = (r["be"], r["area"])
    if k in seen: continue
    seen.add(k); res.append(r)
json.dump(res, open(os.path.join(root, "data", "book_lakes.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
print(len(res)); [print(r) for r in res[:30]]
