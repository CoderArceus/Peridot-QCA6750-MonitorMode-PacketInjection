# Peridot QCA6750 Monitor Mode & Raw Packet Injection

[![Target: POCO F6 (peridot)](https://img.shields.io/badge/Target-POCO%20F6%20%28peridot%29-blue?style=for-the-badge&logo=android)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Platform: SM8635 / QCA6750](https://img.shields.io/badge/SoC-Snapdragon%208s%20Gen%203-red?style=for-the-badge&logo=qualcomm)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Kernel: Linux 6.1 Stock GKI](https://img.shields.io/badge/Kernel-Linux%206.1%20%28Stock%20GKI%29-green?style=for-the-badge&logo=linux)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)
[![Author: CoderArceus](https://img.shields.io/badge/Author-CoderArceus-orange?style=for-the-badge)](https://github.com/CoderArceus)
[![Root: KernelSU / APatch / Magisk](https://img.shields.io/badge/Root-KSU%20%7C%20APatch%20%7C%20Magisk-purple?style=for-the-badge)](https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection)

Native, crash-free 802.11 monitor mode and raw packet injection for the **POCO F6 (`peridot`)**, powered by Qualcomm Snapdragon 8s Gen 3 (SM8635) and FastConnect / QCA6750 running **Android 17 / Linux 6.1 (`android14-6.1`)**.

Works directly on the **untouched OEM stock kernel** without custom kernel reflashing, preserving Xiaomi proprietary hardware peripherals (including `aw882xx` / `WL2866D` SmartPA audio amplifiers).

---

## 📑 Documentation Sitemap

Explore detailed documentation and technical deep-dives across the project:

| Document | Description | Direct Link |
| :--- | :--- | :--- |
| **Usage Guide** | Complete CLI guide for non-Termux terminals, ADB shell, manual sysfs commands, and wireless tools | [📖 Read USAGE.md](USAGE.md) |
| **Architecture Deep-Dive** | Qualcomm QCACLD-3.0 internals, STA helper vdev design, WEXT registration, and CRC alignment | [🔬 Read ARCHITECTURE.md](ARCHITECTURE.md) |
| **Build & Research Log** | Step-by-step engineering timeline, crash diagnoses, and symbol resolution logs | [🛠️ Read BUILD_LOG.md](BUILD_LOG.md) |
| **Port Diff Patch** | Complete unified patch against stock Xiaomi SM8635 WLAN drivers | [📄 View peridot-injection-port.diff](peridot-injection-port.diff) |

---

## ⚡ Feature Comparison Matrix

| Feature | Stock OEM Driver | Traditional Injection Ports | **This Project (`Peridot-QCA6750`)** |
| :--- | :--- | :--- | :--- |
| **802.11 Monitor Mode** | ❌ Blocked (`con_mode=4` fails) | ⚠️ Partial (crashes or hangs) | ✅ **Full Promiscuous Sniffing** |
| **Raw Packet Injection** | ❌ TX dropped by firmware | ❌ TCL exception crash / kernel panic | ✅ **Native WMI STA Helper Injection** |
| **Stability / Crashes** | N/A | ❌ Kernel panic on packet burst | ✅ **100% Crash-Free (Tested under load)** |
| **Channel `-1` Bug** | ❌ No WEXT ioctls exposed | ❌ Tools fail with "Channel -1" | ✅ **Fixed (`SIOCGIWFREQ` & sysfs sync)** |
| **Stryker Auto-Channel** | ❌ Unsupported | ❌ Channel locked / manual only | ✅ **Seamless Universal Wrappers** |
| **Kernel Compatibility** | OEM stock only | ❌ Requires custom permissive kernel | ✅ **100% Stock Kernel CRC Alignment** |
| **Xiaomi Hardware** | Audio & sensors functional | ❌ Breaks SmartPA amplifiers | ✅ **Completely Untouched OEM Peripherals** |

---

## 🚀 Quick Start

### 1. Installation

1. Download the latest release: [**`Peridot-QCA6750-Injection-Test-v0.8.zip`**](Peridot-QCA6750-Injection-Test-v0.8.zip).
2. Flash the module zip in **KernelSU**, **SuKiSU Ultra**, **APatch**, or **Magisk**.
3. Reboot your device.

### 2. Global CLI Commands Reference

Shortcuts are automatically mapped to **`pwm`** (*Peridot WLAN Mode*) and **`wlan-mode`** across all shells:

| Action | Shortcut Command | Full Command | Expected Result |
| :--- | :--- | :--- | :--- |
| **Status Check** | `su -c pwm status` | `su -c wlan-mode status` | Prints driver, interface, and active mode status |
| **Enable Monitor Mode** | `su -c pwm monitor` | `su -c wlan-mode monitor` | Activates monitor mode & injection helper |
| **Set Channel** | `su -c pwm channel 6` | `su -c wlan-mode channel 6` | Locks monitor radio to Channel 6 (2437 MHz) |
| **Revert to Auto** | `su -c pwm channel auto` | `su -c wlan-mode channel auto` | Resets channel hopping baseline |
| **Diagnostic Test** | `su -c aireplay-ng --test wlan0` | `su -c aireplay-ng --test wlan0` | Verifies two-way injection against nearby APs |
| **Restore Normal Wi-Fi** | `su -c pwm managed` | `su -c wlan-mode managed` | Restores standard Android Wi-Fi service |

---

## 🌐 Supported Environments

The module installs universal shims and path synchronization for all Android execution contexts:

```
                  ┌─────────────────────────────────────────┐
                  │      POCO F6 Qualcomm QCA6750           │
                  │   Stock Kernel 6.1 (CONFIG_MODVERSIONS) │
                  └────────────────────┬────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     ┌──────────────────────┐                      ┌──────────────────────┐
     │  Android Host / Root │                      │   Stryker Chroot     │
     │  - Termux (tsu)      │                      │  - airmon-ng         │
     │  - ADB Shell         │                      │  - airodump-ng       │
     │  - MT Manager Term   │                      │  - aireplay-ng       │
     │  - TermOne           │                      │  - Handshake Capture │
     └──────────┬───────────┘                      └──────────┬───────────┘
                │                                             │
                └──────────────┬──────────────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │  Universal iw / iwconfig Wrappers           │
        │  - Intercepts set channel / channel         │
        │  - Writes directly to Qualcomm Sysfs        │
        │  - Forwards info queries to real binaries   │
        └──────────────────────┬──────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │  /sys/class/net/wlan0/monitor_mode_channel  │
        │  - Instantaneous hardware retuning          │
        │  - Dynamic STA Helper Vdev realignment      │
        └─────────────────────────────────────────────┘
```

| Environment | How to Execute | Auto-Channel Switching |
| :--- | :--- | :--- |
| **Termux** | Run `tsu`, then `pwm status`, `pwm monitor`, `pwm channel 6` | ✅ Full native support via `$PREFIX/bin/` |
| **ADB Shell** | Run `adb shell`, then `su -c pwm monitor` | ✅ Full support via `/system/bin/` |
| **Non-Termux Terminals** | Open MT Manager / TermOne / NP Manager, run `su`, then `pwm` | ✅ Full support via root PATH |
| **Stryker Suite** | Launch Stryker app, select Monitor Mode & Handshake Capture | ✅ Automated via chroot wrapper shims |

---

## 🛠️ Technical Overview

### 1. The STA Companion Vdev Injection Engine
In Qualcomm's FastConnect architecture (`qcacld-3.0`), frames sent to a monitor vdev are discarded by hardware because monitor vdevs lack scheduler transmit queues and rate-control tables. 

Instead of routing raw frames through the broken monitor vdev or relying on unstable TCL exception rings, this driver dynamically creates an internal STA helper vdev (`vdev_id 2`) on the same physical frequency. Frames passed through `wlan0` are encapsulated in WMI management commands (`WMI_MGMT_UNIFIED_CMD_SEND`) and pushed directly into the hardware scheduler, achieving reliable transmission without kernel exceptions.

### 2. Universal Wireless Extensions (WEXT) Channel Support
Legacy audit tools (`airodump-ng`, `aireplay-ng`, `kismet`) query interface channels via `ioctl(SIOCGIWFREQ)` and `ioctl(SIOCGIWMODE)`. Stock Qualcomm drivers do not expose WEXT handlers for monitor mode, returning `-1` or failure.

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

- **[CoderArceus](https://github.com/CoderArceus)**: Project author, Peridot QCA6750 architecture port, crash elimination, WMI helper design, WEXT registration, Stryker auto-channel shims, and stock CRC alignment.
- **Loukious**: Groundbreaking reference research on the WCN7750 STA helper concept.
- **Qualcomm & Xiaomi**: Original Linux kernel and QCACLD-3.0 codebase.
