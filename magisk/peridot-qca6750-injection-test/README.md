# Peridot QCA6750 Monitor Mode & Raw Packet Injection Module

Magisk, KernelSU, SuKiSU Ultra, and APatch module for the **POCO F6 (`peridot`)**, providing crash-free 802.11 monitor mode and raw packet injection on the Qualcomm FastConnect / QCA6750 WLAN chipset.

## Highlights
- **100% Stock OEM Kernel Aligned**: All 487 imported symbol CRCs are bit-exact aligned with the stock OEM symbol table under `CONFIG_MODVERSIONS=y`.
- **STA Helper Vdev Injection Engine**: Bypasses firmware monitor TX drop by encapsulating packets via an internal STA helper vdev with valid hardware scheduler queues.
- **Wireless Extensions (WEXT) Channel Support**: Exposes `SIOCGIWFREQ` and `SIOCGIWMODE`, fixing the "Channel -1" error in `airodump-ng` and `aireplay-ng`.
- **WMI Management Frame Injection**: Injects raw 802.11 management frames (probe requests, deauth, disassoc) directly to firmware via WMI mgmt tx.
- **Terminal CLI Tooling**: Instant access via `pwm`, `wlan-mode`, and `peridot-wlan-mode` across Termux, ADB shell, and root terminals.

## Terminal Usage (Termux / ADB / Root Shell)
```sh
# Check driver status
su -c pwm status

# Enter Monitor Mode
su -c pwm monitor

# Lock Wi-Fi Channel
su -c pwm channel 6

# Revert Channel to Auto / Default Hopping Baseline
su -c pwm channel auto

# Card Diagnostics
su -c aireplay-ng --test wlan0

# Restore Standard Android Wi-Fi
su -c pwm managed
```

Author: CoderArceus  
Repository: https://github.com/CoderArceus/Peridot-QCA6750-MonitorMode-PacketInjection
