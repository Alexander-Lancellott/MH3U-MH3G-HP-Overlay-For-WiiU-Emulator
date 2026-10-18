"""MH3U (Cemu) monster radar (read-only).

Top-down X/Z map of every active entity. Click a row to center the map on it
(e.g. your hunter).

Offsets relative to the HP field (hp_addr):
  +0x004  max HP (u16 BE)
  -0x816  size scale (f32 BE)
  -0x87A  position x, y, z (f32 BE, y is up)
  +0x527  area number (u8); switches to the destination as soon as the monster
          takes off. +0x526 holds the hunter's current area.
Small monsters only exist in the hunter's area, so their area is the hunter's.
"""
from collections import Counter
import math
import struct
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from mh3u_mem import Proc
from names import LARGE, SMALL

POS = -0x87A
SIZE = -0x816
AREA = 0x527
RESCAN_S = 3.0
TICK_MS = 150
MAP = 340
FLYING_Y = 800  # Rathian logged y≈1000-10500 while flying between areas, ≈-30..0 on the ground


class Radar:
    def __init__(self):
        self.p = Proc()
        self.entities = []          # from last scan
        self.hunter_obj = None      # hunter transform object (host addr)
        self.center_addr = None     # hp_addr the map is centered on; None = hunter
        self.lock = threading.Lock()
        threading.Thread(target=self.scan_loop, daemon=True).start()

        self.root = tk.Tk()
        self.root.title("MH3U Radar")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="#14161a")
        self.canvas = tk.Canvas(self.root, width=MAP, height=MAP, bg="#14161a", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)

        self.tree = ttk.Treeview(self.root, columns=("name", "area", "dist"), show="headings", height=8)
        for col, w in (("name", 150), ("area", 110), ("dist", 70)):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="x", padx=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        bar = tk.Frame(self.root, bg="#14161a")
        bar.pack(fill="x", padx=6, pady=6)
        for text, fn in (("Center here", self.center_selected), ("Center on me", self.clear_center)):
            tk.Button(bar, text=text, command=fn, bg="#2a2e35", fg="#e6e6e6", relief="flat").pack(side="left", padx=2)
        self.status = tk.Label(bar, text="", bg="#14161a", fg="#8a8f98")
        self.status.pack(side="right")
        self.selected = None
        self.root.after(TICK_MS, self.tick)

    # --- memory -----------------------------------------------------------
    def scan_loop(self):
        while True:
            try:
                found = self.p.find_monsters()
                hunter = self.p.find_hunter()
                with self.lock:
                    self.entities = found
                    self.hunter_obj = hunter
            except (OSError, SystemExit) as e:
                with self.lock:
                    self.entities = []
                self.err = str(e)
            time.sleep(RESCAN_S)

    def read_entity(self, e):
        a = e["hp_addr"]
        hp, _, mx = struct.unpack(">HHH", self.p.read(a, 6))
        x, y, z = self.p.floats(a + POS, 3)
        area = self.p.read(a + AREA, 1)[0]
        mid = e["id"]
        if mid in LARGE:
            kind, name = "large", LARGE[mid]
        elif mid in SMALL:
            kind, name = "small", SMALL[mid]
        else:
            kind, name = "other", f"id {mid}"
        return {"addr": a, "kind": kind, "name": name, "hp": hp, "max": mx, "x": x, "y": y, "z": z, "area": area}

    # --- ui ---------------------------------------------------------------
    def on_select(self, _):
        sel = self.tree.selection()
        self.selected = int(sel[0]) if sel else None

    def center_selected(self):
        self.center_addr = self.selected

    def clear_center(self):
        self.center_addr = None

    def tick(self):
        with self.lock:
            ents = list(self.entities)
            hobj = self.hunter_obj
        hunter = None
        if hobj:
            try:
                h = self.p.hunter(hobj)
                if all(map(math.isfinite, h)):
                    hunter = h
            except OSError:
                pass
        rows = []
        for e in ents:
            try:
                r = self.read_entity(e)
            except OSError:
                continue
            # Small-monster slots are pooled and reused per area; while they reload
            # they carry transitional IDs, max HP 0 and a (0,0,0)/NaN position.
            if (r["kind"] != "other" and r["max"] > 0
                    and all(map(math.isfinite, (r["x"], r["y"], r["z"])))
                    and (r["x"], r["y"], r["z"]) != (0.0, 0.0, 0.0)):
                rows.append(r)
        self.rows = rows
        self.draw(rows, hunter)
        self.root.after(TICK_MS, self.tick)

    def draw(self, rows, hunter):
        c = self.canvas
        c.delete("all")
        smalls = Counter(r["area"] for r in rows if r["kind"] == "small")
        my_area = smalls.most_common(1)[0][0] if smalls else None
        here = lambda r: my_area is None or r["area"] == my_area
        away = [r for r in rows if not here(r)]
        rows_all, rows = rows, [r for r in rows if here(r)]
        center = next((r for r in rows if r["addr"] == self.center_addr), None)
        if center is None and hunter:
            center = {"x": hunter[0], "z": hunter[2]}
        if center:
            cx, cz, span = center["x"], center["z"], 4000.0
        elif rows:
            xs, zs = [r["x"] for r in rows], [r["z"] for r in rows]
            cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
            span = max(max(xs) - min(xs), max(zs) - min(zs), 1500.0) * 1.2
        else:
            cx = cz = 0.0
            span = 4000.0
        scale = MAP / span

        for i in range(1, 4):  # range rings
            rad = MAP / 2 * i / 3
            c.create_oval(MAP / 2 - rad, MAP / 2 - rad, MAP / 2 + rad, MAP / 2 + rad, outline="#262a31")
        c.create_text(6, 6, anchor="nw", fill="#5b616b", text=f"{span / 2:.0f}u radius" if center else "auto-fit")

        colors = {"large": "#ff5a4f", "small": "#9aa0a6"}
        for r in sorted(rows, key=lambda r: r["kind"] == "large"):
            px = MAP / 2 + (r["x"] - cx) * scale
            py = MAP / 2 + (r["z"] - cz) * scale
            px, py = min(max(px, 4), MAP - 4), min(max(py, 4), MAP - 4)  # clamp to edge
            rad = 7 if r["kind"] == "large" else 4
            c.create_oval(px - rad, py - rad, px + rad, py + rad, fill=colors[r["kind"]], outline="")
            if r["addr"] == self.center_addr:
                c.create_oval(px - rad - 4, py - rad - 4, px + rad + 4, py + rad + 4, outline="#e6e6e6")
            if r["kind"] == "large":
                flying = "  ↑ airborne" if r["y"] > FLYING_Y else ""
                c.create_text(px + 9, py, anchor="w", fill="#e6e6e6", font=("Segoe UI", 8),
                              text=f"{r['name']} · Area {r['area']}{flying}")

        # large monsters in other areas: listed, not plotted (their coords are another area's)
        ly = MAP - 6
        for r in (r for r in away if r["kind"] == "large"):
            verb = "→" if r["y"] > FLYING_Y else "in"
            c.create_text(6, ly, anchor="sw", fill="#ff8a80", font=("Segoe UI", 9, "bold"),
                          text=f"{r['name']} {verb} Area {r['area']}")
            ly -= 16

        if hunter:  # green arrow pointing where the hunter faces
            hx = MAP / 2 + (hunter[0] - cx) * scale
            hy = MAP / 2 + (hunter[2] - cz) * scale
            fx, fz = hunter[3], hunter[4]
            n = math.hypot(fx, fz) or 1.0
            fx, fz = fx / n, fz / n
            tip = (hx + fx * 11, hy + fz * 11)
            left = (hx - fx * 6 - fz * 6, hy - fz * 6 + fx * 6)
            right = (hx - fx * 6 + fz * 6, hy - fz * 6 - fx * 6)
            c.create_polygon(*tip, *left, *right, fill="#5ad16a", outline="#14161a")

        # table
        keep = set()
        for r in rows_all:
            iid = str(r["addr"])
            keep.add(iid)
            d = math.dist((r["x"], r["z"]), (center["x"], center["z"])) if center and here(r) else None
            area = f"→ {r['area']} (flying)" if r["y"] > FLYING_Y else str(r["area"])
            vals = (r["name"], area, f"{d:.0f}" if d is not None else "-")
            if self.tree.exists(iid):
                self.tree.item(iid, values=vals)
            else:
                self.tree.insert("", "end", iid=iid, values=vals)
        for iid in self.tree.get_children():
            if iid not in keep:
                self.tree.delete(iid)
        self.status.config(text=f"You: Area {my_area}" if my_area is not None else "You: area ?")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Radar().run()
