#!/usr/bin/env python3
"""Replace the kernel in a v4 Android boot image and clear stale AVB data."""

from __future__ import annotations

import argparse
import pathlib
import struct


# Debug kernel command line to inject (overrides stock empty cmdline)
DEBUG_CMDLINE = (
    "earlyprintk loglevel=8 initcall_debug "
    "console=ttyMSM0,115200n8 "
    "androidboot.boot_devices=soc/1d84000.ufshc "
    "printk.devkmsg=on "
    "ignore_loglevel "
    "kpti=off "
    "page_poison=off "
    "slub_debug=FZPU "
    "androidboot.hardware=qcom "
    "androidboot.selinux=permissive"
)


def inject_cmdline(boot: bytearray, cmdline: str) -> None:
    """Inject cmdline into v4 boot header at offset 64 (512 bytes)."""
    cmdline_bytes = cmdline.encode('ascii') + b'\0'
    if len(cmdline_bytes) > 512:
        raise SystemExit(f"Cmdline too long: {len(cmdline_bytes)} > 512")
    boot[64:64+len(cmdline_bytes)] = cmdline_bytes
    # Clear rest of cmdline area
    boot[64+len(cmdline_bytes):64+512] = b'\0' * (512 - len(cmdline_bytes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stock_boot", type=pathlib.Path)
    parser.add_argument("kernel_image", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--debug-cmdline", action="store_true",
                        help="Inject debug kernel command line (earlyprintk, loglevel=8, etc.)")
    parser.add_argument("--cmdline", type=str, default=None,
                        help="Custom kernel command line to inject")
    args = parser.parse_args()

    boot = bytearray(args.stock_boot.read_bytes())
    kernel = args.kernel_image.read_bytes()
    if boot[:8] != b"ANDROID!":
        raise SystemExit("Input does not have Android boot image magic")

    kernel_size, ramdisk_size = struct.unpack_from("<II", boot, 8)
    header_size = struct.unpack_from("<I", boot, 20)[0]
    header_version = struct.unpack_from("<I", boot, 40)[0]
    if header_version != 4:
        raise SystemExit(f"Expected boot header v4, found v{header_version}")
    if ramdisk_size != 0:
        raise SystemExit("Expected a boot image with no ramdisk")
    if header_size != 1584:
        raise SystemExit(f"Unexpected v4 header size: {header_size}")

    page_size = 4096
    kernel_offset = page_size
    if kernel_offset + len(kernel) > len(boot):
        raise SystemExit("Kernel does not fit in the supplied image")

    # The original image has an AVB footer. Its vbmeta and footer become stale
    # when the kernel changes, so clear everything after the new kernel payload.
    boot[kernel_offset:] = b"\0" * (len(boot) - kernel_offset)
    boot[kernel_offset : kernel_offset + len(kernel)] = kernel
    struct.pack_into("<I", boot, 8, len(kernel))
    struct.pack_into("<I", boot, 1580, 0)  # v4 signature_size

    # Inject kernel command line
    if args.cmdline:
        inject_cmdline(boot, args.cmdline)
    elif args.debug_cmdline:
        inject_cmdline(boot, DEBUG_CMDLINE)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(boot)

    check = args.output.read_bytes()
    if check[:8] != b"ANDROID!":
        raise SystemExit("Repacked image failed magic check")
    if struct.unpack_from("<I", check, 8)[0] != len(kernel):
        raise SystemExit("Repacked image kernel_size check failed")
    if check[kernel_offset : kernel_offset + len(kernel)] != kernel:
        raise SystemExit("Repacked kernel payload does not match input Image")
    if check.rfind(b"AVBf") != -1:
        raise SystemExit("Stale AVB footer remains in output")
    print(f"Wrote unsigned boot image candidate: {args.output} ({len(check)} bytes)")
    print(f"Kernel payload: {len(kernel)} bytes; ramdisk: 0; AVB footer: cleared")

    # Verify cmdline injection
    injected = check[64:64+512].split(b'\0', 1)[0].decode('ascii', errors='replace')
    if injected:
        print(f"Injected cmdline: {injected}")


if __name__ == "__main__":
    main()
