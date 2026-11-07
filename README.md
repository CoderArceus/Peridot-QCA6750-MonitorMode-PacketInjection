# Izanami QCA6750 Monitor Mode & Packet Injection (v2.2-WebUI)

[![Target: POCO F6 (peridot)](https://img.shields.io/badge/Target-POCO%20F6%20%28peridot%29-blue?style=for-the-badge&logo=android)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Platform: SM8635 / QCA6750](https://img.shields.io/badge/SoC-Snapdragon%208s%20Gen%203-red?style=for-the-badge&logo=qualcomm)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Kernel: Linux 6.1 Universal GKI](https://img.shields.io/badge/Kernel-Linux%206.1%20%28Universal%20GKI%29-green?style=for-the-badge&logo=linux)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Author: CoderArceus & Sahayaraj](https://img.shields.io/badge/Author-CoderArceus%20%26%20Sahayaraj-orange?style=for-the-badge)](https://github.com/CoderArceus)
[![Root: KernelSU / APatch / Magisk](https://img.shields.io/badge/Root-KSU%20%7C%20APatch%20%7C%20Magisk-purple?style=for-the-badge)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Release: v2.2-WebUI](https://img.shields.io/badge/Release-v2.2--WebUI-brightgreen?style=for-the-badge)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection/releases/latest)

Native, crash-free 802.11 promiscuous monitor mode and raw management + data packet injection for the **POCO F6 / Redmi Turbo 3 (`peridot`)**, powered by Qualcomm Snapdragon 8s Gen 3 (SM8635) and FastConnect / QCA6750 running **Android 17 / Linux 6.1 (`android14-6.1`)**.

Featuring a built-in **KernelSU WebUI Matrix**, **Action Button** toggle, **Zygisk-Style Share & Export Log**, **One-Tap Channel Matrix**, and a **Native Standalone AArch64 ELF64 Auto-Vermagic + Symbol CRC Spoofer (Zero-Python)** that automatically adapts and loads the injection driver on boot across ANY custom or stock 6.1 GKI kernel build!

---

## 📑 Documentation Sitemap

Explore detailed technical documentation, CLI tutorials, and research records:

| Document | Description | Direct Link |
| :--- | :--- | :--- |
| **Usage Guide** | Complete CLI tutorial for WebUI, Termux, ADB shell, MT Manager, and manual sysfs operation | [📖 Read USAGE.md](USAGE.md) |
| **Architecture Deep-Dive** | Qualcomm QCACLD-3.0 internals, Loukious WMI injection engine, STA helper vdev, and CRC alignment | [🔬 Read ARCHITECTURE.md](ARCHITECTURE.md) |
| **Build & Research Log** | Chronological engineering logs, crash triage (`pcss_ssr_tm`), and symbol resolution | [🛠️ Read BUILD_LOG.md](BUILD_LOG.md) |
| **Port Diff Patch** | Unified diff patch applied against Xiaomi SM8635 WLAN drivers | [📄 View peridot-injection-port.diff](peridot-injection-port.diff) |
| **Porting Notes** | Summary of changes and symbols ported from Loukious WCN7750 tree | [📝 Read PORTING_NOTES.md](PORTING_NOTES.md) |

---

## ⚡ Feature Comparison Matrix

| Feature | Stock OEM Driver | Evil_Twin / Generic Monitor Ports | **This Project (`Izanami v2.1-WebUI`)** |
| :--- | :--- | :--- | :--- |
| **802.11 Monitor Mode** | ❌ Blocked (`con_mode=4` fails) | ⚠️ Promiscuous RX only | ✅ **Full Promiscuous Sniffing** |
| **Raw Packet Injection** | ❌ Inbound & outbound dropped | ❌ Fails / Dropped by datapath | ✅ **Native WMI STA Helper Injection** |
| **Management Frame Injection** | ❌ Blocked | ❌ Not supported | ✅ **Direct WMI Tx (Probe/Deauth/Disassoc/Auth/Assoc)** |
| **Data Frame Injection (EAPOL)** | ❌ Blocked | ❌ Not supported | ✅ **Full 802.11 Data / EAPOL / 802.1X Tx** |
| **KernelSU WebUI Dashboard** | ❌ None | ❌ None | ✅ **Neon Matrix Telemetry & Controls** |
| **KSU / APatch Action Button** | ❌ None | ❌ None | ✅ **One-Tap Mode Toggle in Manager** |
| **Auto-Vermagic on Boot** | ❌ Fails on mismatched kernel | ❌ Locked to specific kernel build | ✅ **Native Zero-Python Auto-Spoof on Boot** |
| **Universal Vermagic Spoofer** | ❌ Fails on mismatched kernel | ❌ Locked to specific kernel build | ✅ **Standalone AArch64 ELF64 Patcher (`patch_ko`)** |
| **Rapid Channel Hopping** | N/A | ❌ Firmware assert (`pcss_ssr_tm`) | ✅ **100% Stable (`wash`, `airodump`)** |
| **System Stability** | N/A | ❌ Firmware assert / PMIC watchdog panic | ✅ **100% Crash-Free (Tested under load)** |
| **Channel `-1` Bug** | ❌ No WEXT ioctls exposed | ❌ Tools fail with "Channel -1" | ✅ **Fixed (`SIOCGIWFREQ` & sysfs sync)** |
| **Channel Control** | ❌ Locked | ⚠️ Requires manual vendor commands | ✅ **POSIX `iw`, `iwconfig`, and `pwm channel`** |
| **Kernel Compatibility** | OEM stock only | ❌ Requires custom kernel / broken audio | ✅ **100% Stock OEM Symbol CRC Alignment** |
| **Terminal Integration** | None | ❌ Manual script hacking required | ✅ **Universal CLI (`pwm`, `wlan-mode`)** |

---

## 🚀 Quick Start

### 1. Download & Installation

Flashable ZIP packages are distributed exclusively through [**GitHub Releases**](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection/releases/latest) to keep the Git source tree clean:

1. Download [**`Izanami-QCA6750-Monitor-WebUI-v2.2.zip`**](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection/releases/latest).
2. Flash the module zip in **KernelSU**, **KernelSU-Next**, **SuKiSU Ultra (v0.4+)**, **APatch**, or **Magisk (v26+)**.
3. Reboot your device. Vermagic and symbol CRCs are automatically verified and adapted to your kernel on boot!

### 2. Global CLI Commands Reference

The module installs global shortcuts (**`pwm`**, **`wlan-mode`**, and **`peridot-wlan-mode`**) into root PATHs (`/data/adb/ksu/bin`, `/data/adb/magisk`, `/data/adb/ap/bin`) and Termux (`$PREFIX/bin`):

| Action | Shortcut Command | Full Command | Description |
| :--- | :--- | :--- | :--- |
| **Status Check** | `su -c pwm status` | `su -c peridot-wlan-mode status` | Displays driver, interface state, and active mode |
| **Enable Monitor Mode** | `su -c pwm monitor` | `su -c peridot-wlan-mode monitor` | Activates monitor mode (`con_mode=4`) & injection helper |
| **Set Channel** | `su -c pwm channel 6` | `su -c peridot-wlan-mode channel 6` | Locks monitor radio to Channel 6 (2437 MHz) |
| **Revert Channel to Auto** | `su -c pwm channel auto` | `su -c peridot-wlan-mode channel auto` | Resets channel hopping baseline |
| **Injection Diagnostics** | `su -c aireplay-ng --test wlan0` | `su -c aireplay-ng --test wlan0` | Verifies two-way injection against nearby APs |
| **Restore Normal Wi-Fi** | `su -c pwm managed` | `su -c peridot-wlan-mode managed` | Restores standard Android Wi-Fi (auto-reverts channel) |

---

## 🌐 Supported Terminal Environments

The module installs universal shims and path synchronization for all Android terminal contexts:

```
                  ┌─────────────────────────────────────────┐
                  │      POCO F6 Qualcomm QCA6750           │
                  │   Stock Kernel 6.1 (CONFIG_MODVERSIONS) │
                  └────────────────────┬────────────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      ┌──────────────────────┐                    ┌──────────────────────┐
      │  Termux (tsu / root) │                    │ ADB Shell / Root     │
      │  - airodump-ng       │                    │ - MT Manager Term    │
      │  - aireplay-ng       │                    │ - TermOne / NP Term  │
      │  - tcpdump / tshark  │                    │ - Root scripts / CI  │
      └──────────┬───────────┘                    └──────────┬───────────┘
                 │                                           │
                 └─────────────────────┬─────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────┐
        │  Universal iw / iwconfig Wrappers                   │
        │  - Intercepts "set channel" / "channel"             │
        │  - Writes directly to Qualcomm Sysfs                │
        │  - Synthesizes interface type for audit tools       │
        └──────────────────────────────┬──────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────┐
        │  /sys/class/net/wlan0/monitor_mode_channel          │
        │  - Instantaneous hardware retuning                  │
        │  - Dynamic STA Helper Vdev realignment              │
        └─────────────────────────────────────────────────────┘
```

| Environment | Setup & Execution | Channel Switching |
| :--- | :--- | :--- |
| **Termux** | Run `tsu`, then `pwm status`, `pwm monitor`, `pwm channel 6` | ✅ Full native support via `$PREFIX/bin/` |
| **ADB Shell** | Run `adb shell`, then `su -c pwm monitor` | ✅ Full support via root PATH |
| **Non-Termux Terminals** | Open MT Manager / TermOne, run `su`, then `pwm` | ✅ Full support via `/data/adb/*/bin` |

---

## 🛠️ Technical Architecture

### 1. The Loukious WMI Management Frame Injection Architecture
On Linux 6.1 Android kernels (`android14-6.1`), Qualcomm FastConnect drivers drop outbound raw 802.11 frames passed to monitor interfaces because monitor vdevs lack hardware scheduler queues, rate-control tables, and transmit descriptors.

Based on groundbreaking architecture pioneered by **@Loukious** (`vendor_qcom_opensource_wlan`):
- Rather than pushing raw skb packets through broken monitor datapath rings (which panics firmware DMA with `pcss_ssr_tm`), the driver dynamically creates an internal Station helper vdev (`vdev_id 2`) on the same physical frequency.
- Raw 802.11 management frames (probe requests, deauth, disassoc) are extracted from the raw socket and sent directly to the firmware coprocessor via `wmi_mgmt_unified_cmd_send()`.
- The firmware scheduler treats them as authenticated management frames, returning completion status `0` (`WMI_MGMT_TX_COMP_TYPE_COMPLETE_OK`).

### 2. Universal Wireless Extensions (WEXT) Channel Support
Audit tools (`airodump-ng`, `aireplay-ng`) query interface channels via `ioctl(SIOCGIWFREQ)` and `ioctl(SIOCGIWMODE)`. Stock Qualcomm drivers do not expose WEXT handlers for monitor mode, returning `-1` or failing outright.

This project implements dedicated WEXT ioctl dispatchers inside `wlan_hdd_wext.c`:
- **`SIOCGIWMODE`**: Accurately reports `IW_MODE_MONITOR`.
- **`SIOCGIWFREQ`**: Dynamically translates the active hardware frequency from `pdev->cur_chan` into m/e frequency pairs.
- Eliminates the infamous `"Waiting for beacon frame ... on channel -1"` error across all auditing suites.

### 3. Bit-Exact Stock Kernel CRC Alignment
Under `CONFIG_MODVERSIONS=y`, Linux checks the 64-bit CRC of every imported symbol against the running kernel.

Using a custom ELF analysis engine (`align_modversions.py`), 487 imported kernel symbols were aligned against Xiaomi's stock OEM kernel symbol table, achieving a **100.0% CRC match rate**. The module loads directly onto production devices without triggering vermagic or CRC verification rejections.

---

## 📱 Hardware & Compatibility Specifications

| Specification | Target Details |
| :--- | :--- |
| **Device Model** | POCO F6 / Redmi Turbo 3 (`peridot`) |
| **SoC** | Qualcomm Snapdragon 8s Gen 3 (SM8635) |
| **WLAN Hardware** | Qualcomm FastConnect / QCA6750 |
| **Android Version** | Android 14 / Android 15 / Android 17 (tested on RisingOS 9) |
| **Kernel Version** | Linux `6.1.176-g7fee93174ed9` (GKI `android14-6.1`) |
| **Root Solutions** | KernelSU, SuKiSU Ultra (v0.4+), APatch, Magisk (v26+) |
| **SELinux** | Enforcing & Permissive compatible |
| **Modversions** | `CONFIG_MODVERSIONS=y` (100% matched) |

---

## ⚖️ Legal & Ethical Use Notice

This software is developed strictly for **educational research, wireless protocol verification, and authorized network diagnostics**. It is designed to evaluate Wi-Fi driver architectures and verify hardware packet transmission.

Do not use this software on networks or devices without explicit written permission from the network owner. The authors and contributors assume no liability for misuse.

---

## 👥 Credits & Acknowledgments

- **[CoderArceus](https://github.com/CoderArceus)**: Project author, Peridot QCA6750 port, crash elimination, WMI helper implementation, WEXT registration, POSIX wrappers, and stock CRC alignment.
- **[Loukious](https://github.com/Loukious)**: Original design and architecture for Qualcomm WMI management frame injection and STA helper vdev.
- **Qualcomm & Xiaomi**: Original Linux kernel and QCACLD-3.0 codebase.
