"""Read-only: tiny topmost window showing the game's internal area number for the hunter.

Type the map number shown in-game and press Enter to save "game area -> map" for the
current location into area_map.json (the only file this writes; nothing is written to the game).

Source: hunter object +0xE95 (location) / +0xE96 (area).
"""
import json, sys, threading, time
import tkinter as tk
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
from mh3u_mem import Proc, HUNTER_CLASS, HUNTER_PTR

MAP_FILE = DIR + r"\area_map.json"
p = Proc()
state = {"hunter": None}


def scan():
    while True:
        try:
            ptr = int.from_bytes(p.read(p.g2h(HUNTER_PTR), 4), "big")
            h = p.g2h(ptr) if ptr else None
            if h and p.read(h, 4) == HUNTER_CLASS:
                state["hunter"] = h
            # in the hub the pointer is empty: keep the found object while it is still valid,
            # since the full-memory fallback is slow
            elif not state["hunter"] or p.read(state["hunter"], 4) != HUNTER_CLASS:
                state["hunter"] = p.find_hunter()
        except BaseException as e:  # never let the reader thread die
            print("scan:", repr(e), flush=True)
            state["hunter"] = None
        time.sleep(2)


def current():
    """(location, area) or None."""
    h = state["hunter"]
    if h:
        try:
            loc, area = p.read(h + 0xE95, 2)
            return loc, area
        except OSError:
            pass
    return None


def load():
    with open(MAP_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    # one line per location's areas, like the hand-written file
    def key(k): return (0, int(k)) if k.isdigit() else (-1, 0)
    lines = []
    for k in sorted(data, key=key):
        v = data[k]
        if isinstance(v, dict):
            areas = {a: v["areas"][a] for a in sorted(v.get("areas", {}), key=int)}
            body = (f'{{\n    "name": {json.dumps(v["name"])},\n    "areas": {json.dumps(areas)}\n  }}'
                    if areas else f'{{"name": {json.dumps(v["name"])}, "areas": {{}}}}')
        else:
            body = json.dumps(v)
        lines.append(f"  {json.dumps(k)}: {body}")
    with open(MAP_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(lines) + "\n}\n")


BG, FG, DIM = "#14161a", "#5ad16a", "#8a8f98"
root = tk.Tk()
root.title("Area ID")
root.attributes("-topmost", True)
root.geometry("+40+40")
root.configure(bg=BG)
lbl = tk.Label(root, font=("Segoe UI", 28, "bold"), bg=BG, fg=FG, padx=24, pady=6)
lbl.pack()
info = tk.Label(root, font=("Segoe UI", 10), bg=BG, fg=DIM)
info.pack()
row = tk.Frame(root, bg=BG)
row.pack(pady=6)
tk.Label(row, text="map #", font=("Segoe UI", 10), bg=BG, fg=DIM).pack(side="left", padx=(0, 6))
entry = tk.Entry(row, width=4, font=("Segoe UI", 14), justify="center")
entry.pack(side="left")
status = tk.Label(root, font=("Segoe UI", 9), bg=BG, fg=DIM, wraplength=220, justify="center")
status.pack(padx=10, pady=(0, 8))


def submit(_=None):
    text = entry.get().strip()
    entry.delete(0, "end")
    cur = current()
    if not text.isdigit():
        status.config(text="type a number, then Enter"); return
    if not cur or not cur[1]:
        status.config(text="not in a quest area"); return
    loc, area = cur
    data = load()
    entry_ = data.setdefault(str(loc), {"name": f"location {loc}", "areas": {}})
    old = entry_["areas"].get(str(area))
    entry_["areas"][str(area)] = int(text)
    save(data)
    status.config(text=f"saved game {area} → map {text}" + (f" (was {old})" if old not in (None, int(text)) else ""))


entry.bind("<Return>", submit)


def tick():
    cur = current()
    if cur and cur[1]:
        loc, area = cur
        try:
            loc_data = load().get(str(loc), {})
        except (OSError, ValueError):
            loc_data = {}
        areas = loc_data.get("areas", {})
        known = areas.get(str(area))
        lbl.config(text=f"{area}")
        info.config(text=f"{loc_data.get('name', f'location {loc}')} · map {known if known is not None else '?'}"
                         f" · {len(areas)} mapped")
    else:
        lbl.config(text="?")
        info.config(text="hub / loading" if cur else "hunter not found")
    root.after(300, tick)


threading.Thread(target=scan, daemon=True).start()
tick()
root.mainloop()
