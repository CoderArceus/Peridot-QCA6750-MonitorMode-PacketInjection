#!/system/bin/sh
MODDIR="${0%/*}"
KREL="$(uname -r)"
MODULE="$MODDIR/qca_cld3_qca6750.ko"
PATCHER="$MODDIR/bin/patch_ko"

# Enforce permissions & SELinux context
chmod -R 0755 "$MODDIR" 2>/dev/null || true
chmod 0644 "$MODULE" "$MODDIR/kernel.release" 2>/dev/null || true
chcon -R u:object_r:system_file:s0 "$MODDIR" 2>/dev/null || true

# Automatically adapt vermagic & symbol CRCs before overlayfs/magic mount
if [ -f "$MODULE" ] && [ -f "$PATCHER" ]; then
	"$PATCHER" "$MODULE" "$KREL" >/dev/null 2>&1 || true
fi

