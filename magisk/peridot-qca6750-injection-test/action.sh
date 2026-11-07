#!/system/bin/sh
# KernelSU / APatch / Magisk Action Button toggle
MODDIR="${0%/*}"
EXEC=""
if [ -x "$MODDIR/system/bin/peridot-wlan-mode" ]; then
	EXEC="$MODDIR/system/bin/peridot-wlan-mode"
elif command -v pwm >/dev/null 2>&1; then
	EXEC="pwm"
elif [ -x /system/bin/peridot-wlan-mode ]; then
	EXEC="/system/bin/peridot-wlan-mode"
fi

CM=$(cat /sys/module/qca_cld3_qca6750/parameters/con_mode 2>/dev/null || echo 0)

if [ "$CM" = "4" ]; then
	echo "[*] Switching back to STA (Managed Wi-Fi) mode..."
	if [ -n "$EXEC" ]; then
		"$EXEC" managed
	else
		echo 0 > /sys/module/qca_cld3_qca6750/parameters/con_mode 2>/dev/null || true
		svc wifi enable 2>/dev/null || true
	fi
else
	echo "[*] Switching to Monitor + Packet Injection mode..."
	if [ -n "$EXEC" ]; then
		"$EXEC" monitor --force
	else
		echo 4 > /sys/module/qca_cld3_qca6750/parameters/con_mode 2>/dev/null || true
	fi
fi
