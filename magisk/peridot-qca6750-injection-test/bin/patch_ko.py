#!/usr/bin/env python3
"""
ELF64 Vermagic & Symbol CRC Patcher for Peridot QCA6750 Module
Allows loading the injection driver on any Android 17 / Linux 6.1 kernel build
by dynamically transplanting __versions CRCs and patching .modinfo vermagic.
"""

import os
import sys
import struct
import subprocess

STOCK_CANDIDATES = [
    "/vendor_dlkm/lib/modules/qca_cld3_qca6750.ko",
    "/vendor/lib/modules/qca_cld3_qca6750.ko",
    "/system_dlkm/lib/modules/qca_cld3_qca6750.ko",
    "/data/adb/modules/peridot-qca6750-injection-test/stock_ref.ko"
]
BACKUP_STOCK = "/data/adb/modules/peridot-qca6750-injection-test/stock_ref.ko"


def get_sections(data):
    e_shoff = struct.unpack_from("<Q", data, 40)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 58)
    shstr_sh = e_shoff + e_shstrndx * e_shentsize
    shstr_off = struct.unpack_from("<Q", data, shstr_sh + 24)[0]
    sections = []
    for i in range(e_shnum):
        sh = e_shoff + i * e_shentsize
        name_idx = struct.unpack_from("<I", data, sh)[0]
        end = data.find(b"\x00", shstr_off + name_idx)
        name = data[shstr_off + name_idx:end].decode("latin1")
        off, size = struct.unpack_from("<QQ", data, sh + 24)
        sections.append({
            "idx": i,
            "sh_pos": sh,
            "name": name,
            "off": off,
            "size": size
        })
    return e_shoff, e_shentsize, e_shnum, sections


def find_stock_ko():
    if os.path.exists(BACKUP_STOCK):
        return BACKUP_STOCK
    for cand in STOCK_CANDIDATES:
        if os.path.exists(cand):
            try:
                os.makedirs(os.path.dirname(BACKUP_STOCK), exist_ok=True)
                with open(cand, "rb") as src, open(BACKUP_STOCK, "wb") as dst:
                    dst.write(src.read())
            except Exception:
                pass
            return cand
    return None


def patch_ko(inj_path, target_krel=None):
    if not target_krel:
        try:
            target_krel = subprocess.check_output(["uname", "-r"]).decode().strip()
        except Exception:
            target_krel = "6.1.176-g7fee93174ed9"

    ref_ko = find_stock_ko()
    with open(inj_path, "rb") as f:
        inj = bytearray(f.read())

    e_shoff, e_shentsize, e_shnum, inj_secs = get_sections(inj)

    # Step A: Transplant __versions symbol CRCs from stock driver if available
    crc_patched = 0
    if ref_ko and os.path.exists(ref_ko):
        with open(ref_ko, "rb") as f:
            stock = bytearray(f.read())
        _, _, _, stock_secs = get_sections(stock)
        s_ver = next((s for s in stock_secs if s["name"] == "__versions"), None)
        i_ver = next((s for s in inj_secs if s["name"] == "__versions"), None)
        if s_ver and i_ver:
            crc_map = {}
            for pos in range(s_ver["off"], s_ver["off"] + s_ver["size"], 64):
                crc = struct.unpack_from("<Q", stock, pos)[0]
                sym = stock[pos+8:pos+64].split(b"\x00", 1)[0].decode("latin1")
                if sym:
                    crc_map[sym] = crc
            for pos in range(i_ver["off"], i_ver["off"] + i_ver["size"], 64):
                old_crc = struct.unpack_from("<Q", inj, pos)[0]
                sym = inj[pos+8:pos+64].split(b"\x00", 1)[0].decode("latin1")
                if sym in crc_map and crc_map[sym] != old_crc:
                    struct.pack_into("<Q", inj, pos, crc_map[sym])
                    crc_patched += 1
        print(f"[+] Stock symbol CRCs synced from '{ref_ko}': {crc_patched} updated")
    else:
        print("[*] No stock reference module found for CRC sync; preserving pre-aligned CRCs.")

    # Step B: ELF64-safe .modinfo vermagic replacement with section offset recalculation
    mod_sec = next((s for s in inj_secs if s["name"] == ".modinfo"), None)
    if not mod_sec:
        print("[-] .modinfo section not found!")
        sys.exit(1)

    old_off, old_sz = mod_sec["off"], mod_sec["size"]
    mod_bytes = bytes(inj[old_off:old_off + old_sz])
    entries = mod_bytes.split(b"\x00")
    new_entries = []
    old_vm = ""
    new_vm = ""

    for e in entries:
        if e.startswith(b"vermagic="):
            old_vm = e.decode("latin1")
            parts = old_vm.split(" ", 1)
            suffix = (" " + parts[1]) if len(parts) > 1 else " SMP preempt mod_unload modversions aarch64"
            new_vm = f"vermagic={target_krel}{suffix}"
            new_entries.append(new_vm.encode("latin1"))
        else:
            new_entries.append(e)

    new_mod_raw = b"\x00".join(new_entries)
    rem = (len(new_mod_raw) - old_sz) % 8
    if rem != 0:
        new_mod_raw += b"\x00" * (8 - rem)
    delta = len(new_mod_raw) - old_sz

    for s in inj_secs:
        if s["idx"] == mod_sec["idx"]:
            struct.pack_into("<Q", inj, s["sh_pos"] + 32, len(new_mod_raw))
        elif s["off"] > old_off:
            struct.pack_into("<Q", inj, s["sh_pos"] + 24, s["off"] + delta)

    if e_shoff > old_off:
        struct.pack_into("<Q", inj, 40, e_shoff + delta)

    inj[old_off:old_off + old_sz] = new_mod_raw

    with open(inj_path, "wb") as f:
        f.write(inj)

    print(f"[+] Vermagic patched: '{old_vm}' -> '{new_vm}'")

    # Step C: Update helper scripts with target kernel release
    mod_dir = os.path.dirname(os.path.abspath(inj_path))
    for rel_path in ["system/bin/peridot-wlan-mode", "system/bin/pwm", "peridot-wlan-mode", "pwm"]:
        script_file = os.path.join(mod_dir, rel_path)
        if os.path.isfile(script_file):
            try:
                content = open(script_file, "r").read()
                new_content = re.sub(
                    r'EXPECTED_RELEASE="[^"]*"',
                    f'EXPECTED_RELEASE="{target_krel}"',
                    content
                )
                if new_content != content:
                    open(script_file, "w").write(new_content)
            except Exception:
                pass


if __name__ == "__main__":
    import re
    target_module = sys.argv[1] if len(sys.argv) > 1 else "/data/adb/modules/peridot-qca6750-injection-test/qca_cld3_qca6750.ko"
    target_kernel = sys.argv[2] if len(sys.argv) > 2 else None
    patch_ko(target_module, target_kernel)
