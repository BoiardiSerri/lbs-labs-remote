#!/bin/bash
# Crea il DMG con lo sfondo LBS (dmgbuild: niente Finder/AppleScript, affidabile sui server di build).
# Uso: bash packaging/macos/make_dmg.sh LBS-Labs-Remote-macOS.dmg
set -euo pipefail
OUT="${1:-LBS-Labs-Remote-macOS.dmg}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ICONS="$HERE/../icons"
# sfondo nitido anche su Retina: TIFF con le due risoluzioni
tiffutil -cathidpicheck "$ICONS/dmg-background.png" "$ICONS/dmg-background@2x.png" -out "$ICONS/dmg-background.tiff"
rm -f "$OUT"
for i in 1 2 3; do   # hdiutil sui server di build a volte è "occupato": riprova
  if dmgbuild -s "$HERE/dmg_settings.py" -D app="dist/LBS Labs Remote.app" \
       -D background="$ICONS/dmg-background.tiff" "LBS Labs Remote" "$OUT"; then
    echo "Creato $OUT"; exit 0
  fi
  sleep 5
done
exit 1
