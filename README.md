# Peridot QCA6750 Monitor Mode & Raw Packet Injection

Native, crash-free 802.11 monitor mode and raw packet injection for the **POCO F6 (`peridot`)**, powered by Qualcomm Snapdragon 8s Gen 3 (SM8635) and FastConnect / QCA6750 running **Android 17 / Linux 6.1 (`android14-6.1`)**.

Works directly on the **untouched OEM stock kernel** without breaking Xiaomi proprietary hardware (such as `aw882xx` / `WL2866D` SmartPA audio amplifiers).

---

## Highlights

- **Crash-Free Operation**: Replaces unstable TCL exception hacks with Qualcomm native WMI command transmission (`wmi_mgmt_unified_cmd_send`). Zero kernel panics, zero reboots.
- **Companion STA Helper Vdev**: Bypasses Qualcomm firmware's monitor-mode TX discard by dynamically spawning an internal STA helper vdev with valid scheduler queues.
- **Channel `-1` Fixed**: Built-in monitor Wireless Extensions (`SIOCGIWFREQ`, `SIOCGIWMODE`, `SIOCSIWFREQ`) allowing legacy tools (`airodump-ng`, `aireplay-ng`, Stryker) to query and switch channels seamlessly.
- **100% Stock Kernel CRC Alignment**: Aligns all 487 imported symbol CRCs against stock OEM symbols, allowing execution under `CONFIG_MODVERSIONS=y`.
- **Global Tooling**: Exposes short, convenient commands (`pwm` and `wlan-mode`) across all environments (Termux, ADB shell, MT Manager, TermOne).

---

## Quick Start

### 1. Installation

1. Download **`Peridot-QCA6750-Injection-Test-v0.7.zip`**.
2. Flash the zip in **Magisk**, **KernelSU**, **SuKiSU Ultra**, or **APatch**.
3. Reboot your device.

### 2. Basic Commands

Open any terminal emulator (or ADB shell) and run:

```bash
# Check current driver and interface status
su -c pwm status

# Enable Monitor Mode and Packet Injection
su -c pwm monitor

# Set Wi-Fi channel (e.g. Channel 6)
su -c pwm channel 6

# Verify injection over the air
su -c aireplay-ng --test wlan0

# Return to standard Android Wi-Fi
su -c pwm managed
```

---

## Documentation

- **[USAGE.md](USAGE.md)**: Complete guide for non-Termux terminals, ADB shell, manual sysfs commands, and wireless tools.
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Deep dive into the Qualcomm QCACLD-3.0 driver internals, STA helper vdev design, WEXT registration, and CRC alignment.
- **[BUILD_LOG.md](BUILD_LOG.md)**: Detailed step-by-step build, testing, and debugging timeline.
- **[peridot-injection-port.diff](peridot-injection-port.diff)**: Complete unified git diff against stock Xiaomi SM8635 WLAN drivers.

---

## Credits & Acknowledgments

- **subaru**: Peridot QCA6750 architecture port, crash fixes, WMI helper design, WEXT registration, and stock CRC alignment.
- **Loukious**: Groundbreaking reference research on WCN7750 STA helper concept.
- **Qualcomm & Xiaomi**: Original Linux kernel and QCACLD-3.0 codebase.
