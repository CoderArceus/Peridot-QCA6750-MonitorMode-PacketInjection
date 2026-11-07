#!/system/bin/sh
MODDIR="${0%/*}"
KREL="$(uname -r)"
MODULE="$MODDIR/qca_cld3_qca6750.ko"
PATCHER="$MODDIR/bin/patch_ko"

# Automatically adapt vermagic & symbol CRCs before overlayfs/magic mount
if [ -f "$MODULE" ] && [ -f "$PATCHER" ]; then
	chmod 0755 "$PATCHER" 2>/dev/null || true
	"$PATCHER" "$MODULE" "$KREL" >/dev/null 2>&1 || true
fi
