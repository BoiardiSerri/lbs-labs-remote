#!/bin/bash
# Crea il DMG: LBS Labs Remote.app + collegamento ad Applicazioni + istruzioni.
# Uso: bash packaging/macos/make_dmg.sh LBS-Labs-Remote-macOS.dmg
set -euo pipefail
OUT="${1:-LBS-Labs-Remote-macOS.dmg}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
cp -R "dist/LBS Labs Remote.app" "$STAGE/"
ln -s /Applications "$STAGE/Applicazioni"
cp "$HERE/LEGGIMI.txt" "$STAGE/LEGGIMI - Come installare.txt"
rm -f "$OUT"
for i in 1 2 3 4 5; do   # hdiutil sui server di build a volte è "occupato": riprova
  if hdiutil create -volname "LBS Labs Remote" -srcfolder "$STAGE" -ov -format UDZO "$OUT"; then
    echo "Creato $OUT"; exit 0
  fi
  sleep 5
done
exit 1
