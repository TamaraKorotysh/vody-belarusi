# Report breaks inside river ribbons: a line end that is close to, but not touching, another line of the same river.
# Usage (from data/): python ../scripts/check_gaps.py [lp.json]
import json, sys, numpy as np
from scipy.spatial import cKDTree
L = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "lp.json", encoding="utf8"))
bad = []
for n, r in L["rivers"].items():
    lines = [np.array(l)[:, :2] for l in r["lines"]]
    if len(lines) < 2: continue
    ln = [float(np.sum(np.hypot(*np.diff(l, axis=0).T))) for l in lines]
    for i, l in enumerate(lines):
        if ln[i] < 1.0: continue          # short side arms and stubs are not breaks in the course
        big = [o for j, o in enumerate(lines) if j != i and ln[j] >= 1.0]
        if not big: continue
        others = np.vstack(big); t = cKDTree(others)
        for end in (l[0], l[-1]):
            d = t.query(end)[0]
            if .12 < d < 2.5: bad.append((n, round(float(d), 2)))
print(len({b[0] for b in bad}), "rivers with breaks;", len(bad), "breaks")
for n in sorted({b[0] for b in bad}): print("  ", n, [d for m, d in bad if m == n])
