#!/bin/bash
# Prova sull'emulatore: installa l'APK, lo collega all'agente di prova (sul computer che ospita
# l'emulatore: 10.0.2.2), controlla che arrivino i frame e che un tocco diventi un clic.
# Uso: tools/android_e2e.sh app.apk fake_agent.log
set -u
APK="$1"; AGENT_LOG="$2"
adb install -r "$APK" || exit 1
adb logcat -c
adb shell am start -n com.lbslabs.remote/.MainActivity --es connect 10.0.2.2
ok=0
for i in $(seq 1 40); do
  if adb logcat -d -s LBS:I | grep -q "first frame"; then ok=1; break; fi
  sleep 1
done
adb logcat -d -s LBS:I | tail -10
[ $ok = 1 ] || { echo "E2E FAIL: nessun frame ricevuto"; adb logcat -d | tail -40; exit 1; }
for i in $(seq 1 15); do adb logcat -d -s LBS:I | grep -q "frame displayed" && break; sleep 1; done
adb logcat -d -s LBS:I | grep -q "frame displayed" || { echo "E2E FAIL: la pagina non mostra i frame"; adb logcat -d | tail -40; exit 1; }
echo "la pagina mostra i frame: $(adb logcat -d -s LBS:I | grep 'frame displayed' | head -1)"
sleep 3
adb exec-out screencap -p > e2e_screen.png || true
SIZE=$(adb shell wm size | tail -1 | sed 's/.*: //')
W=${SIZE%x*}; H=${SIZE#*x}
echo "schermo $W x $H: tocco al centro"
adb shell input tap $((W/2)) $((H/2))
sleep 2
adb shell input swipe $((W/2)) $((H/2)) $((W/2+200)) $((H/2+50)) 400
sleep 2
if grep -q "INPUT.*'btn'" "$AGENT_LOG"; then
  echo "E2E PASS: il tocco è arrivato all'agente"; grep INPUT "$AGENT_LOG" | head -6; exit 0
fi
echo "E2E FAIL: nessun clic ricevuto dall'agente"; tail -20 "$AGENT_LOG"; adb logcat -d | tail -30; exit 1
