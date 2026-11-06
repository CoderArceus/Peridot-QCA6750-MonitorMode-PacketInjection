#!/system/bin/sh
MODDIR="${0%/*}"

# Sync helper to Termux if installed
for termux_bin in /data/data/com.termux/files/usr/bin /data/user/0/com.termux/files/usr/bin; do
	if [ -d "$termux_bin" ]; then
		rm -f "$termux_bin/peridot-wlan-mode" "$termux_bin/pwm" "$termux_bin/wlan-mode"
		cp -f "$MODDIR/system/bin/peridot-wlan-mode" "$termux_bin/peridot-wlan-mode" 2>/dev/null || true
		chmod 0755 "$termux_bin/peridot-wlan-mode" 2>/dev/null || true
		(
			cd "$termux_bin" || exit 0
			ln -sf peridot-wlan-mode pwm 2>/dev/null || true
			ln -sf peridot-wlan-mode wlan-mode 2>/dev/null || true
		)
	fi
done

# Sync shortcuts to KernelSU / Magisk / APatch root paths
for root_bin in /data/adb/ksu/bin /data/adb/magisk /data/adb/ap/bin; do
	if [ -d "$root_bin" ]; then
		for alias_name in wlan-mode pwm peridot-wlan-mode; do
			ln -sf "/data/adb/modules/peridot-qca6750-injection-test/system/bin/peridot-wlan-mode" "$root_bin/$alias_name" 2>/dev/null || true
		done
	fi
done
