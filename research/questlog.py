"""Read-only quest logger: hunter location/area/position and every large monster's area,
position and HP, until Ctrl+C. Writes questlog.csv next to this script (one row per entity per sample).
"""
import csv, sys, time
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
from mh3u_mem import Proc
from names import LARGE

SAMPLE, RESCAN = 0.5, 3.0
p = Proc()
t0 = time.time(); last_scan = -99; ents = []; hunter = None; last = None
with open(DIR + r"\questlog.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t", "who", "id", "loc", "area", "hunter_area", "x", "y", "z", "hp", "max"])
    try:
        while True:
            t = time.time() - t0
            if t - last_scan >= RESCAN:
                try:
                    hunter = p.find_hunter()
                    ents = [e for e in p.find_monsters() if e["id"] in LARGE]
                except (OSError, SystemExit) as e:
                    print(f"{t:7.1f} scan failed: {e}", flush=True); hunter, ents = None, []
                last_scan = t
            loc = None
            if hunter:
                try:
                    loc, area = p.read(hunter + 0xE95, 2)
                    x, y, z = p.floats(hunter + 0x40, 3)
                    w.writerow([f"{t:.1f}", "hunter", "", loc, area, area, f"{x:.0f}", f"{y:.0f}", f"{z:.0f}", "", ""])
                except OSError:
                    hunter = None
            for e in ents:
                a = e["hp_addr"]
                try:
                    x, y, z = p.floats(a - 0x87A, 3)
                    area, harea = p.read(a + 0x527, 1)[0], p.read(a + 0x526, 1)[0]
                    w.writerow([f"{t:.1f}", hex(a), e["id"], loc, area, harea,
                                f"{x:.0f}", f"{y:.0f}", f"{z:.0f}", p.u16(a), p.u16(a + 4)])
                except OSError:
                    pass
            status = (loc, len(ents))
            if status != last:
                print(f"{t:7.1f} location={loc} large monsters={len(ents)}", flush=True); last = status
            f.flush()
            time.sleep(SAMPLE)
    except KeyboardInterrupt:
        pass
print("saved", DIR + r"\questlog.csv")
