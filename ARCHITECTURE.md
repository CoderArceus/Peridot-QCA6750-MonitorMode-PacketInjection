# Architecture & Technical Deep Dive: Peridot QCA6750 Packet Injection

This document describes the internal architecture, reverse-engineering findings, design hurdles, and solutions developed to achieve stable, native 802.11 monitor mode and raw packet injection on the **POCO F6 (`peridot`)**, powered by Qualcomm Snapdragon 8s Gen 3 (SM8635) and the Qualcomm FastConnect / QCA6750 Wi-Fi subsystem running Android 17 (Linux 6.1).

---

## 1. Background & Lineage

1. **Qualcomm QCACLD Architecture**:
   - Qualcomm's mobile Wi-Fi stack is split between the Linux kernel driver (`qcacld-3.0`), common datapath (`qca-wifi-host-cmn`), and firmware running on the onboard ARM processor inside the radio subsystem.
   - Unlike standard open-source desktop Wi-Fi drivers (`mac80211` / `cfg80211`), Qualcomm devices operate as "FullMAC" or "Host-Offload" devices: frame construction, rate control, power management, and scheduler queues are managed by the firmware via the Wireless Module Interface (WMI) and Host-Target Transport (HTT).

2. **Prior Work (Loukious / Konoha WCN7750)**:
   - Developer Loukious explored raw packet injection for Xiaomi 14 / SM8650 devices (`konoha`) using the WCN7750 chip.
   - Loukious pioneered the concept of using a companion Station (STA) virtual device (vdev) to provide a valid hardware transmit queue for raw frames.
   - However, Loukious's patch series also introduced a low-level Datapath (DP) Transmit Control Loop (TCL) exception ring hack (`cdp_tx_send_exc`) attempting to transmit frames on fake AP vdevs.

---

## 2. Obstacles Encountered & How They Were Solved

### Issue 1: Firmware Panic & Instant Reboot (`pcss_ssr_tm`)

* **Symptom**:
  Executing `aireplay-ng --test wlan0` immediately crashed the phone into a black screen, triggering Qualcomm PMIC watchdog reset and cold reboot.
* **Root Cause Analysis**:
  Kernel incident logs revealed:
  ```text
  pcss_ssr_tm: Subsystem restart assert triggered in wlan firmware
  ```
  Loukious's TCL exception ring hack bypassed the Qualcomm MAC scheduler and pushed raw skb buffers directly into firmware DMA ring descriptors. Because the monitor interface (`vdev=0`) lacks allocated hardware transmit flow rings, the firmware encountered illegal DMA memory accesses and panicked the radio coprocessor, tripping the SoC subsystem restart.
* **The Solution**:
  - Reverted `core/dp/txrx/` and `cdp_txrx_ops.h` to pristine stock Qualcomm datapath.
  - Switched frame injection entirely to Qualcomm's native management command interface: `wmi_mgmt_unified_cmd_send()`.
  - Frame descriptors are tracked asynchronously through `wmi_mgmt_params` and completed cleanly via `WMI_MGMT_TX_COMPLETION_EVENTID`.
  - **Result**: Zero panics, zero reboots, 100% system stability.

---

### Issue 2: Silent Firmware Discard on Monitor Vdev

* **Symptom**:
  Frames transmitted via WMI returned completion status `1` (`WMI_MGMT_TX_COMP_TYPE_DISCARD`). Packets were never transmitted over the RF medium.
* **Root Cause Analysis**:
  Qualcomm's closed-source firmware hardcodes `WMI_VDEV_TYPE_MONITOR` as a receive-only promiscuous interface. The firmware scheduler drops any TX request targeting a monitor vdev ID.
* **The Solution (Companion STA Helper Vdev)**:
  Implemented in `peridot-modules/qcom/opensource/wlan/qcacld-3.0/core/wma/src/wma_data.c`:
  1. Driver dynamically allocates an unused vdev ID (e.g., `vdev_id=2`).
  2. Issues `wmi_unified_vdev_create_send()` with `type = WMI_VDEV_TYPE_STA`.
  3. Sends `wmi_unified_vdev_start_send()` tuned to the active monitor frequency (`chanfreq`).
  4. Calls `wmi_unified_peer_create_send()` to register a local hardware peer.
  5. Injected raw frames are directed to `helper->vdev_id`.
  6. Radio firmware transmits the frame and returns status `0` (`WMI_MGMT_TX_COMP_TYPE_COMPLETE_OK`).
  7. When monitor mode stops, `__wma_injection_destroy_helper()` cleanly tears down peer and vdev.

---

### Issue 3: Aircrack-ng Channel `-1` Error

* **Symptom**:
  Wireless audit utilities such as `airodump-ng` and `aireplay-ng` failed with:
  ```text
  Waiting for beacon frame on channel -1
  ```
* **Root Cause Analysis**:
  Many legacy 802.11 auditing utilities (including `airodump-ng` and `aireplay-ng`) query the operating channel via legacy Wireless Extensions (WEXT) ioctls (`SIOCGIWFREQ`, `SIOCGIWMODE`) when nl80211 returns monitor attributes. Qualcomm's stock driver did not bind WEXT handlers to `wlan_mon_drv_ops`.
* **The Solution**:
  Implemented in `peridot-modules/qcom/opensource/wlan/qcacld-3.0/core/hdd/src/wlan_hdd_main.c`:
  - Created `hdd_monitor_wext_handlers` implementing `SIOCGIWNAME`, `SIOCGIWMODE`, `SIOCGIWFREQ`, and `SIOCSIWFREQ`.
  - Bound handlers via `dev->wireless_handlers = &hdd_monitor_wext_handler_def`.
  - Tied `wlan_hdd_set_mon_chan` directly to `wma_injection_prepare` so changing channels automatically re-tunes the STA injection helper.

---

### Issue 4: Stock Kernel Compatibility & `CONFIG_MODVERSIONS`

* **Symptom**:
  Custom kernels broke Xiaomi's proprietary SmartPA audio amplifiers (`aw882xx` / `WL2866D`), causing system watchdog audio reboots. Reverting to stock OEM kernel gave `Exec format error` on loading custom modules.
* **Root Cause Analysis**:
  The OEM kernel enables `CONFIG_MODVERSIONS=y`. Every symbol imported by `qca_cld3_qca6750.ko` must have a 64-bit CRC bit-exact with the symbols in the running kernel's symbol table.
* **The Solution**:
  - Extracted 4,905 symbols and stock CRCs from all 403 companion modules in stock `vendor_dlkm.img` and `system_dlkm.img`.
  - Created `scripts/align_modversions.py`:
    - Reads the ELF `__versions` section of the compiled module.
    - Patches mismatched symbol CRCs with bit-exact OEM stock values.
    - Replaces unavailable symbols with stock equivalents (`schedule_work` via `system_wq`).
  - Achieved **487/487 (100.0%) CRC match**, allowing the driver to load cleanly on the untouched OEM stock kernel.

---

### Issue 5: Firmware Panic During Rapid Channel Hopping (`wash` / WPS Scanning)

* **Symptom**:
  Running `wash -i wlan0` printed `[!] Found packet with bad FCS, skipping...` and then immediately crashed the phone into a black screen / cold power-off.
* **Root Cause Analysis**:
  Crash logs (`/data/vendor/wlan_logs/pcss_ssr_tm`) revealed a Qualcomm WLAN firmware Subsystem Restart (SSR) assert.
  `wash` (built without `libnl-3`) hops channels every 1 second via `SIGALRM` using `ioctl(SIOCSIWFREQ)`.
  In `wlan_hdd_main.c`, `wlan_hdd_set_mon_chan()` previously called `wma_injection_prepare(vdev_id, freq)` synchronously on every channel frequency change.
  This teardown and recreation of the STA helper vdev and peer in firmware included `msleep()` delays totaling ~700ms per hop. In addition, `wash` hops across invalid frequencies (such as Channel 14 in non-JP regulatory domains). Rapidly deleting and recreating STA vdevs in firmware during continuous monitor packet reception overwhelmed WMI descriptor queues, triggering the firmware assertion and PMIC watchdog reset.
* **The Solution**:
  1. Decoupled helper preparation from channel hopping: removed `wma_injection_prepare()` from `wlan_hdd_set_mon_chan()`. The companion STA injection helper is prepared strictly on-demand during actual transmission (`wma_injection_send()`).
  2. Added frequency sanity validation (`if (!freq) return -EINVAL;`) in both `wlan_hdd_set_mon_chan()` and `hdd_monitor_wext_siwfreq()`.
  3. Added automatic channel reset on returning to managed mode (`pwm managed`).
  - **Result**: Channel hopping with `wash`, `airodump-ng`, or automated scanners runs 100% stable with zero reboots and zero firmware panics.

---

### Issue 6: 802.11 Data Frame (EAPOL / 802.1X) Drop in Injection Filter

* **Symptom**:
  Utilities attempting EAPOL handshakes (such as WPS exchanges) successfully authenticated and associated (`Associated with BSSID`), but timed out immediately upon sending `EAPOL START` with `Receive timeout occurred`.
* **Root Cause Analysis**:
  Dmesg revealed:
  ```text
  hdd_monitor_mode_tx_inject: monitor tx: dropping invalid injection frame len 36
  ```
  Authentication and Association are 802.11 Management frames (Type `0x00`), whereas EAPOL is an 802.11 Data frame (Type `0x02`, EtherType `0x888E` in LLC/SNAP). The injection validation function `hdd_injection_frame_is_valid()` in `wlan_hdd_tx_rx.c` strictly enforced `return ieee80211_is_mgmt(hdr->frame_control);`, silently dropping all non-management 802.11 frames before they reached WMI transmission.
* **The Solution**:
  - Expanded `hdd_injection_frame_is_valid()` to accept both management and data frame types:
    ```c
    return ieee80211_is_mgmt(hdr->frame_control) ||
           ieee80211_is_data(hdr->frame_control);
    ```
  - Over-the-air testing confirmed that Qualcomm QCA6750 target firmware transmits these frames cleanly via the companion STA helper vdev with completion `status=0` (`WMI_MGMT_TX_COMP_TYPE_COMPLETE_OK`), successfully completing full bidirectional EAPOL exchanges (EAPOL Start -> Identity Request/Response -> M1..M4 -> WSC NACK).

---

## 3. Acknowledgments & Credits

- **CoderArceus**: Peridot QCA6750 architecture port, crash elimination, WMI helper implementation, WEXT handlers, CLI wrappers, and stock CRC alignment.
- **Loukious**: Groundbreaking reference research on Qualcomm WMI management frame injection and STA helper vdev architecture.
- **Qualcomm & Xiaomi**: Original Linux kernel and QCACLD-3.0 codebase.

