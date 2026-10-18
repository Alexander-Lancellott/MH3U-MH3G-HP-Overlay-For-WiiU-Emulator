"""Minimal Cemu/MH3U memory access via ctypes (no third-party deps).

Monster layout (from MH3U-MH3G-HP-Overlay): pattern match M, HP = M+0x8A.
All game data is big-endian.
"""
import ctypes as C
import ctypes.wintypes as W
import struct
import subprocess

k32 = C.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400
MEM_COMMIT = 0x1000

PATTERN = bytes.fromhex("3CF5C28F000000000000000000000000")
GUEST_OFFSET = 0x02000000          # guest address = host - emu_base + this
HUNTER_PTR = 0x10547BF0            # static: -> hunter transform object
HUNTER_CLASS = bytes.fromhex("1007F1A0")  # that object's vtable (unique in memory)
HUNTER_POS = 0x40                  # pos x,y,z; facing = matrix row at +0x50 (x) / +0x58 (z)
REGION_SIZE = 0x4E000000
BASE_OFFSET = 0x2CF00000
SCAN_SIZE = 0x3B00000


class MBI(C.Structure):
    _fields_ = [("BaseAddress", C.c_void_p), ("AllocationBase", C.c_void_p),
                ("AllocationProtect", W.DWORD), ("PartitionId", W.WORD),
                ("RegionSize", C.c_size_t), ("State", W.DWORD),
                ("Protect", W.DWORD), ("Type", W.DWORD)]


k32.OpenProcess.restype = W.HANDLE
k32.VirtualQueryEx.argtypes = [W.HANDLE, C.c_void_p, C.POINTER(MBI), C.c_size_t]
k32.VirtualQueryEx.restype = C.c_size_t
k32.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]


def cemu_pid():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Cemu.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.strip('"').split('","')
        if parts[0].lower() == "cemu.exe":
            return int(parts[1])
    raise SystemExit("Cemu.exe is not running")


class Proc:
    def __init__(self):
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, cemu_pid())
        if not self.h:
            raise OSError(C.get_last_error(), "OpenProcess failed")

    def read(self, addr, n):
        buf = C.create_string_buffer(n)
        got = C.c_size_t()
        if not k32.ReadProcessMemory(self.h, C.c_void_p(addr), buf, n, C.byref(got)):
            raise OSError(C.get_last_error(), f"read @{addr:#x}")
        return buf.raw[:got.value]

    def u16(self, a): return struct.unpack(">H", self.read(a, 2))[0]
    def f32(self, a): return struct.unpack(">f", self.read(a, 4))[0]
    def floats(self, a, n): return struct.unpack(f">{n}f", self.read(a, 4 * n))

    def emu_base(self):
        """Host address of the region the overlay uses (size 0x4E000000)."""
        addr, mbi = 0, MBI()
        while k32.VirtualQueryEx(self.h, C.c_void_p(addr), C.byref(mbi), C.sizeof(mbi)):
            if mbi.State == MEM_COMMIT and mbi.RegionSize == REGION_SIZE:
                return mbi.BaseAddress
            addr = (mbi.BaseAddress or 0) + mbi.RegionSize
        raise SystemExit("Emulated memory region not found (is MH3U in-game?)")

    def g2h(self, guest):
        return guest - GUEST_OFFSET + self.emu_base()

    def find_hunter(self):
        """Host address of the hunter transform object, or None."""
        try:
            obj = self.g2h(struct.unpack(">I", self.read(self.g2h(HUNTER_PTR), 4))[0])
            if self.read(obj, 4) == HUNTER_CLASS:
                return obj
        except OSError:
            pass
        # fallback: the class pointer only appears once
        base = self.emu_base()
        for off in range(0, REGION_SIZE, 0x4000000):
            try:
                d = self.read(base + off, 0x4000000)
            except OSError:
                continue
            i = d.find(HUNTER_CLASS)
            while i != -1:
                if i % 4 == 0 and base + off + i - base + GUEST_OFFSET >= 0x20000000:
                    return base + off + i
                i = d.find(HUNTER_CLASS, i + 1)
        return None

    def hunter(self, obj):
        """(x, y, z, face_x, face_z) of the hunter object."""
        x, y, z = self.floats(obj + HUNTER_POS, 3)
        fx, _, fz = self.floats(obj + HUNTER_POS + 0x50, 3)
        return x, y, z, fx, fz

    def find_monsters(self):
        base = self.emu_base() + BASE_OFFSET
        data = self.read(base, SCAN_SIZE)
        out, i = [], data.find(PATTERN)
        while i != -1:
            hp_addr = base + i + 0x8A
            try:
                if self.read(hp_addr + 0x148, 2) == b"\x03\xe8":
                    mid = int.from_bytes(self.read(hp_addr - 0x8B7, 2), "little")
                    out.append({"id": mid, "hp_addr": hp_addr,
                                "hp": self.u16(hp_addr), "max": self.u16(hp_addr + 4)})
            except OSError:
                pass
            i = data.find(PATTERN, i + 1)
        return out
