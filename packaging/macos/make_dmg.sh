#!/bin/bash
# Crea il DMG: RemoteLAN.app + collegamento ad Applicazioni + istruzioni.
# Uso: bash packaging/macos/make_dmg.sh RemoteLAN-macOS.dmg
set -euo pipefail
OUT="${1:-RemoteLAN-macOS.dmg}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
cp -R dist/RemoteLAN.app "$STAGE/"
ln -s /Applications "$STAGE/Applicazioni"
cp "$HERE/LEGGIMI.txt" "$STAGE/LEGGIMI - Come installare.txt"
rm -f "$OUT"
for i in 1 2 3 4 5; do   # hdiutil sui server di build a volte è "occupato": riprova
  if hdiutil create -volname "RemoteLAN" -srcfolder "$STAGE" -ov -format UDZO "$OUT"; then
    echo "Creato $OUT"; exit 0
  fi
  sleep 5
done
exit 1
