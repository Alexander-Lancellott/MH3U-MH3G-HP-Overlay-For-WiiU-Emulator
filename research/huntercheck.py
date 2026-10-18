"""Find the hunter's position: snapshot memory while standing still vs walking.

A topmost window + beeps tell you what to do:
  long low beep   = STAND STILL
  two short beeps = WALK around
Read-only. Results -> hunter_candidates.json next to this script.
"""
import json, math, struct, sys, time, winsound
import tkinter as tk
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
from mh3u_mem import Proc, BASE_OFFSET

SPAN = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x3B00000
BLK = 4096

p = Proc()
base = p.emu_base() + BASE_OFFSET


def snap():
    return p.read(base, SPAN)


def diff(a, b):
    """Word offsets (4-byte aligned) whose value differs."""
    out = set()
    n = min(len(a), len(b))
    for blk in range(0, n, BLK):
        if a[blk:blk + BLK] != b[blk:blk + BLK]:
            for o in range(blk, min(blk + BLK, n), 4):
                if a[o:o + 4] != b[o:o + 4]:
                    out.add(o)
    return out


# (label, kind, seconds, snapshot times within phase)
PHASES = [
    ("Click back into Cemu now", "ready", 8, []),
    ("STAND STILL", "still", 7, [2.5, 5.5]),
    ("WALK around", "walk", 7, [2.5, 5.0]),
    ("STAND STILL", "still", 7, [2.5, 5.5]),
    ("WALK around", "walk", 7, [2.5, 5.0]),
    ("STAND STILL", "still", 7, [2.5, 5.5]),
]

root = tk.Tk()
root.title("Hunter check")
root.attributes("-topmost", True)
root.geometry("+40+40")
root.configure(bg="#14161a")
lbl = tk.Label(root, text="", font=("Segoe UI", 22, "bold"), bg="#14161a", fg="#e6e6e6", padx=24, pady=16)
lbl.pack()
sub = tk.Label(root, text="", font=("Segoe UI", 11), bg="#14161a", fg="#8a8f98")
sub.pack(pady=(0, 12))

snaps = []          # (phase_index, kind, bytes)
log = []


def run():
    for i, (label, kind, secs, at) in enumerate(PHASES):
        lbl.config(text=label, fg={"ready": "#e6e6e6", "still": "#ffb347", "walk": "#5ad16a"}[kind])
        root.update()
        if kind == "still":
            winsound.Beep(500, 600)
        elif kind == "walk":
            winsound.Beep(1200, 120); winsound.Beep(1200, 120)
        t0 = time.time()
        pending = list(at)
        while (el := time.time() - t0) < secs:
            if pending and el >= pending[0]:
                pending.pop(0)
                snaps.append((i, kind, snap()))
            sub.config(text=f"step {i}/{len(PHASES) - 1}   {secs - el:4.1f}s")
            root.update()
            time.sleep(0.05)
    winsound.Beep(900, 300)
    lbl.config(text="Done - analysing...", fg="#e6e6e6"); sub.config(text=""); root.update()
    analyse()
    root.destroy()


def analyse():
    by_phase = {}
    for i, kind, b in snaps:
        by_phase.setdefault(i, []).append(b)
    still = [i for i, (_, k, _, _) in enumerate(PHASES) if k == "still"]
    walk = [i for i, (_, k, _, _) in enumerate(PHASES) if k == "walk"]

    # moved between consecutive still phases
    cand = None
    for a, b in zip(still, still[1:]):
        d = diff(by_phase[a][-1], by_phase[b][0])
        cand = d if cand is None else cand & d
    print(f"changed between every still phase: {len(cand)}")
    # stable within each still phase
    for s in still:
        cand -= diff(by_phase[s][0], by_phase[s][1])
    print(f"... and stable while standing still: {len(cand)}")
    # changing while walking
    for w in walk:
        a, b = by_phase[w]
        cand = {o for o in cand if a[o:o + 4] != b[o:o + 4]}
    print(f"... and changing while walking: {len(cand)}")

    def f(b, o):
        return struct.unpack(">f", b[o:o + 4])[0]

    all_snaps = [b for _, _, b in snaps]
    good = {o for o in cand
            if all(math.isfinite(v := f(b, o)) and 1e-3 < abs(v) < 30000 for b in all_snaps)}
    print(f"... and plausible floats: {len(good)}")

    # x and z of one vec3 sit 8 bytes apart
    triples = sorted(o for o in good if o + 8 in good)
    res = []
    for o in triples:
        vals = [[round(f(b, o + k), 1) for k in (0, 4, 8)] for b in all_snaps]
        res.append({"host_addr": hex(base + o), "offset": hex(o), "snapshots_xyz": vals})
    singles = sorted(good - set(triples) - {o + 8 for o in triples})
    json.dump({"base": hex(base), "triples": res,
               "singles": [{"host_addr": hex(base + o), "vals": [round(f(b, o), 1) for b in all_snaps]}
                           for o in singles[:200]]},
              open(DIR + r"\hunter_candidates.json", "w"), indent=1)
    print(f"{len(res)} vec3 candidates, {len(singles)} single floats -> hunter_candidates.json")
    for r in res[:40]:
        print(r["host_addr"], " | ".join(",".join(f"{v:.0f}" for v in s) for s in r["snapshots_xyz"]))


root.after(200, run)
root.mainloop()
