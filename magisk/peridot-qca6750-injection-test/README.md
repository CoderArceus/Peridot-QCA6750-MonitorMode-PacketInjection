# Peridot QCA6750 injection test module

This Magisk ZIP installs the rebuilt `qca_cld3_qca6750.ko` and a root helper.
It does not replace or unload the ROM WLAN module during boot. The helper checks
both the expected kernel release and the Clang 18 build fingerprint before it
will switch drivers.

**This package is not compatible with the stock kernel.** The stock config has
`CONFIG_MODVERSIONS=y`; a comparison against the stock QCACLD module found 252
different symbol CRCs among 484 shared imports, plus five imports absent from
that stock module. Changing `vermagic` or relaxing the helper's build check
cannot correct this ABI mismatch. A stock-compatible module requires rebuilding
QCACLD against the exact stock kernel source/configuration and its matching
`Module.symvers`, then validating it on-device.

After booting the matching experimental kernel:

```sh
su -c peridot-wlan-mode status
su -c peridot-wlan-mode monitor
# Run authorized monitor/injection checks in the test app or a root shell.
su -c peridot-wlan-mode managed
```

`monitor` disables Android Wi-Fi, unloads the currently loaded WLAN module,
loads the test module, writes `4` to `con_mode`, and brings `wlan0` up. `managed`
unloads the test module, reloads the ROM module, sets `con_mode` to `0`, and
reenables Android Wi-Fi. If the test module fails to load or mode switching
fails, the helper attempts to restore the ROM module.

The ZIP does not rewrite `vermagic`; changing that text cannot repair a kernel
ABI or symbol-version mismatch. The custom kernel and module are still
experimental. The exact stock kernel source/build symbol data has not been
obtained, and the device has not been used to validate module loading, monitor
mode, or packet injection.
