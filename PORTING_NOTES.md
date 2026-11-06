# Peridot QCACLD frame injection port

## Source and patch

- Module base: `peridot-dev/android_kernel_xiaomi_sm8635-modules`, branch
  `seventeen`, base commit `ed4ad0d1ad00b755af2fe61387dcc5397ad20b8f`.
- Work branch: `codex/peridot-injection-port` in `peridot-modules/`.
- Reference: Loukious's QCACLD 3.0 direct injection commit
  `25875eb1a65e94fae404c6e9188c7a1fe679e0f5` (`konoha-kernel-gki`, Android
  15/6.6 lineage).
- Peridot selects `pineapple_gki_qca6750_defconfig`; this profile and
  `default_defconfig` enable `CONFIG_FEATURE_FRAME_INJECTION_SUPPORT=y`.
- Build-driven adaptations use Peridot's existing adapter monitor frequency
  fields and remove the reference's WCN7750-only filter condition, which does
  not apply to QCA6750.

## Build result

The 6.1.176 Peridot kernel, DTBs, and in-tree modules compiled successfully with
the config extracted from the supplied boot image. The external QCACLD module
compiled with `DFEATURE_FRAME_INJECTION_SUPPORT` and linked through modpost using
the matching CNSS platform module symbol table. Build artifacts are under
[`out/peridot-android17-6.1.176/`](out/peridot-android17-6.1.176/).

See [BUILD_LOG.md](BUILD_LOG.md) for source selections, build commands, config
decisions, compatibility findings, and the ADIOS module metadata fix.

## Verification & Status

With the development of `scripts/align_modversions.py`, 100% of imported symbol CRCs (487/487) were aligned with Xiaomi's stock OEM kernel symbol table under `CONFIG_MODVERSIONS=y`.

- **Device Verification**: Tested on a physical POCO F6 running Android 17 (Linux `6.1.176-g7fee93174ed9`).
- **Stability**: Elimination of the DP TCL exception hack in favor of native Qualcomm WMI frame queuing completely resolved radio firmware panics (`pcss_ssr_tm`).
- **Packet Transmission**: Active frame transmission verified over-the-air with `aireplay-ng --test wlan0` and standard terminal monitoring tools.
- **Stock Integrity**: Xiaomi OEM proprietary hardware drivers (including SmartPA audio amplifiers) remain completely intact on the untouched factory kernel.
