#!/bin/bash
# Prova sul simulatore iPad: avvia l'app (che si collega a 127.0.0.1, dove gira l'agente di prova),
# controlla che arrivino i frame e che l'agente riceva il clic e il tasto di prova.
# Uso: tools/ios_e2e.sh LBSLabsRemote.app fake_agent.log
set -u
APP="$1"; AGENT_LOG="$2"
UDID=$(xcrun simctl list devices available | grep -E "iPad" | head -1 | grep -oE '[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}')
[ -n "$UDID" ] || { echo "nessun simulatore iPad"; xcrun simctl list devices available; exit 1; }
echo "simulatore iPad: $UDID"
xcrun simctl boot "$UDID" || true
xcrun simctl bootstatus "$UDID" -b | tail -2
xcrun simctl install "$UDID" "$APP" || exit 1
nohup xcrun simctl launch --console "$UDID" com.lbslabs.remote -LBSConnect 127.0.0.1 -LBSSelfTest 1 > ios_console.log 2>&1 &
for i in $(seq 1 60); do grep -q "first frame" ios_console.log && break; sleep 1; done
tail -15 ios_console.log
grep -q "first frame" ios_console.log || { echo "E2E FAIL: nessun frame ricevuto"; exit 1; }
for i in $(seq 1 15); do grep -q "frame displayed" ios_console.log && break; sleep 1; done
grep -q "frame displayed" ios_console.log || { echo "E2E FAIL: la pagina non mostra i frame"; tail -20 ios_console.log; exit 1; }
echo "la pagina mostra i frame: $(grep 'frame displayed' ios_console.log | head -1)"
sleep 2
xcrun simctl io "$UDID" screenshot ios_screen.png || true
if grep -q "INPUT.*'btn'" "$AGENT_LOG" && grep -q "INPUT.*'key'" "$AGENT_LOG"; then
  echo "E2E PASS: clic e tasto arrivati all'agente"; grep INPUT "$AGENT_LOG" | head -6; exit 0
fi
echo "E2E FAIL: l'agente non ha ricevuto l'input"; tail -20 "$AGENT_LOG"; exit 1
