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

# Hook Stryker chroot if present
STRYKER_ROOT="/data/local/stryker/release"
if [ -d "$STRYKER_ROOT" ]; then
	# Ensure airmon-ng PATH and monitor start/stop intercept
	if [ -f "$STRYKER_ROOT/usr/sbin/airmon-ng" ]; then
		if ! grep -q "peridot-wlan-mode" "$STRYKER_ROOT/usr/sbin/airmon-ng" 2>/dev/null; then
			sed -i '2i export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH\nif [ "$1" = "start" ]; then /system/bin/peridot-wlan-mode monitor >/dev/null 2>&1; echo "wlan0 (monitor mode enabled)"; exit 0; fi\nif [ "$1" = "stop" ]; then /system/bin/peridot-wlan-mode managed >/dev/null 2>&1; echo "wlan0 (managed mode enabled)"; exit 0; fi' "$STRYKER_ROOT/usr/sbin/airmon-ng" 2>/dev/null || true
		fi
	fi
	if [ -f "$STRYKER_ROOT/usr/sbin/iw" ] && ! head -n 1 "$STRYKER_ROOT/usr/sbin/iw" 2>/dev/null | grep -q "^#"; then
		cp -f "$STRYKER_ROOT/usr/sbin/iw" "$STRYKER_ROOT/usr/sbin/iw.real" 2>/dev/null || true
		chmod 0755 "$STRYKER_ROOT/usr/sbin/iw.real" 2>/dev/null || true
	fi
	if [ -f "$MODDIR/system/bin/iw" ] && [ -d "$STRYKER_ROOT/usr/sbin" ]; then
		cp -f "$MODDIR/system/bin/iw" "$STRYKER_ROOT/usr/sbin/iw" 2>/dev/null || true
		chmod 0755 "$STRYKER_ROOT/usr/sbin/iw" 2>/dev/null || true
		ln -sf /usr/sbin/iw "$STRYKER_ROOT/usr/bin/iw" 2>/dev/null || true
	fi
	if [ -f "$STRYKER_ROOT/usr/sbin/iwconfig" ] && ! head -n 1 "$STRYKER_ROOT/usr/sbin/iwconfig" 2>/dev/null | grep -q "^#"; then
		cp -f "$STRYKER_ROOT/usr/sbin/iwconfig" "$STRYKER_ROOT/usr/sbin/iwconfig.real" 2>/dev/null || true
		chmod 0755 "$STRYKER_ROOT/usr/sbin/iwconfig.real" 2>/dev/null || true
	fi
	if [ -f "$MODDIR/system/bin/iwconfig" ] && [ -d "$STRYKER_ROOT/usr/sbin" ]; then
		cp -f "$MODDIR/system/bin/iwconfig" "$STRYKER_ROOT/usr/sbin/iwconfig" 2>/dev/null || true
		chmod 0755 "$STRYKER_ROOT/usr/sbin/iwconfig" 2>/dev/null || true
		ln -sf /usr/sbin/iwconfig "$STRYKER_ROOT/usr/bin/iwconfig" 2>/dev/null || true
	fi
	for app in airodump-ng aireplay-ng airmon-ng; do
		if [ -f "$STRYKER_ROOT/usr/sbin/$app" ] && [ ! -e "$STRYKER_ROOT/usr/bin/$app" ]; then
			ln -sf "/usr/sbin/$app" "$STRYKER_ROOT/usr/bin/$app" 2>/dev/null || true
		fi
	done
fi

