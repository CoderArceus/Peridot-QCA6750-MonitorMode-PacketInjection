# Usage Guide: Peridot QCA6750 Monitor Mode & Packet Injection

This guide explains how to control and verify monitor mode and 802.11 raw packet injection on the **POCO F6 (`peridot`)** across different terminal environments:
- Standard Root Shell / Terminal Emulators (TermOne, MT Manager Terminal, NP Manager)
- Android Debug Bridge (ADB shell)
- Termux
- Raw Kernel & Sysfs Commands (manual script-free operation)

---

## 1. Quick Command Reference

Once the Magisk / KernelSU / APatch module is installed, the helper command is available globally via either **`pwm`** (Peridot WLAN Mode) or **`wlan-mode`**.

| Action | Shortcut Command | Full Command |
| :--- | :--- | :--- |
| **Check Current Status** | `su -c pwm status` | `su -c wlan-mode status` |
| **Enable Monitor & Injection** | `su -c pwm monitor` | `su -c wlan-mode monitor` |
| **Switch Back to Normal Wi-Fi** | `su -c pwm managed` | `su -c wlan-mode managed` |
| **Set Operating Channel** | `su -c pwm channel <1-165>` | `su -c wlan-mode channel <1-165>` |
| **Revert Channel to Auto** | `su -c pwm channel auto` | `su -c wlan-mode channel auto` |

---

## 2. Using from Non-Termux Terminals (MT Manager, TermOne, NP Manager)

In graphical Android terminal emulators:

1. Open the terminal app.
2. Acquire root privileges:
   ```sh
   su
   ```
3. Enter monitor and packet injection mode:
   ```sh
   pwm monitor
   ```
   *Expected output:*
   ```text
   [*] Injection driver active: fast switching to Monitor Mode...
   [+] Monitor mode enabled (con_mode=4).
   ```
4. Check interface state:
   ```sh
   pwm status
   ```
5. When finished, restore normal Android Wi-Fi:
   ```sh
   pwm managed
   ```

> [!NOTE]
> If your terminal app runs non-root by default, always prepend `su -c`, for example:
> `su -c pwm status`

---

## 3. Using from ADB Shell (PC / Mac USB Connection)

Connect your phone via USB with USB Debugging enabled:

```bash
# Enter ADB shell
adb shell

# Check WLAN injection status
su -c pwm status

# Turn on monitor mode
su -c pwm monitor

# Change channel to Channel 6 (2437 MHz)
su -c pwm channel 6

# Verify with iw
su -c iw dev wlan0 info

# Return to managed mode
su -c pwm managed
```

---

## 4. Manual Operation (Raw Driver & Sysfs Commands)

If you are developing custom tools or wish to control the driver manually without helper scripts:

### Step 1: Disable Android Wi-Fi Service
Android's framework Wi-Fi manager (`wificond` / `supplicant`) will interfere with monitor mode if left active:
```sh
su -c svc wifi disable
```

### Step 2: Switch Qualcomm Operating Mode (`con_mode`)
Qualcomm QCACLD-3.0 uses `con_mode` module parameters:
- `con_mode=0`: Managed / Station mode (normal Wi-Fi)
- `con_mode=4`: Raw RF Promiscuous Monitor mode

```sh
# Bring interface down
su -c ip link set wlan0 down

# Switch to Monitor mode
su -c "echo 4 > /sys/module/qca_cld3_qca6750/parameters/con_mode"

# Bring interface up
su -c ip link set wlan0 up
```

### Step 3: Set Monitor Channel
You can change channels using `iw`, `iwconfig`, or sysfs:

**Via `iw`:**
```sh
su -c iw dev wlan0 set channel 6
```

**Via `iwconfig` (Wireless Extensions):**
```sh
su -c iwconfig wlan0 channel 6
```

**Via Sysfs:**
```sh
# Sets channel 6 (0 represents default 20MHz bandwidth)
su -c "echo '6 0' > /sys/class/net/wlan0/monitor_mode_channel"
```

### Step 4: Restore Normal Wi-Fi
```sh
su -c ip link set wlan0 down
su -c "echo 0 > /sys/module/qca_cld3_qca6750/parameters/con_mode"
su -c ip link set wlan0 up
su -c svc wifi enable
```

---

## 5. Packet Injection & Card Diagnostics

To verify raw packet transmission over the air using `aireplay-ng`:

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

## 6. Sniffing and Packet Capture

### With `tcpdump`:
```sh
su -c tcpdump -i wlan0 -s 0 -w /sdcard/capture.pcap
```

### With `airodump-ng`:
```sh
su -c airodump-ng wlan0 --channel 6
```

---

## 7. Stryker Integration & Automated Channel Switching

Stryker runs inside a dedicated chroot environment at `/data/local/stryker/release/`. 

### Automated Hooks
The Magisk module automatically detects and hooks Stryker's chroot environment during module flashing, system boot, and whenever `pwm` is run:
1. **`iw` & `iwconfig` Wrappers**: Intercepts `iw dev wlan0 set channel <ch>` and `iwconfig wlan0 channel <ch>` calls from Stryker and routes them directly to `/sys/class/net/wlan0/monitor_mode_channel`.
2. **Dynamic PATH Export**: Patches `/usr/sbin/airmon-ng` to properly locate system binaries (`mountpoint`, `iw`, `iwconfig`, `ethtool`).
3. **Multi-Environment Symlinks**: Exposes `iw`, `iwconfig`, `airodump-ng`, and `aireplay-ng` across both `/usr/bin/` and `/usr/sbin/`.

### Using with Stryker
1. Launch Stryker and start Monitor Mode.
2. Handshake capture and automated tools will automatically tune Qualcomm monitor channel to the target BSSID without requiring manual terminal switching.
3. If you ever need to manually set or reset channels:
   - Lock channel: `su -c pwm channel <n>`
   - Revert to auto: `su -c pwm channel auto`


