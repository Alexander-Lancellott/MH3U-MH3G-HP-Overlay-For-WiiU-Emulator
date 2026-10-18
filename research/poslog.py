"""Read-only 2-minute position logger. Writes poslog.csv next to this script."""
import csv, sys, time
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
from mh3u_mem import Proc

DURATION, SAMPLE, RESCAN = 120, 0.25, 2.0
p = Proc()
t0 = time.time(); last_scan = -99; ents = []
with open(DIR + r"\poslog.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t", "addr", "id", "hp", "max", "x", "y", "z", "x2", "y2", "z2", "hx", "hy", "hz", "size"])
    while (t := time.time() - t0) < DURATION:
        if t - last_scan >= RESCAN:
            try:
                ents = p.find_monsters()
            except (OSError, SystemExit) as e:
                print(f"{t:6.1f} scan failed: {e}", flush=True); ents = []
            last_scan = t
        for e in ents:
            a = e["hp_addr"]
            try:
                pos = p.floats(a - 0x87A, 3); prev = p.floats(a - 0x86A, 3)
                home = p.floats(a - 0x83A, 3); size = p.f32(a - 0x816)
                w.writerow([f"{t:.2f}", hex(a), e["id"], p.u16(a), p.u16(a + 4),
                            *(f"{v:.2f}" for v in (*pos, *prev, *home)), f"{size:.3f}"])
            except OSError:
                pass
        time.sleep(SAMPLE)
print("done", flush=True)
