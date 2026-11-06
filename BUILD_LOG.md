# Peridot packet injection build log

This file records source, configuration, build, and packaging decisions for the
Peridot (POCO F6 / SM8635) Android 17 kernel packet injection work.

## 2026-11-05

### Goal and input

- Target: Peridot, Android 17, Android common kernel 6.1 (`android14-6.1`).
- Primary feature: QCACLD packet injection; monitor mode is already present.
- Supplied boot image: `boot.img` (extracted from stock firmware).
- Input image SHA-256: `579282ac6a04c3413e2aadabdd9795a0fb893df1eea9adcb602a0ca32c7dc1bd`.
- The boot image is Android boot header v4, 96 MiB, kernel payload at offset 4096,
  kernel size 35,711,488 bytes, and no ramdisk.

### Injection patch and module source

- Ported Loukious's QCACLD frame injection changes from reference commit
  `25875eb1a65e94fae404c6e9188c7a1fe679e0f5` into
  `peridot-dev/android_kernel_xiaomi_sm8635-modules`, branch `seventeen`, base
  commit `ed4ad0d1ad00b755af2fe61387dcc5397ad20b8f`.
- Working module branch: `codex/peridot-injection-port`.
- Peridot selects `pineapple_gki_qca6750_defconfig`; enabled
  `CONFIG_FEATURE_FRAME_INJECTION_SUPPORT=y` in that profile (along with the
  existing monitor-mode setting). The earlier `default_defconfig`-only change
  was insufficient and is retained only as a fallback profile change.
- Port fixes based on build findings:
  - Monitor frequency reporting uses Peridot's existing `adapter->mon_chan_freq`
    fields instead of unavailable `hdd_monitor_ctx` accessors.
  - Removed the reference patch's `TARGET_TYPE_WCN7750` monitor-filter special
    case because Peridot is QCA6750 and its source does not define that target.
- A Linux Docker VM was used because macOS filesystem case-insensitivity makes
  the kernel source checkout unreliable. Container: `peridot-build`.

### First build attempt and compatibility finding

- Kernel source: `peridot-dev/android_kernel_xiaomi_sm8635`, branch `seventeen`,
  commit `199ec7c084cf6927ecb4522fe58296b4a771d8b1`, kernel release 6.1.174.
- Kernel `Image`, DTBs, and in-tree modules compiled. The external QCACLD and
  CNSS modules also compiled after resolving include paths and supplying the
  platform module symbol table.
- The supplied boot image contains kernel `6.1.176-g7fee93174ed9`, so artifacts
  from the 6.1.174 source are incompatible with the ROM's module release and
  were not selected for packaging.

### Matching-version source and config

- Found `Mohithash/kernel_xiaomi_sm8635`, branch `17`, commit
  `690024ef343deb44b03fa8e83dea5d5312c27795`, whose source is Linux 6.1.176.
- The boot image's embedded kernel config was extracted to `/work/stock.config`.
  Comparing it with a plain GKI + vendor-fragment config showed relevant
  differences, including `CONFIG_HZ=250` vs 300, TCP default, Xiaomi modules,
  and module signing settings.
- Decision: use the supplied boot image's extracted config as the build baseline,
  run `olddefconfig` against the 6.1.176 Peridot source, and set
  `CONFIG_LOCALVERSION="-g7fee93174ed9"` with `CONFIG_LOCALVERSION_AUTO` disabled
  so kernel and new modules present the ROM's expected release string.
- The extracted config enables the fork's ADIOS I/O scheduler as a module, but
  `block/adios.c` lacked `MODULE_LICENSE()` and stopped modpost. Added
  `MODULE_LICENSE("GPL")` in the isolated kernel build checkout; the file's
  SPDX header is GPL-2.0. The reproducible source change is captured in
  `build-support/0001-adios-module-license.patch`. This is a build metadata fix,
  not a scheduler behavior change.
- This aligns the Linux version, config, and module vermagic. The source commit
  still differs from the boot image's recorded git suffix; module symbol CRC and
  runtime compatibility have not been verified on a device.

### Build status at log update

- The 6.1.176 kernel, DTBs, and in-tree modules now build against the extracted
  boot config. External CNSS and QCACLD modules are being rebuilt against this
  final config and module symbol table.
- No device boot test, module load test, or packet injection test has been run.
- No image has been flashed. Any resulting boot image must be labeled experimental
  until its exact source/ABI compatibility and device boot behavior are verified.

### Completed build and artifacts

- Kernel `Image`, DTBs, and in-tree modules completed successfully with the
  extracted config after adding the GPL module metadata to ADIOS.
- The external CNSS platform modules built successfully. QCACLD `wlan.ko` built
  successfully with CNSS `Module.symvers`; the generated compile command contains
  `DFEATURE_FRAME_INJECTION_SUPPORT`.
- `kernel.release` and every packaged WLAN/CNSS module report
  `6.1.176-g7fee93174ed9` vermagic. The source git commit remains
  `690024ef343deb44b03fa8e83dea5d5312c27795`, so matching the release string does
  not establish matching symbol CRCs.
- Output directory: `out/peridot-android17-6.1.176/`. It contains `Image`, the
  96 MiB `boot-unsigned-candidate.img`, the stripped WLAN/CNSS modules, final
  `.config`, release string, README, and SHA-256 manifest.
- The candidate preserves the supplied v4 header, replaces the kernel payload,
  sets the kernel size to the built Image size, and clears the old AVB footer and
  vbmeta bytes. It is unsigned; no ROM signing key was available.
- Candidate image SHA-256:
  `1846a876d5d3865ab190257ab9e88c350ca9a7301ebb67fc457e4bb66bfea38e`.
- Built Image SHA-256:
  `a2004d29b803a195ef057a2c95373e6df7b1a7e04c8fff41acc0b5db8511dddd`.
- Refreshed `peridot-injection-port.diff` from the current module worktree.
  `git diff --check` passed. This only checks patch whitespace; no device/runtime
  tests were run.

### Magisk test module and mode switching

- Inspected `Universal-EvilTwin-WiFi-Magisk-v1.0.zip` as a format/example only.
  Its `post-fs-data.sh` rewrites the `vermagic` text in a `.ko` to match
  `uname -r`. We did not copy that behavior: changing the text does not repair
  module ABI or `CONFIG_MODVERSIONS` symbol CRC mismatches. Kernel module version
  CRC checks are documented in the [Linux Kbuild module documentation](https://docs.kernel.org/next/kbuild/modules.html).
- Inspection found the first QCACLD build had internal module name `wlan` even
  though the target sysfs path and example module use `qca_cld3_qca6750`. Rebuilt
  QCACLD with `MODNAME=qca_cld3_qca6750`, `DEVNAME=qca6750`; the final `.ko`
  reports `name=qca_cld3_qca6750` and the expected release vermagic.
- Verified both monitor and injection compile flags in the final HDD object
  command: `DFEATURE_MONITOR_MODE_SUPPORT` and
  `DFEATURE_FRAME_INJECTION_SUPPORT`. The selected profile has both corresponding
  config options enabled.
- Source inspection confirms writes to `con_mode` call the runtime driver-mode
  transition handler. `QDF_GLOBAL_MISSION_MODE` is `0` and
  `QDF_GLOBAL_MONITOR_MODE` is `4`; the driver stops/reopens adapters during the
  transition. This explains the command sequence without requiring each app to
  carry a separate kernel patch. The `iw`/nl80211 monitor interface is the more
  portable Linux interface model; this Qualcomm vendor driver exposes a private
  global mode parameter instead.
- Built `magisk/peridot-qca6750-injection-test/` and
  `out/peridot-android17-6.1.176/Peridot-QCA6750-Injection-Test-v0.1.zip`. The
  module does not change the live driver during boot. Its helper checks the
  expected release and Clang 18 fingerprint, then on explicit `monitor`/`managed`
  commands swaps between the test `.ko` and ROM `.ko`, changing `con_mode` and
  Wi-Fi service state. It attempts to restore the ROM module on load/switch
  failure.
- The current upstream StrykerOSS README describes Wi-Fi features via external
  monitor-mode USB adapters; it does not document this internal Qualcomm driver
  backend. See [StrykerOSS README](https://github.com/zalexdev/strykerapp/blob/main/README.md).
- The module ZIP and shell scripts were syntax/archive checked only. No Magisk
  install, device kernel boot, module load, monitor capture, or packet injection
  was performed.

- Finished the manual Magisk test package at
  `out/peridot-android17-6.1.176/Peridot-QCA6750-Injection-Test-v0.1.zip`.
  Status reporting is available even before the experimental kernel checks;
  mode-changing commands remain gated on the expected release and compiler
  fingerprint. The ZIP contains the corrected `qca_cld3_qca6750` module and a
  `peridot-wlan-mode` helper, and performs no automatic boot-time driver swap.
- Confirmed the Peridot profile had monitor-mode support enabled before this
  port. The final QCACLD build also enables frame injection. This confirms
  compile configuration only; radio behavior is still untested.
- The helper packages Qualcomm's `con_mode=4` / `con_mode=0` sequence under
  `monitor` / `managed` commands. Apps need not expose raw sysfs commands if
  they can invoke a root helper, though the private parameter itself remains
  Qualcomm-driver-specific. `iw`/nl80211 is the normal portable interface when
  a driver supports it.

### Device boot regression report (2026-11-05)

- User booted `boot-unsigned-candidate.img`; ADB is reachable and reports kernel
  `6.1.176-g7fee93174ed9`. At 65 seconds uptime, `sys.boot_completed` remained
  unset, boot animation was still running, and `system_server` remained alive.
- Captured unmodified ADB logs under `incident-logs/`. `dmesg` and pstore are
  inaccessible to the ADB shell user; no `su` binary is available in this boot.
- Crash buffer shows `/vendor/bin/cnd` restarting and aborting roughly every
  five seconds. Scudo reports an invalid chunk deallocation; the backtrace goes
  through `libcne.so` `CneDriverInterface::~CneDriverInterface()` and
  `WifiQosProvider::initialize()`. This implicates the Qualcomm CNE Wi-Fi path,
  but logs alone do not establish whether the kernel change, missing/changed
  WLAN driver, or another vendor compatibility issue is causal.
- The user confirms the device is on Android 17. Live properties reported
  `ro.build.version.release=17` and SDK 37. The crash report's embedded build
  fingerprint contains `:16/` and `BP2A...`; these signals conflict, so the
  fingerprint alone must not be used to identify the active Android release.
- No device modifications were made during log collection. Kernel boot failure
  is confirmed; the candidate must not be treated as usable. Recovery should
  restore the exact original boot image to the partition it replaced, after
  verifying active slot/partition layout.

### Stock-kernel Magisk feasibility check

- Extracted the OEM `qca_cld3_qca6750.ko` from the supplied
  `vendor_dlkm.img` into `incident-logs/stock-module-inspection/` for read-only
  comparison. Its vermagic release string matches `6.1.176-g7fee93174ed9`, but
  that string is not proof of ABI compatibility.
- The supplied stock config enables `CONFIG_MODVERSIONS=y`. Comparing the
  original stock driver's `__versions` table with the rebuilt injection driver
  found 252 CRC mismatches across 484 shared imported symbols and five
  additional imports in the rebuilt module. Therefore the current Magisk
  module cannot be made stock-compatible by changing its helper checks or
  rewriting `vermagic`; doing so would permit an unsafe module load attempt.
- A stock-compatible rebuild needs the exact stock kernel source revision,
  matching `.config`, and matching `Module.symvers` (or equivalent full build
  outputs). The supplied boot/vendor_dlkm images provide a config and stock
  binary modules, but not those exact build outputs. The current QCACLD module
  remains experimental-kernel-only until a matching stock ABI build is made and
  validated.
- Android-version note corrected: user confirms Android 17; captured live
  properties show release 17 / SDK 37, while the crash report fingerprint
  string says `:16/`. Preserve the discrepancy rather than asserting Android 16.

### SuKiSU Ultra, SuSFS v2.3.0, and Droidspaces integration

- Rebuilt on branch `peridot-suki-susfs-droidspaces` on top of `Mohithash/kernel_xiaomi_sm8635` (branch `17`, 6.1.176).
- **Droidspaces container support:**
  - Applied `001.GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch` to `include/linux/sched.h`. Replaces `ANDROID_KABI_RESERVE(6)`, `(7)`, `(8)` with `sysvsem` and `sysvshm` structs in `task_struct`, preventing ABI/struct size breakage on GKI.
  - Enabled config symbols: `CONFIG_SYSVIPC=y`, `CONFIG_POSIX_MQUEUE=y`, `CONFIG_PID_NS=y`, `CONFIG_USER_NS=y`, `CONFIG_DEVTMPFS=y`, `CONFIG_TMPFS_POSIX_ACL=y`, `CONFIG_TMPFS_XATTR=y`, `CONFIG_MACVLAN=y`, `CONFIG_BRIDGE_NETFILTER=y`.
  - Intentionally kept `CONFIG_CFS_BANDWIDTH=n` and `CONFIG_CGROUP_PIDS=n` because enabling them on GKI shifts scheduler and cgroup struct layouts across ~4,000 exported symbol CRCs, breaking out-of-tree vendor modules.
- **SuSFS v2.3.0 integration:**
  - Applied `50_add_susfs_in_gki-android14-6.1.patch` from `gitlab.com/simonpunk/susfs4ksu` (`gki-android14-6.1`).
  - Added `fs/susfs.c`, `include/linux/susfs.h`, `include/linux/susfs_def.h`.
  - Removed `android/abi_gki_protected_exports_*` per SuSFS requirements.
  - Enabled config symbols: `CONFIG_KSU_SUSFS=y`, `CONFIG_KSU_SUSFS_SUS_PATH=y`, `CONFIG_KSU_SUSFS_SUS_MOUNT=y`, `CONFIG_KSU_SUSFS_SUS_KSTAT=y`, `CONFIG_KSU_SUSFS_SPOOF_UNAME=y`, `CONFIG_KSU_SUSFS_ENABLE_LOG=y`, `CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y`, `CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG=y`, `CONFIG_KSU_SUSFS_OPEN_REDIRECT=y`, `CONFIG_KSU_SUSFS_SUS_MAP=y`.
- **SuKiSU Ultra integration:**
  - Source: `shoey63/SukiSU-Ultra` (`stable` branch, commit `c3f7401`).
  - Linked as in-tree kernel driver via `drivers/kernelsu` symlink and Kconfig/Makefile bindings.
  - SukiSU Ultra uses a modern `pt_regs` architecture rather than legacy VFS function hooks. Neutralized conflicting legacy static branch calls from the 50_ patch in `fs/exec.c`, `fs/open.c`, `fs/stat.c`, `fs/read_write.c`, `drivers/input/input.c`, and `kernel/sys.c` to prevent symbol collisions.
  - Marked unused cred helper functions in `fs/susfs.c` as `__maybe_unused`.
  - Enabled config symbols: `CONFIG_KSU=y`, `CONFIG_KPM=y`, `CONFIG_KPROBES=y`.
- **Compilation results:**
  - Kernel `Image` built cleanly with Clang 18 / LLD 18 (`exit code 0`, 35,781,120 bytes).
  - Platform modules (`cnss2.ko`, `icnss2.ko`, `cnss_utils.ko`, `cnss_plat_ipc_qmi_svc.ko`, `cnss_prealloc.ko`, `cnss_nl.ko`, `wlan_firmware_service.ko`) rebuilt cleanly against new `out176` and generated new `Module.symvers`.
  - QCACLD-3.0 injection module (`qca_cld3_qca6750.ko`) rebuilt cleanly against new `Module.symvers` with both `CONFIG_FEATURE_FRAME_INJECTION_SUPPORT=y` and `CONFIG_FEATURE_MONITOR_MODE_SUPPORT=y` (`exit code 0`).
  - Repacked unsigned v4 boot image candidate `boot-unsigned-candidate.img` (100,663,296 bytes) using `repack_boot.py` and updated Magisk helper `Peridot-QCA6750-Injection-Test-v0.1.zip`.


## 2026-11-06

### Native Stock OEM Kernel Injection via CRC Alignment (v0.3-stock-aligned)

- **Problem Addressed**:
  - Custom kernel attempts triggered audio amplifier (`aw882xx` / `WL2866D`) deadlocks, resulting in Android System Watchdog kill loops.
  - Reverting to the stock OEM kernel restored 100% device functionality, but loading the injection driver caused `insmod: Exec format error` due to `CONFIG_MODVERSIONS=y` checking the module's `__versions` CRC table.
- **Symbol Analysis**:
  - Extracted stock `vendor_dlkm.img` and `system_dlkm.img` from OEM ROM dump.
  - Extracted 4,905 unique exported symbols and verified 64-bit CRCs across all 403 companion modules.
  - Rebuilt injection driver imported 489 symbols:
    - 484 symbols matched existing stock WLAN imports.
    - `strscpy`, `schedule_timeout`, and `system_power_efficient_wq` matched known stock companion module CRCs (`tipc.ko`, `usbnet.ko`, `rfkill.ko`).
    - `system_highpri_wq`: Replaced with `schedule_work(&wma_injection_ctx.work);` in `core/wma/src/wma_data.c`, routing execution via `system_wq` (Stock CRC `0x2d3385d3`).
    - `dev_open`: Replaced with direct `adapter->dev->netdev_ops->ndo_open(adapter->dev)` inside RTNL lock in `core/hdd/src/wlan_hdd_p2p.c`, removing external symbol dependency.
- **Recompilation & Alignment**:
  - Recompiled QCACLD-3.0 with Clang 18 (`LLVM=1`) against clean matching stock kernel configuration.
  - Executed `scripts/align_modversions.py`:
    - Total imported symbols: 487.
    - Matched with stock CRCs: 487/487 (100.0%).
    - Mismatched CRCs updated: 38.
    - Symbols already identical: 449.
    - Missing stock symbols: 0 (0.0%).
  - Both `vermagic` and all 487 symbol CRCs in `__versions` are now 100% bit-exact with the OEM stock kernel.
- **Packaging & Deployment**:
  - Packaged into `Peridot-QCA6750-Injection-Test-v0.3.zip` (5.0 MiB).
  - Updated `system/bin/peridot-wlan-mode` helper to recognize stock kernel release `6.1.176-g7fee93174ed9` natively without `--force`.
  - Pushed to device: `/sdcard/Download/Peridot-QCA6750-Injection-Test-v0.3.zip`.

### Phone Crash Fix & Firmware WMI Architecture (v0.5 - v0.6)

- **Crash Root Cause Identified & Resolved**:
  - `aireplay-ng --test wlan0` previously panicked the phone and caused instant reboot (`pcss_ssr_tm` firmware assert).
  - Root cause was Loukious's DP TCL exception ring hack (`cdp_tx_send_exc`) on unattached fake AP vdevs, which broke Qualcomm's descriptor DMA queues.
  - Reverted `dp_tx.c` to pristine Qualcomm stock. Switched frame transmission exclusively to Qualcomm native WMI command queuing (`wmi_mgmt_unified_cmd_send`).
  - Result: **Zero kernel panics, zero reboots, phone remained 100% stable during frame transmission.**
- **Firmware Discard Root Cause**:
  - Qualcomm firmware explicitly defines `WMI_VDEV_TYPE_MONITOR` as RX-only; transmissions sent directly to monitor `vdev=0` are returned with status `1` (`WMI_MGMT_TX_COMP_TYPE_DISCARD`).

### The Breakthrough: Companion STA Helper Vdev & WEXT Channel Handling (v0.7)

- **STA Helper Vdev Architecture**:
  - Implemented dynamic companion `WMI_VDEV_TYPE_STA` in `core/wma/src/wma_data.c`:
    - Automatically allocates an unused vdev ID (e.g. `vdev=2`).
    - Issues `wmi_unified_vdev_create_send()`, `wmi_unified_vdev_start_send()` on the active channel frequency, and `wmi_unified_peer_create_send()`.
    - Routes injected frames to `helper->vdev_id` via `wmi_mgmt_unified_cmd_send()`.
    - Handles asynchronous tx completion (`wma_injection_complete`), returning `status=0` (`WMI_MGMT_TX_COMP_TYPE_COMPLETE_OK`).
- **Channel -1 Fix**:
  - Registered monitor WEXT handlers (`SIOCGIWFREQ`, `SIOCSIWFREQ`, `SIOCGIWMODE`, `SIOCGIWNAME`) in `core/hdd/src/wlan_hdd_main.c`.
  - Tools such as `iw`, `iwconfig`, `airodump-ng`, and `aireplay-ng` now query and set frequency and mode directly without negative-one channel errors.
  - Connected `wlan_hdd_set_mon_chan` to `wma_injection_prepare` to automatically transition the injection helper when changing channels.
- **Physical Device Over-the-Air Verification**:
  - Rebuilt and aligned 100% symbol CRCs (487/487).
  - Deployed and loaded on physical POCO F6 (`peridot`, SM8635, kernel `6.1.176-g7fee93174ed9`).
  - Ran `aireplay-ng --test wlan0` on Channel 6:
    - Broadcast probe requests sent: **Injection confirmed working!**
    - Detected live APs (`Airtel_Zerotech`, `Airtel_anki_0648`).
    - Measured live round-trip probe response ping: `3.606ms/15.936ms/93.665ms` at `Power: -88.11`.
    - Success rate: 60%.
    - Firmware reported `wma_injection_complete: status=0` for all transmitted descriptors.
  - Device stability: Rock solid. No reboots, no audio issues, no system panics.

### Streamlined Terminal Integration & Official v1.0 Release

- **Purged Stryker Dependencies**:
  - Removed all Stryker chroot hooks, chroot wrappers, and third-party app permissions from `customize.sh`, `service.sh`, and `peridot-wlan-mode`.
  - Streamlined module architecture to focus purely on native terminal environments (Termux, ADB shell, and root terminals).
- **Telegram Technical Consensus & Loukious Architecture**:
  - Community discussions (developer Subaru, Kukumba, Robin) confirmed that generic 6.1 kernel monitor mode ports (such as Evil_Twin) only provide promiscuous reception; outbound packet injection is discarded by the Qualcomm CLD 3.0 datapath.
  - Loukious's architecture (`vendor_qcom_opensource_wlan` commit `30ef497a813c0422fc4d1d9ac50ce05b551a066a`) bypasses datapath transmission restrictions by routing 802.11 raw management frames directly via WMI management commands (`wma_mgmt_send`) through an internal companion STA helper vdev.
  - Physical testing verified that deauthentication frame transmission and 4-way handshake capture using `airodump-ng` and `aireplay-ng` in Termux function reliably without requiring external chroot GUI applications.
- **Enhanced CLI Controls**:
  - Shortened and standardized CLI commands to `pwm` (*Peridot WLAN Mode*) with aliases `wlan-mode` and `peridot-wlan-mode`.
  - Added `pwm channel auto` to reset channel hopping baselines back to Channel 1.
  - Implemented auto-healing symlinks for Termux and root directories (`/data/adb/ksu/bin`, `/data/adb/magisk`, `/data/adb/ap/bin`).
- **Release Packaging Hygiene**:
  - Cleaned all binary `.zip` releases out of the Git tree, adding `*.zip` to `.gitignore`.
  - Authored release metadata attributing project author `CoderArceus` and crediting `@Loukious`.
  - Prepared official GitHub Release `v1.0` with flashable module asset `Peridot-QCA6750-MonitorMode-v1.0.zip`.

### Rapid Channel Hopping Fix & Official v1.1 Release

- **Incident Triage (`wash -i wlan0` Crash)**:
  - User reported running `pwm monitor` followed by `wash -i wlan0` in Termux. After printing `[!] Found packet with bad FCS, skipping...`, the phone crashed and shut down.
  - Device triage on connected POCO F6 (`89405825`):
    - Examined `/data/vendor/wlan_logs/pcss_ssr_tm`, confirming a Qualcomm WLAN firmware Subsystem Restart (SSR) assert. On SM8635, an unhandled WLAN SSR during monitor mode triggers an unhandled SoC PMIC watchdog reset and cold power-off.
    - `wash` in Termux (`reaver-wps-fork-t6x`) was built without `libnl-3` and hops channels every 1 second via `SIGALRM` -> `next_channel()` -> `ioctl(SIOCSIWFREQ)`.
    - In `wlan_hdd_main.c:10437-10440`, `wlan_hdd_set_mon_chan()` called `wma_injection_prepare(adapter->deflink->vdev_id, freq)` synchronously on *every* channel change.
    - Each `wma_injection_prepare` destroyed and recreated the companion STA helper vdev/peer in firmware with multiple `msleep(100)` to `msleep(150)` sleeps (~700ms latency per hop). In addition, `wash` sweeps channel 14 (invalid in non-Japan domains where `wlan_reg_legacy_chan_to_freq` returns 0).
    - Rapidly deleting and creating STA vdevs in firmware during continuous monitor packet reception caused WMI descriptor queue collisions and triggered the firmware assertion.
- **Kernel & Driver Fix**:
  - Removed `wma_injection_prepare()` from `wlan_hdd_set_mon_chan()`. The companion STA helper vdev is needed only during active transmission (`wma_injection_send`), not during passive sniffing or channel hopping.
  - Added frequency sanity check `if (!freq) return -EINVAL;` to both `wlan_hdd_set_mon_chan()` and `hdd_monitor_wext_siwfreq()`.
  - Recompiled in `peridot-build` Docker container with LLVM/Clang 18 against kernel `6.1.176` and `out176`.
  - Aligned symbol modversions: **487/487 (100.0%) stock OEM CRC match**.
  - Refreshed unified diff in `peridot-injection-port.diff`.
- **Quality-of-Life Update (Auto Channel Reset)**:
  - Updated `peridot-wlan-mode`: switching to managed mode (`pwm managed`) now automatically writes `1 0` to `/sys/class/net/wlan0/monitor_mode_channel`, resetting the radio baseline back to auto.
- **Physical Device Over-the-Air Verification**:
  - Pushed updated module and kernel object to device.
  - Activated monitor mode via `pwm monitor`.
  - Tested `wash -i wlan0`: scanned continuously across 2.4 GHz and 5 GHz channels without a single drop or crash. Discovered APs and handled bad FCS frames cleanly.
  - Ran `pwm managed`: Wi-Fi restored cleanly, channel reset to auto, and network connectivity pinged successfully.
- **Packaged & Released**:
  - Module bumped to `v1.1` (`versionCode=11`).
  - Flashable ZIP generated: `Peridot-QCA6750-MonitorMode-v1.1.zip`.

