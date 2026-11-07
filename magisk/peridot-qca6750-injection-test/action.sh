#!/system/bin/sh
# KernelSU / APatch / Magisk Action Button toggle
MODDIR=${0%/*}
CM=$(cat /sys/module/qca_cld3_qca6750/parameters/con_mode 2>/dev/null || echo 0)

if [ "$CM" = "4" ]; then
	echo "[*] Switching back to STA (Managed Wi-Fi) mode..."
	pwm managed || pwm sta || (echo 0 > /sys/module/qca_cld3_qca6750/parameters/con_mode && svc wifi enable)
else
	echo "[*] Switching to Monitor + Packet Injection mode..."
	pwm monitor --force || /system/bin/peridot-wlan-mode monitor --force
fi
