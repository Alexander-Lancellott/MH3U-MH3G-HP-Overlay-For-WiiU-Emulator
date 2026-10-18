"""Disassemble guest PPC code from live Cemu memory (needs: pip install capstone).
usage: ppcdis.py ADDR [BEFORE] [AFTER]  (hex guest addr, counts in instructions)"""
import sys
DIR = __file__.rsplit("\\", 1)[0]
sys.path.insert(0, DIR)
import capstone
from mh3u_mem import Proc

p = Proc()
md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN)


def dis(addr, before=40, after=30, mark=None):
    start = addr - 4 * before
    code = p.read(p.g2h(start), 4 * (before + after))
    for i in md.disasm(code, start):
        flag = ">>" if i.address == (mark if mark is not None else addr) else "  "
        print(f"{flag} {i.address:08x}: {i.bytes.hex()}  {i.mnemonic:8s} {i.op_str}")


if __name__ == "__main__":
    a = int(sys.argv[1], 16)
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    c = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    dis(a, b, c)
