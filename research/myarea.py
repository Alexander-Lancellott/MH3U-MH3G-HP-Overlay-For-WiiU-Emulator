import sys
from collections import Counter
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from mh3u_mem import Proc
from names import SMALL
p = Proc(); o = p.find_hunter()
sm = Counter(p.read(e["hp_addr"] + 0x527, 1)[0] for e in p.find_monsters() if e["id"] in SMALL and p.u16(e["hp_addr"] + 4))
print("hunter area:", p.read(o + 0xE96, 1)[0], " map?:", p.read(o + 0xE95, 1)[0], " small monsters:", dict(sm))
