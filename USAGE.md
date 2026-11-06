# Usage Guide: Peridot QCA6750 Monitor Mode & Packet Injection

This guide explains how to control, configure, and verify monitor mode and 802.11 raw packet injection on the **POCO F6 (`peridot`)** across various terminal environments:
- **Termux** (Native terminal environment with standard wireless tools)
- **Standard Root Shell / Terminal Emulators** (MT Manager, TermOne, NP Manager)
- **Android Debug Bridge** (ADB shell via USB or Wireless ADB)
- **Raw Kernel & Sysfs Commands** (manual, dependency-free scriptless operation)

---

## 1. Quick Command Reference

Once the Magisk / KernelSU / APatch module is installed, the helper command is available globally via **`pwm`** (*Peridot WLAN Mode*), **`wlan-mode`**, or **`peridot-wlan-mode`**:

| Action | Shortcut Command | Full Command | Expected Result |
| :--- | :--- | :--- | :--- |
| **Check Current Status** | `su -c pwm status` | `su -c peridot-wlan-mode status` | Prints driver, interface, and active mode status |
| **Enable Monitor & Injection** | `su -c pwm monitor` | `su -c peridot-wlan-mode monitor` | Activates monitor mode (`con_mode=4`) & injection helper |
| **Switch Back to Normal Wi-Fi** | `su -c pwm managed` | `su -c peridot-wlan-mode managed` | Restores standard Android Wi-Fi service (auto-resets channel) |
| **Set Operating Channel** | `su -c pwm channel <1-165>` | `su -c peridot-wlan-mode channel <ch>` | Locks radio & STA helper to specified channel |
| **Revert Channel to Auto** | `su -c pwm channel auto` | `su -c peridot-wlan-mode channel auto` | Resets channel hopping baseline |

---

## 2. Using from Termux

Termux is the recommended environment for running wireless auditing and network diagnostic tools directly on Android.

### Initial Setup in Termux
Ensure root access utilities are installed:
```sh
# Update package repositories
pkg update

# Install root helper (tsu) and wireless tools
pkg install tsu aircrack-ng tcpdump wireless-tools
```

### Switching to Monitor Mode
Open Termux and run:
```sh
# Elevate to root
tsu

# Verify injection driver status
pwm status

# Enable monitor mode
pwm monitor

# Lock interface to target channel (e.g., Channel 6)
pwm channel 6
```

### Capturing & Injecting in Termux
```sh
# Sniff traffic on target channel
airodump-ng wlan0 --channel 6

# Diagnostic injection test
aireplay-ng --test wlan0
```

### Restoring Wi-Fi
When finished, return the device to standard managed Android Wi-Fi:
```sh
pwm managed
```

> [!TIP]
> **Installed Termux after flashing the module?**
> The module automatically syncs shortcuts to `$PREFIX/bin` during module flashing and system boot. If you install Termux after flashing, simply running `su -c pwm` or `su -c peridot-wlan-mode` once from any root shell will automatically auto-link the commands into Termux!

---

## 3. Using from Non-Termux Terminals (MT Manager, TermOne, NP Manager)

In graphical Android terminal emulators:

1. Open the terminal app.
2. Elevate to root:
   ```sh
   su
   ```
3. Enter monitor and packet injection mode:
   ```sh
   pwm monitor
   ```
   *Expected output:*
   ```text
   [*] Switching to Monitor Mode...
   [+] Monitor mode enabled (con_mode=4).
   [+] Raw frame injection is active on wlan0.
   ```
4. Verify interface state:
   ```sh
   pwm status
   ```
5. When finished, restore standard Android Wi-Fi:
   ```sh
   pwm managed
   ```

---

## 4. Using from ADB Shell (PC / Mac USB or Wireless ADB)

Connect your device with USB Debugging enabled:

```bash
# 1. Open ADB shell
adb shell

# 2. Check WLAN injection driver status
su -c pwm status

# 3. Enable monitor mode
su -c pwm monitor

# 4. Lock to Channel 1 (2412 MHz)
su -c pwm channel 1

# 5. Check interface attributes
su -c iw dev wlan0 info

# 6. Revert back to managed mode when done
su -c pwm managed
```

---

## 5. Manual Operation (Raw Driver & Sysfs Commands)

If you are writing custom automation scripts or wish to control the driver manually without helper scripts:

### Step 1: Disable Android Wi-Fi Service
Android's framework Wi-Fi manager (`wificond` / `supplicant`) must be disabled to avoid channel contention:
```sh
su -c svc wifi disable
```

### Step 2: Switch Qualcomm Operating Mode (`con_mode`)
Qualcomm QCACLD-3.0 uses the `con_mode` module parameter:
- `con_mode=0`: Managed / Station mode (normal Android Wi-Fi)
- `con_mode=4`: Raw RF Promiscuous Monitor mode

```sh
# Bring interface down
su -c ip link set wlan0 down

# Switch driver parameter to Monitor mode
su -c "echo 4 > /sys/module/qca_cld3_qca6750/parameters/con_mode"

# Bring interface up
su -c ip link set wlan0 up
```

### Step 3: Set Monitor Channel
You can change channels using `iw`, `iwconfig`, or sysfs:

**Via `pwm channel`:**
```sh
su -c pwm channel 6
```

**Via Sysfs directly:**
```sh
# Sets Channel 6 (0 represents default 20MHz bandwidth)
su -c "echo '6 0' > /sys/class/net/wlan0/monitor_mode_channel"
```

**Via `iw`:**
```sh
su -c iw dev wlan0 set channel 6
```

**Via `iwconfig`:**
```sh
su -c iwconfig wlan0 channel 6
```

### Step 4: Restore Normal Wi-Fi
```sh
su -c ip link set wlan0 down
su -c "echo 0 > /sys/module/qca_cld3_qca6750/parameters/con_mode"
su -c ip link set wlan0 up
su -c svc wifi enable
```

---

## 6. Packet Injection & Card Diagnostics

To verify raw packet transmission over the air using standard diagnostic tools:

```sh
# 1. Enter monitor mode
su -c pwm monitor

# 2. Lock to the target AP channel (e.g. Channel 6)
su -c pwm channel 6

# 3. Run card injection diagnostics
su -c aireplay-ng --test wlan0
```

*Expected Diagnostic Output:*
```text
Trying broadcast probe requests...
Injection is working!
Found X APs

Trying directed probe requests...
<BSSID> - channel: 6 - '<SSID>'
Ping (min/avg/max): 3.606ms/15.936ms/93.665ms Power: -88.11
18/30:  60%
```

---

## 7. Sniffing and Packet Capture

### With `tcpdump`:
```sh
su -c tcpdump -i wlan0 -s 0 -w /sdcard/capture.pcap
```

### With `airodump-ng`:
```sh
su -c airodump-ng wlan0 --channel 6
```

---

## 8. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `pwm: command not found` | PATH variable missing root dir | Run `su -c /data/adb/modules/peridot-qca6750-injection-test/system/bin/peridot-wlan-mode status` to auto-heal symlinks. |
| `Waiting for beacon frame on channel -1` | Outdated driver without WEXT | Ensure module v1.0 is active; our driver exposes `SIOCGIWFREQ`. |
| `Device or resource busy` | Android Wi-Fi service running | Run `su -c svc wifi disable` or `su -c pwm monitor`. |
| `con_mode: Permission denied` | Running non-root | Always run commands as root via `su` or `tsu`. |
