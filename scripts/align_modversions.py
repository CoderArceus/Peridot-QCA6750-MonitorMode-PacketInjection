#!/usr/bin/env python3
"""
align_modversions.py

Aligns the symbol CRC table (__versions) of a rebuilt Linux kernel module with
the exact CRCs from stock OEM modules (CONFIG_MODVERSIONS=y).
"""

import argparse
import glob
import os
import struct
import sys
from elftools.elf.elffile import ELFFile

ENTRY_SIZE = 64  # struct modversion_info: 8 bytes unsigned long crc + 56 bytes char name

def extract_versions_from_ko(path):
    symbols = {}
    try:
        with open(path, 'rb') as f:
            elf = ELFFile(f)
            sec = elf.get_section_by_name('__versions')
            if not sec:
                return {}
            data = sec.data()
            for i in range(0, len(data), ENTRY_SIZE):
                chunk = data[i:i + ENTRY_SIZE]
                if len(chunk) < ENTRY_SIZE:
                    break
                crc = struct.unpack('<Q', chunk[:8])[0]
                name = chunk[8:].split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                if name:
                    symbols[name] = crc
    except Exception as e:
        pass
    return symbols

def collect_stock_symbol_crcs(stock_ko, search_dirs):
    crc_map = {}
    if stock_ko and os.path.exists(stock_ko):
        stock_crcs = extract_versions_from_ko(stock_ko)
        print(f"Loaded {len(stock_crcs)} symbols from OEM stock module: {stock_ko}")
        crc_map.update(stock_crcs)

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        count = 0
        for root, _, files in os.walk(sdir):
            for file in files:
                if file.endswith('.ko'):
                    p = os.path.join(root, file)
                    mod_crcs = extract_versions_from_ko(p)
                    for k, v in mod_crcs.items():
                        if k not in crc_map:
                            crc_map[k] = v
                            count += 1
        print(f"Added {count} new symbols from directory: {sdir}")

    print(f"Total reference stock symbols available: {len(crc_map)}")
    return crc_map

def align_module_crcs(target_ko, stock_crc_map, output_ko=None):
    if not output_ko:
        output_ko = target_ko

    with open(target_ko, 'rb') as f:
        file_bytes = bytearray(f.read())

    from io import BytesIO
    elf = ELFFile(BytesIO(file_bytes))
    sec = elf.get_section_by_name('__versions')
    if not sec:
        raise ValueError(f"No __versions section found in {target_ko}!")

    sh_offset = sec['sh_offset']
    sh_size = sec['sh_size']
    num_entries = sh_size // ENTRY_SIZE
    print(f"Target module has {num_entries} symbols in __versions (offset 0x{sh_offset:x}, size {sh_size} bytes)")

    matched_count = 0
    updated_count = 0
    missing = []

    for idx in range(num_entries):
        entry_offset = sh_offset + (idx * ENTRY_SIZE)
        chunk = file_bytes[entry_offset:entry_offset + ENTRY_SIZE]
        current_crc = struct.unpack('<Q', chunk[:8])[0]
        sym_name = chunk[8:].split(b'\x00', 1)[0].decode('utf-8', errors='ignore')

        if sym_name in stock_crc_map:
            stock_crc = stock_crc_map[sym_name]
            matched_count += 1
            if current_crc != stock_crc:
                # Overwrite CRC in-place in file_bytes
                file_bytes[entry_offset:entry_offset + 8] = struct.pack('<Q', stock_crc)
                updated_count += 1
                # print(f"  [CRC FIX] {sym_name}: 0x{current_crc:016x} -> 0x{stock_crc:016x}")
            else:
                pass
        else:
            missing.append((sym_name, current_crc))

    print(f"Alignment Summary:")
    print(f"  Total imported symbols: {num_entries}")
    print(f"  Matched with stock CRCs: {matched_count}/{num_entries} ({matched_count/num_entries*100:.1f}%)")
    print(f"  CRCs updated (were mismatched): {updated_count}")
    print(f"  Symbols already identical: {matched_count - updated_count}")

    if missing:
        print(f"  WARNING: {len(missing)} symbols NOT found in stock tables:")
        for sym, crc in missing:
            print(f"    - {sym} (current CRC: 0x{crc:016x})")
        raise RuntimeError(f"Cannot produce safe module: {len(missing)} missing stock symbol CRCs!")

    # Write output file
    with open(output_ko, 'wb') as f:
        f.write(file_bytes)
    print(f"Successfully wrote aligned module to: {output_ko}")

    # Verification read
    verify_versions = extract_versions_from_ko(output_ko)
    mismatches = 0
    for sym, crc in verify_versions.items():
        if stock_crc_map.get(sym) != crc:
            mismatches += 1
    if mismatches == 0:
        print(f"VERIFICATION PASSED: 100% of symbols in {output_ko} match OEM stock CRCs!")
    else:
        raise RuntimeError(f"VERIFICATION FAILED: {mismatches} mismatches remain!")

def main():
    parser = argparse.ArgumentParser(description="Align Linux module __versions with OEM stock CRCs")
    parser.add_argument("--target", required=True, help="Path to built target .ko")
    parser.add_argument("--stock", help="Path to OEM stock .ko")
    parser.add_argument("--search-dirs", nargs="*", default=[], help="Directories containing companion .ko files")
    parser.add_argument("--output", help="Path to output .ko (default: overwrite target)")
    args = parser.parse_args()

    stock_map = collect_stock_symbol_crcs(args.stock, args.search_dirs)
    align_module_crcs(args.target, stock_map, args.output)

if __name__ == '__main__':
    main()

