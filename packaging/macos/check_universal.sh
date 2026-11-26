#!/bin/bash
# Verifica che l'app funzioni nativamente sia su Intel sia su Apple Silicon:
#  - l'eseguibile principale deve contenere x86_64 e arm64;
#  - ogni libreria usata dalla parte arm64 deve contenere arm64.
# Le librerie solo-Intel sono ammesse solo se nessuna parte arm64 le usa
# (es. librerie X11 incluse nella versione Intel di Pillow).
# Uso: bash packaging/macos/check_universal.sh "dist/LBS Labs Remote.app"
set -uo pipefail
APP="$1"
MAIN="$APP/Contents/MacOS/LBSLabsRemote"
fail=0
archs=$(lipo -archs "$MAIN")
echo "eseguibile principale: $archs"
[[ " $archs " == *" arm64 "* && " $archs " == *" x86_64 "* ]] || { echo "ERRORE: eseguibile non universale"; fail=1; }

arm_deps=$(mktemp); x86_only=$(mktemp); n=0
while IFS= read -r -d '' f; do
  file "$f" | grep -q "Mach-O" || continue
  n=$((n+1))
  a=" $(lipo -archs "$f" 2>/dev/null) "
  if [[ "$a" == *" arm64 "* ]]; then
    otool -arch arm64 -L "$f" 2>/dev/null | tail -n +2 | awk '{print $1}' | xargs -n1 basename >> "$arm_deps"
  else
    echo "$(basename "$f")|$f" >> "$x86_only"
  fi
done < <(find "$APP" -type f -print0)
echo "componenti binari: $n, solo-Intel: $(wc -l < "$x86_only")"
while IFS='|' read -r name path; do
  if grep -qxF "$name" "$arm_deps"; then
    echo "ERRORE: $path è solo Intel ma serve anche alla parte Apple Silicon"; fail=1
  else
    echo "ok (usata solo dalla parte Intel): $name"
  fi
done < "$x86_only"
exit $fail
