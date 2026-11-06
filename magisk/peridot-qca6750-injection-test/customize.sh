ui_print "- Peridot QCA6750 Monitor Mode & Packet Injection"
ui_print "- Target: POCO F6 (peridot) - Android 17 / Linux 6.1"
ui_print "- Compatible with KernelSU, SuKiSU Ultra, APatch, and Magisk"

[ -f "$MODPATH/qca_cld3_qca6750.ko" ] || abort "! Missing QCA6750 WLAN module"
[ -f "$MODPATH/system/bin/peridot-wlan-mode" ] || abort "! Missing mode helper"

# 1. Set recursive directory and file permissions
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/bin" 0 0 0755 0755
set_perm "$MODPATH/system/bin/peridot-wlan-mode" 0 0 0755
[ -f "$MODPATH/system/bin/iw" ] && set_perm "$MODPATH/system/bin/iw" 0 0 0755
[ -f "$MODPATH/system/bin/iwconfig" ] && set_perm "$MODPATH/system/bin/iwconfig" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/kernel.release" 0 0 0644
set_perm "$MODPATH/qca_cld3_qca6750.ko" 0 0 0644

# 2. Set SELinux context so the shell can execute the helper under Enforcing
chcon -R u:object_r:system_file:s0 "$MODPATH/system" 2>/dev/null || true

# 3. Create direct executable shortcuts in module
chmod 0755 "$MODPATH/system/bin/peridot-wlan-mode" 2>/dev/null || true
ln -sf peridot-wlan-mode "$MODPATH/system/bin/wlan-mode" 2>/dev/null || true
ln -sf peridot-wlan-mode "$MODPATH/system/bin/pwm" 2>/dev/null || true
ln -sf system/bin/peridot-wlan-mode "$MODPATH/wlan-mode" 2>/dev/null || true
ln -sf system/bin/peridot-wlan-mode "$MODPATH/pwm" 2>/dev/null || true
ln -sf system/bin/peridot-wlan-mode "$MODPATH/peridot-wlan-mode" 2>/dev/null || true

# 4. Link into root PATHs (KernelSU, Magisk, APatch)
FINAL_MOD_BIN="/data/adb/modules/peridot-qca6750-injection-test/system/bin/peridot-wlan-mode"
for root_bin in /data/adb/ksu/bin /data/adb/magisk /data/adb/ap/bin /data/adb; do
  if [ -d "$root_bin" ]; then
    ui_print "- Linking shortcuts into root PATH: $root_bin"
    for alias_name in wlan-mode pwm peridot-wlan-mode; do
      ln -sf "$FINAL_MOD_BIN" "$root_bin/$alias_name" 2>/dev/null || true
    done
  fi
done

# 5. If Termux is installed, copy helper script directly into Termux usr/bin so it works in tsu and non-root
for termux_bin in /data/data/com.termux/files/usr/bin /data/user/0/com.termux/files/usr/bin; do
  if [ -d "$termux_bin" ]; then
    ui_print "- Installing helper into Termux usr/bin: $termux_bin"
    rm -f "$termux_bin/peridot-wlan-mode" "$termux_bin/pwm" "$termux_bin/wlan-mode"
    cp -f "$MODPATH/system/bin/peridot-wlan-mode" "$termux_bin/peridot-wlan-mode" 2>/dev/null || true
    chmod 0755 "$termux_bin/peridot-wlan-mode" 2>/dev/null || true
    (
      cd "$termux_bin" || exit 0
      ln -sf peridot-wlan-mode pwm 2>/dev/null || true
      ln -sf peridot-wlan-mode wlan-mode 2>/dev/null || true
    )
  fi
done

ui_print "--------------------------------------------------"
ui_print " Installation complete!"
ui_print " Commands available in root shell or Termux:"
ui_print "   su -c pwm status"
ui_print "   su -c pwm monitor"
ui_print "   su -c pwm channel <1-165|auto>"
ui_print "   su -c pwm managed"
ui_print ""
ui_print " Short aliases: pwm, wlan-mode, peridot-wlan-mode"
ui_print " If Termux is installed later, service.sh"
ui_print " will automatically link shortcuts on next boot,"
ui_print " or immediately upon first running 'su -c pwm'."
ui_print "--------------------------------------------------"
