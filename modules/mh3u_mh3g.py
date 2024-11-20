import time
from struct import unpack
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymem
import scanmodule
import numpy as np
from ahk import AHK


@dataclass
class Monsters:
    large_monsters = {
        257: {
            "name": "Rathian",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        258: {
            "name": "Rathalos",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        259: {
            "name": "Qurupeco",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        260: {
            "name": "Gigginox",
            "crowns": {"g": 116, "s": 111, "m": 92}
        },
        261: {
            "name": "Barioth",
            "crowns": {"g": 116, "s": 111, "m": 92}
        },
        262: {
            "name": "Diablos",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        263: {
            "name": "Deviljho",
            "crowns": {"g": 128, "s": 120, "m": 90}
        },
        264: {
            "name": "Barroth",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        265: {
            "name": "Uragaan",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        268: {
            "name": "Great Jaggi",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        270: {
            "name": "Great Baggi",
            "crowns": {"g": 137, "s": 125, "m": 83}
        },
        271: {
            "name": "Lagiacrus",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        272: {
            "name": "Royal Ludroth",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        274: {
            "name": "Gobul",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        275: {
            "name": "Agnaktor",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        276: {
            "name": "Ceadeus",
            "crowns": {"g": None, "s": None, "m": None}
        },
        280: {
            "name": "Alatreon",
            "crowns": {"g": None, "s": None, "m": None}
        },
        281: {
            "name": "Jhen Mohran",
            "crowns": {"g": None, "s": None, "m": None}
        },
        297: {
            "name": "Zinogre",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        298: {
            "name": "Arzuros",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        299: {
            "name": "Lagombi",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        300: {
            "name": "Volvidon",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        301: {
            "name": "Great Wroggi",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        302: {
            "name": "Duramboros",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        303: {
            "name": "Nibelsnarf",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        307: {
            "name": "Crimson Qurupeco",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        308: {
            "name": "Baleful Gigginox",
            "crowns": {"g": 116, "s": 111, "m": 92}
        },
        309: {
            "name": "Sand Barioth",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        310: {
            "name": "Jade Barroth",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        311: {
            "name": "Steel Uragaan",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        312: {
            "name": "Purple Ludroth",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        313: {
            "name": "Glacial Agnaktor",
            "crowns": {"g": 116, "s": 111, "m": 92}
        },
        314: {
            "name": "Black Diablos",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        315: {
            "name": "Nargacuga",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        316: {
            "name": "Green Nargacuga",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        317: {
            "name": "Lucent Nargacuga",
            "crowns": {"g": None, "s": None, "m": None}
        },
        318: {
            "name": "Pink Rathian",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        319: {
            "name": "Gold Rathian",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        320: {
            "name": "Azure Rathalos",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        321: {
            "name": "Silver Rathalos",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        322: {
            "name": "Plesioth",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        323: {
            "name": "Green Plesioth",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        324: {
            "name": "Ivory Lagiacrus",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        325: {
            "name": "Abyssal Lagiacrus",
            "crowns": {"g": None, "s": None, "m": None}
        },
        326: {
            "name": "Goldbeard Ceadeus",
            "crowns": {"g": None, "s": None, "m": None}
        },
        327: {
            "name": "Savage Deviljho",
            "crowns": {"g": 128, "s": 120, "m": 90}
        },
        328: {
            "name": "Stygian Zinogre",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        329: {
            "name": "Rust Duramboros",
            "crowns": {"g": 123, "s": 117, "m": 98}
        },
        330: {
            "name": "Brachydios",
            "crowns": {"g": 123, "s": 115, "m": 90}
        },
        331: {
            "name": "Dire Miralis",
            "crowns": {"g": None, "s": None, "m": None}
        },
        341: {
            "name": "Hallowed Jhen Mohran",
            "crowns": {"g": None, "s": None, "m": None}
        },
    }

    small_monsters = {
        266: "Jaggi",
        267: "Jaggia",
        269: "Baggi",
        273: "Ludroth",
        277: "Uroktor",
        278: "Delex",
        279: "Epioth",
        282: "Giggi",
        283: "Aptonoth",
        284: "Popo",
        285: "Rhenoplos",
        286: "Felyne",
        287: "Melynx",
        288: "Fish",
        289: "Altaroth",
        290: "Kelbi",
        291: "Giggi Sac",
        292: "Bnahabra",
        293: "Bnahabra",
        294: "Bnahabra",
        295: "Bnahabra",
        296: "Rock",
        304: "Wroggi",
        305: "Slagtoth",
        306: "Gargwa",
        332: "Bullfango",
        333: "Anteka",
        334: "Slagtoth",
        335: "Rock",
        336: "Rock",
        337: "Rock",
        338: "Rock",
        339: "Rock",
        340: "Rock",
    }


def read_int(process_handle, address, length=2, little=True):
    return int.from_bytes(pymem.memory.read_bytes(process_handle, address, length), 'little' if little else 'big')


def read_float(process_handle, address, length=4):
    return unpack('>f', pymem.memory.read_bytes(process_handle, address, length))[0]


def scan_aob_batched(
        process_handle,
        base_address,
        pattern, scan_size,
        show_small_monsters,
        num_chunks=400,
        max_workers=2
):
    large_monster_results = []
    small_monster_results = []
    try:
        wildcard = "??"
        bytes_pattern = bytes(int(byte, 16) if byte != wildcard else 0x00 for byte in pattern.split())
        pattern_np = np.frombuffer(bytes_pattern, dtype=np.uint8)
        mask = np.array([0xFF if byte != wildcard else 0x00 for byte in pattern.split()], dtype=np.uint8)
        chunk_size = scan_size // num_chunks

        large_monsters = Monsters.large_monsters
        small_monsters = Monsters.small_monsters if show_small_monsters else {}

        results = []
        with ThreadPoolExecutor(max_workers) as executor:
            futures = []
            for i in range(num_chunks):
                chunk_offset = i * chunk_size
                memory_chunk = pymem.memory.read_bytes(process_handle, base_address + chunk_offset, chunk_size)
                futures.append(
                    executor.submit(scanmodule.scan_chunk, memory_chunk, pattern_np, mask, base_address, chunk_offset)
                )

            for future in as_completed(futures):
                results.extend(future.result())

        results.sort(key=lambda x: x[0])

        for result in results:
            name = read_int(process_handle, result[0])
            hp = read_int(process_handle, result[1], little=False)
            initial_hp = read_int(process_handle, result[2], little=False)
            is_visible = read_int(process_handle, result[1] + 0x148, 2) == 0xE803
            monster_name = large_monsters.get(name)
            if is_visible:
                if monster_name:
                    monster_size = int(round(read_float(process_handle, result[1] - 0x816) * 100, 2))
                    large_monster_results.append([name, hp, initial_hp, monster_size, result[1]])
                elif show_small_monsters:
                    monster_name = small_monsters.get(name)
                    if monster_name:
                        small_monster_results.append([name, hp, initial_hp, result[1]])
    except (Exception,):
        pass
    return large_monster_results + small_monster_results


def get_base_address(process_name):
    return scanmodule.get_regions(process_name, 0x4E000000) + 0x2CF00000


def get_data(pid, base_address, only_large_monsters, workers=2):
    process_handle = pymem.process.open(pid)
    # pointer - 0x131 = HP
    # pattern = "FF ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? 00 03 E8"
    # pointer + 0x12 = HP
    # pattern = "FF ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? 00 00 ?? ?? 00 00 ?? ?? 3F 80 00 00 00 00"
    # pointer + 0x8A = HP
    pattern = "3C F5 C2 8F 00 00 00 00 00 00 00 00 00 00 00 00"
    scan_size = 0x3B00000  # 0x3B00000  # 0x9BBF000 or 7BBF000
    if process_handle:
        return scan_aob_batched(
            process_handle, base_address, pattern, scan_size, only_large_monsters, max_workers=workers
        )
    else:
        return []


if __name__ == "__main__":
    class Test:
        start = time.time()
        ahk = AHK(version="v2")
        target_window_title = "Cemu.*?MH3(U|G HD Ver\\.) \\[.*?\\]"
        not_responding_title = " \\([\\w\\s]+\\)$"
        win = None
        is_xx = False
        base_address = None
        not_responding = ahk.find_window(
            title=target_window_title + not_responding_title, title_match_mode="RegEx"
        )
        if not not_responding:
            win = ahk.find_window(title=target_window_title, title_match_mode="RegEx")
        if win:
            base_address = get_base_address(win.process_name)
            monsters = get_data(win.pid, base_address, True)
            for monster in monsters:
                if monster[2] > 5:
                    large_monster = Monsters.large_monsters.get(monster[0])
                    small_monster_name = Monsters.small_monsters.get(monster[0])
                    if large_monster:
                        print([large_monster["name"], *monster[1::]])
                    if small_monster_name:
                        print([small_monster_name, *monster[1::]])
        end = time.time()
        print(end - start)

    Test()
