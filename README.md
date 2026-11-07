# Izanami QCA6750 Monitor Mode and Packet Injection (v2.2-WebUI)

[![Target: POCO F6 (peridot)](https://img.shields.io/badge/Target-POCO%20F6%20%28peridot%29-blue?style=for-the-badge&logo=android)](https://github.com/CoderArceus/izanami-peridot)
[![Platform: SM8635 / QCA6750](https://img.shields.io/badge/SoC-Snapdragon%208s%20Gen%203-red?style=for-the-badge&logo=qualcomm)](https://github.com/CoderArceus/izanami-peridot)
[![Kernel: Linux 6.1 Universal GKI](https://img.shields.io/badge/Kernel-Linux%206.1%20%28Universal%20GKI%29-green?style=for-the-badge&logo=linux)](https://github.com/CoderArceus/izanami-peridot)
[![Author: CoderArceus & Sahayaraj](https://img.shields.io/badge/Author-CoderArceus%20%26%20Sahayaraj-orange?style=for-the-badge)](https://github.com/CoderArceus)
[![Root: KernelSU / APatch / Magisk](https://img.shields.io/badge/Root-KSU%20%7C%20APatch%20%7C%20Magisk-purple?style=for-the-badge)](https://github.com/CoderArceus/izanami-peridot)
[![Release: v2.2-WebUI](https://img.shields.io/badge/Release-v2.2--WebUI-brightgreen?style=for-the-badge)](https://github.com/CoderArceus/izanami-peridot/releases/latest)

802.11 promiscuous monitor mode and raw management and data packet injection driver for the POCO F6 / Redmi Turbo 3 (`peridot`), equipped with the Qualcomm Snapdragon 8s Gen 3 (SM8635) and FastConnect / QCA6750 running Linux 6.1 (`android14-6.1`).

Includes a KernelSU WebUI dashboard, Action button integration, diagnostic export with Android share sheet support, channel controls, and an AArch64 standalone ELF64 vermagic and symbol CRC spoofer for loading across GKI kernel variants.

---

## Documentation Sitemap

| Document | Description | Direct Link |
| :--- | :--- | :--- |
| **Usage Guide** | Complete CLI tutorial for WebUI, Termux, ADB shell, MT Manager, and manual sysfs operation | [Read USAGE.md](USAGE.md) |
| **Architecture Deep-Dive** | Qualcomm QCACLD-3.0 internals, Loukious WMI injection engine, STA helper vdev, and CRC alignment | [Read ARCHITECTURE.md](ARCHITECTURE.md) |
| **Build & Research Log** | Chronological engineering logs, crash triage (`pcss_ssr_tm`), and symbol resolution | [Read BUILD_LOG.md](BUILD_LOG.md) |
| **Port Diff Patch** | Unified diff patch applied against Xiaomi SM8635 WLAN drivers | [View peridot-injection-port.diff](peridot-injection-port.diff) |
| **Porting Notes** | Summary of changes and symbols ported from Loukious WCN7750 tree | [Read PORTING_NOTES.md](PORTING_NOTES.md) |

---

## Technical Overview and Differences from Stock

Stock Qualcomm Android drivers reject monitor mode configurations (`con_mode=4`) and lack transmit descriptors for raw frame injection on monitor interfaces. Standard community ports for Qualcomm chips often stop at promiscuous frame reception (RX only) or attempt to route injected frames through broken monitor datapath rings, causing firmware DMA corruption and subsystem restarts (`pcss_ssr_tm`).

This project implements the following architectural changes:

1. **WMI Packet Transmission via Station Helper**: Ported from Loukious's reference architecture on the WCN7750, raw 802.11 management frames (Probe, Auth, Assoc, Deauth) and data frames (EAPOL / 802.1X) bypass broken monitor ring buffers and are passed directly to firmware through Qualcomm's unified WMI management command path (`wmi_mgmt_unified_cmd_send`). An internal Station helper virtual device (`vdev_id 2`) tracks the active physical frequency to satisfy firmware scheduler requirements.
2. **Wireless Extensions (WEXT) Ioctl Dispatch**: Dedicated handlers for `SIOCGIWMODE` and `SIOCGIWFREQ` report `IW_MODE_MONITOR` and translate hardware channel frequency into standard m/e frequency pairs, resolving the "Channel -1" error in tools like `airodump-ng` and `aireplay-ng`.
3. **Symbol CRC Alignment & Standalone Spoofer**: Imported kernel symbols are aligned to the stock OEM kernel symbol table under `CONFIG_MODVERSIONS=y`. Additionally, a standalone statically linked AArch64 binary (`patch_ko`) updates `.modinfo` vermagic and synchronizes `__versions` CRCs dynamically on boot, allowing the prebuilt driver to load on custom kernels (such as Vibranium) without requiring on-device compilers or Python.
4. **Environment Compatibility**: Integrates command wrappers (`pwm`, `wlan-mode`, `peridot-wlan-mode`) and POSIX `iw`/`iwconfig` shims into root PATHs and Termux, alongside a KernelSU/APatch WebUI dashboard for telemetry, mode switching, channel locking, and log export.

### Verified Testing and Known Limitations

* **Tested Platforms**: POCO F6 (`peridot`) running stock Xiaomi HyperOS (kernel `6.1.176-g7fee93174ed9`), custom Vibranium kernel (`6.1.176-Vibranium-V18+`), and RisingOS (Android 17 / SDK 37).
* **Auditing Tools Verified**: Promiscuous packet capture and channel hopping tested with `wash -i wlan0` and `airodump-ng wlan0`. Packet injection verified with `aireplay-ng` (deauthentication and fake authentication) and `reaver` (full 4-way EAPOL/WPS transaction completing M1-M4 exchanges).
* **Limitations**: Enabling monitor mode unloads the standard Android managed station interface; normal internet Wi-Fi connectivity is unavailable while monitor mode is active. Reverting via `pwm managed` or the WebUI restores standard STA Wi-Fi and resets the channel to automatic hopping. Frame injection is restricted to frame types permitted by the firmware WMI layer (management frames and 802.11 data frames including EAPOL).

---

## Quick Start

### 1. Download & Installation

Flashable ZIP packages are distributed through [GitHub Releases](https://github.com/CoderArceus/izanami-peridot/releases/latest):

1. Download `Izanami-QCA6750-Monitor-WebUI-v2.2.zip`.
2. Flash the module ZIP in KernelSU, KernelSU-Next, SuKiSU Ultra (v0.4+), APatch, or Magisk (v26+).
3. Reboot the device. Vermagic and symbol CRCs are verified and adapted to the active kernel release during boot.

### 2. Command Reference

The module installs shortcuts (`pwm`, `wlan-mode`, and `peridot-wlan-mode`) into root PATHs (`/data/adb/ksu/bin`, `/data/adb/magisk`, `/data/adb/ap/bin`) and Termux (`$PREFIX/bin`):

| Action | Shortcut Command | Full Command | Description |
| :--- | :--- | :--- | :--- |
| **Status Check** | `su -c pwm status` | `su -c peridot-wlan-mode status` | Displays driver, interface state, and active mode |
| **Enable Monitor Mode** | `su -c pwm monitor` | `su -c peridot-wlan-mode monitor` | Activates monitor mode (`con_mode=4`) and injection helper |
| **Set Channel** | `su -c pwm channel 6` | `su -c peridot-wlan-mode channel 6` | Locks monitor radio to Channel 6 (2437 MHz) |
| **Revert Channel to Auto** | `su -c pwm channel auto` | `su -c peridot-wlan-mode channel auto` | Resets channel hopping baseline |
| **Export Diagnostics** | `su -c pwm log` | `su -c peridot-wlan-mode log` | Dumps telemetry and dmesg to `/sdcard/peridot_debug.log` |
| **Injection Diagnostics** | `su -c aireplay-ng --test wlan0` | `su -c aireplay-ng --test wlan0` | Verifies two-way injection against nearby APs |
| **Restore Normal Wi-Fi** | `su -c pwm managed` | `su -c peridot-wlan-mode managed` | Restores standard Android Wi-Fi (auto-reverts channel) |

---

## Supported Terminal Environments

The module installs universal shims and path synchronization for standard Android environments:
* **Termux**: Run `tsu` (or `su`), followed by `pwm status`, `pwm monitor`, `pwm channel <ch>`.
* **ADB Shell**: Run `adb shell`, then `su -c pwm monitor`.
* **Terminal Emulators**: Run `su`, then `pwm` in MT Manager, TermOne, or NP Manager.

Calls to `iw` or `iwconfig` are intercepted by wrapper shims in the module's `system/bin` path and directed to the Qualcomm sysfs control interface (`/sys/class/net/wlan0/monitor_mode_channel`), keeping compatibility with auditing scripts that rely on standard Linux tools.

---

## Technical Architecture

### 1. WMI Management and Data Frame Injection
On Linux 6.1 Android kernels (`android14-6.1`), Qualcomm FastConnect drivers drop outbound raw 802.11 frames passed to monitor interfaces because monitor virtual devices lack hardware scheduler queues, rate-control tables, and transmit descriptors.

Based on reference architecture by Loukious (`vendor_qcom_opensource_wlan`):
* Rather than routing raw socket buffers through the monitor datapath ring, the driver dynamically provisions an internal Station helper virtual device (`vdev_id 2`) on the same physical frequency.
* Raw 802.11 management frames (Probe requests, Auth, Assoc, Deauth) and data frames (EAPOL / 802.1X / WPS) are extracted from the raw socket in `wlan_hdd_tx_rx.c` and transmitted directly to firmware via `wmi_mgmt_unified_cmd_send()`.
* The firmware scheduler processes the frame with valid transmit parameters and returns completion status `0` (`WMI_MGMT_TX_COMP_TYPE_COMPLETE_OK`).

### 2. Wireless Extensions (WEXT) Channel Support
Auditing tools query interface channels via `ioctl(SIOCGIWFREQ)` and `ioctl(SIOCGIWMODE)`. Stock Qualcomm drivers omit WEXT handlers for monitor mode, returning `-1` or failing.

Dedicated WEXT dispatchers implemented in `wlan_hdd_wext.c`:
* **`SIOCGIWMODE`**: Accurately reports `IW_MODE_MONITOR`.
* **`SIOCGIWFREQ`**: Translates the active hardware frequency from `pdev->cur_chan` into m/e frequency pairs.
* Resolves the "Waiting for beacon frame ... on channel -1" error in `airodump-ng` and `aireplay-ng`.

### 3. Kernel Symbol Alignment and Dynamic Adaptation
Under `CONFIG_MODVERSIONS=y`, Linux validates the 64-bit CRC of every imported symbol against the active kernel.

Imported symbols in `qca_cld3_qca6750.ko` are matched against Xiaomi's stock OEM kernel symbol table. To support third-party kernel releases, the module includes `patch_ko`, a standalone AArch64 C binary that inspects `.modinfo` and `__versions`, adapts vermagic to match `uname -r`, syncs imported symbol CRCs from stock modules, and recalculates section offsets while maintaining 8-byte alignment. This executes on boot via `post-fs-data.sh` and `service.sh`.

---

## Hardware and Compatibility Specifications

| Specification | Target Details |
| :--- | :--- |
| **Device Model** | POCO F6 / Redmi Turbo 3 (`peridot`) |
| **SoC** | Qualcomm Snapdragon 8s Gen 3 (SM8635) |
| **WLAN Hardware** | Qualcomm FastConnect / QCA6750 |
| **Android Version** | Android 14 / Android 15 / Android 17 (tested on RisingOS 9 and HyperOS) |
| **Kernel Version** | Linux `6.1.176-g7fee93174ed9` (GKI `android14-6.1`), custom 6.1 GKI builds |
| **Root Solutions** | KernelSU, KernelSU-Next, SuKiSU Ultra (v0.4+), APatch, Magisk (v26+) |
| **SELinux** | Enforcing and Permissive compatible |
| **Modversions** | `CONFIG_MODVERSIONS=y` (matched and dynamically spoofed) |

---

## Legal Notice

This software is developed for educational research, wireless protocol verification, and authorized network diagnostics. Do not use this software on networks or devices without explicit written permission from the network owner. The authors and contributors assume no liability for misuse.

---

## Credits and Acknowledgments

* **CoderArceus**: Project author, Peridot QCA6750 port, crash triage, WMI helper implementation, WEXT registration, POSIX wrappers, and symbol alignment.
* **Sahayaraj (Raju-yeager)**: WebUI Matrix design, ELF spoofer design, and testing.
* **Loukious**: Reference research and architecture for Qualcomm WMI frame injection and STA helper virtual device.
* **Qualcomm & Xiaomi**: Linux kernel and QCACLD-3.0 base driver sources.
