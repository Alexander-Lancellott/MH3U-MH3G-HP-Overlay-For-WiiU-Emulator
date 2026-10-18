"""Summarize poslog.csv: per-entity movement, field consistency, set changes."""
import csv, math, sys
from collections import defaultdict
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
from names import LARGE, SMALL

rows = list(csv.DictReader(open(DIR + r"\poslog.csv")))
by = defaultdict(list)
for r in rows:
    by[r["addr"]].append(r)
print(f"{len(rows)} samples, {len(by)} distinct entities, t=0..{float(rows[-1]['t']):.0f}s\n")

def f(r, k): return float(r[k])
print(f"{'addr':>14} {'name':<18} {'t_from':>6} {'t_to':>6} {'n':>4} {'path':>8} {'xrange':>15} {'zrange':>15} {'yr':>11} {'pos=prev%':>9} home_moves bad")
for a, rs in sorted(by.items(), key=lambda kv: float(kv[1][0]["t"])):
    mid = int(rs[0]["id"])
    name = LARGE.get(mid) or SMALL.get(mid) or f"id {mid}"
    ids = {r["id"] for r in rs}
    if len(ids) > 1: name += f" ids{sorted(ids)}"
    path = sum(math.dist((f(p, "x"), f(p, "z")), (f(q, "x"), f(q, "z"))) for p, q in zip(rs, rs[1:]))
    xs, zs, ys = [f(r, "x") for r in rs], [f(r, "z") for r in rs], [f(r, "y") for r in rs]
    same = sum((r["x"], r["y"], r["z"]) == (r["x2"], r["y2"], r["z2"]) for r in rs) / len(rs) * 100
    home = len({(r["hx"], r["hz"]) for r in rs}) - 1
    bad = sum(not all(map(math.isfinite, (f(r, "x"), f(r, "z")))) or abs(f(r, "x")) > 1e5 for r in rs)
    jumps = max((math.dist((f(p, "x"), f(p, "z")), (f(q, "x"), f(q, "z"))) for p, q in zip(rs, rs[1:])), default=0)
    print(f"{a:>14} {name:<18} {f(rs[0],'t'):6.1f} {f(rs[-1],'t'):6.1f} {len(rs):4d} {path:8.0f} "
          f"{min(xs):7.0f},{max(xs):7.0f} {min(zs):7.0f},{max(zs):7.0f} {min(ys):5.0f},{max(ys):5.0f} {same:8.0f}% "
          f"{home:10d} {bad} maxjump={jumps:.0f}")

print("\nEntity-set changes:")
prev = None
for t in sorted({r["t"] for r in rows}, key=float):
    cur = frozenset((r["addr"], r["id"]) for r in rows if r["t"] == t)
    if cur != prev:
        names = sorted(LARGE.get(int(i)) or SMALL.get(int(i)) or f"id{i}" for _, i in cur)
        print(f"  t={float(t):6.1f}  {len(cur)} ents: {', '.join(names)}")
        prev = cur
