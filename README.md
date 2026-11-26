# LBS Labs Remote

Controllo remoto minimale di computer **nella stessa rete locale**, per macOS e Windows
in qualsiasi combinazione. È **la stessa app su tutti i PC**: ogni PC può essere controllato
e controllarne altri.

> ⚠️ **Nessuna autenticazione, nessuna crittografia** (scelta voluta). Chiunque sia nella stessa
> rete e conosca l'IP può collegarsi a un PC su cui gira l'agente. Usala solo su reti fidate.

---

## 0. Installazione semplice (consigliata)

Non serve installare Python: usa i pacchetti pronti.

### Mac — `LBS-Labs-Remote-macOS.dmg`
(App Universale: un solo file per tutti i Mac, nativa sia su chip Apple M1/M2/M3/M4 sia su Intel.)
1. Doppio clic sul file `.dmg`, poi trascina **LBS Labs Remote** sulla cartella **Applicazioni**.
2. Apri **Applicazioni** e fai doppio clic su **LBS Labs Remote**. La prima volta il Mac dice che non
   può verificare l'app (non viene dall'App Store): clicca *Fine*, poi vai in
    → **Impostazioni di Sistema** → **Privacy e sicurezza**, scorri in basso e clicca
   **Apri comunque** accanto a LBS Labs Remote. (Su macOS meno recenti: clic destro sull'app → *Apri*.)
3. Solo sul Mac **da controllare**: concedi *Registrazione schermo* e *Accessibilità* (vedi §5;
   l'icona nella barra dei menu ha le voci *Grant…* che aprono la pagina giusta), poi
   *Quit* e riapri LBS Labs Remote.

Dal primo avvio l'app resta **sempre attiva in background** e riparte da sola a ogni accensione
(avvio al login attivato automaticamente; si può disattivare dal menu dell'icona, *Start at login*).
Doppio clic sull'app mentre è già attiva = si apre la finestra di connessione.

### Windows — `LBS-Labs-Remote-Windows-Setup.exe`
1. Doppio clic sul file. Se compare *"Windows ha protetto il PC"*: **Ulteriori informazioni** →
   **Esegui comunque** (l'app non ha una firma digitale a pagamento).
2. Next → Install. Alla fine LBS Labs Remote è **già attivo in background** (icona LBS vicino
   all'orologio) e ripartirà da solo a ogni accensione. L'installer configura anche il firewall e,
   se mancasse, installa Microsoft Edge WebView2 (il motore usato dalla finestra).
3. Per controllare un altro PC: menu Start → **LBS Labs Remote**. Disinstallazione:
   *Impostazioni → App → LBS Labs Remote*.

**In pratica**: installata l'app su tutti i PC, sul computer di controllo basta aprire LBS Labs
Remote, scrivere l'indirizzo IP (o scegliere il PC dall'elenco) e premere Invio.

### Android (telefoni e tablet) — `LBS-Labs-Remote-Android.apk`
Sui tablet l'app è un **viewer**: serve a controllare Mac e Windows (iOS e Android non permettono a
un'app di essere controllata dall'esterno).
1. Scarica il file `.apk` dal tablet (browser o app GitHub) e aprilo.
2. Android chiede di consentire l'installazione da quella app (*Installa app sconosciute*): consenti.
   Se compare un avviso di Play Protect, scegli *Installa comunque*.
3. Apri **LBS Labs Remote**, scrivi l'indirizzo IP del computer (o scegli un PC dall'elenco) e tocca
   **CONNECT**. Le versioni nuove si installano sopra le vecchie, senza disinstallare.

### iPad e iPhone — `LBS-Labs-Remote-iPad.ipa`
Apple non permette di installare app fuori dall'App Store senza una firma. Il file `.ipa` è **non
firmato**: va firmato al momento dell'installazione con un programma gratuito, usando il tuo ID Apple.
- **Sideloadly** (Mac e Windows, <https://sideloadly.io>): collega l'iPad al computer con il cavo,
  trascina il file `.ipa` nella finestra, inserisci il tuo ID Apple e premi *Start*. Poi sull'iPad:
  *Impostazioni → Generali → VPN e gestione dispositivo* → tocca il tuo ID Apple → **Autorizza**.
- **AltStore** (<https://altstore.io>): installa AltServer sul computer, poi AltStore sull'iPad e
  apri il `.ipa` da lì.

Limiti dell'ID Apple gratuito: l'app **scade dopo 7 giorni** (va reinstallata con lo stesso
programma, che può farlo da solo se il computer è acceso sulla stessa rete) e si possono avere al
massimo 3 app così installate. Con l'**Apple Developer Program** (99 $/anno) l'app dura un anno e si
distribuisce con TestFlight: se ti interessa, lo si può configurare nella build automatica.
La prima volta che ti colleghi, iPadOS chiede il permesso **Rete locale**: tocca *Consenti*.
Su iPad la ricerca automatica dei computer non è disponibile (Apple richiede un permesso speciale):
si scrive l'indirizzo IP, che resta salvato per le volte successive.

### Usare il tablet
- **Tocco** = clic · **doppio tocco** = doppio clic · **trascinare** = trascinamento (fader, selezioni)
- **Tocco lungo** o **tocco con due dita** = clic destro · **due dita che scorrono** = rotella
- **KEYBOARD** apre la tastiera a schermo con una barra di tasti speciali (Esc, Tab, Ctrl, Alt, Shift,
  Win/Cmd, frecce). I modificatori valgono per un solo tasto: tocca *CTRL*, poi una lettera.
  Una tastiera fisica (Bluetooth o Smart Keyboard) funziona direttamente.
- **FULL SCREEN** nasconde le barre; **EXIT FULL SCREEN** (in alto a destra) le riporta.

### Come vengono creati i pacchetti
Il workflow `.github/workflows/build.yml` li costruisce automaticamente su GitHub Actions
(Mac Universale, Windows, Android e iPad) a ogni push sul ramo `main`; i file vengono pubblicati nella
pagina *Releases* del repository. In locale, sulla piattaforma di destinazione:
```bash
pip install -r requirements.txt pyinstaller
python packaging/build_icons.py
pyinstaller --noconfirm --clean packaging/lbs_labs_remote.spec
# macOS:   bash packaging/macos/make_dmg.sh LBS-Labs-Remote-macOS.dmg
# Windows: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\installer.iss
```

---

## 1. Installazione da sorgente (per sviluppatori)

Serve **Python 3.9 o successivo**. Copia la cartella `lbs-labs-remote` sul PC e installa le dipendenze.

### Windows
1. Installa Python da <https://www.python.org/downloads/>. Durante l'installazione spunta
   **"Add python.exe to PATH"** e lascia attivo **"tcl/tk and IDLE"** (serve per la finestra).
2. Apri il *Prompt dei comandi* nella cartella `lbs-labs-remote`:
   ```bat
   py -m pip install -r requirements.txt
   ```

### macOS
1. Installa Python da <https://www.python.org/downloads/> (include già Tk). Se usi Homebrew:
   ```bash
   brew install python
   ```
2. Dal *Terminale*, nella cartella `lbs-labs-remote`:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

(Facoltativo, su entrambi: crea prima un ambiente virtuale con `python -m venv .venv`.)

---

## 2. Uso

| Comando | Cosa fa |
|---|---|
| `python lbs_labs_remote.py` | Icona nella tray/menu bar (**questo PC diventa controllabile**) + finestra **Connetti** |
| `python lbs_labs_remote.py 192.168.1.50` | Come sopra e si connette subito a quel PC |
| `python lbs_labs_remote.py --agent` | **Solo agente**, nessuna finestra: è la modalità per il PC demo |
| `python lbs_labs_remote.py --viewer` | **Solo finestra Connetti**: questo PC *non* diventa controllabile |

Su Windows usa `py` al posto di `python`, oppure `pythonw` per non avere la finestra console.
Su macOS usa `python3`.

### Sul PC da controllare (PC demo)
Avvia `python lbs_labs_remote.py --agent`, oppure attiva l'**avvio automatico al login** (§4).
Compare un'icona nella tray (Windows) o nella menu bar (macOS) con:
- lo stato: *Ready, listening on port 5970* oppure *Controlled from 192.168.1.20*;
- gli **indirizzi IP** del PC (utili se l'auto-discovery non lo trova);
- **Connect to a remote computer…** (su Windows basta un doppio clic sull'icona);
- **Start at login** (casella);
- **Quit**.

L'icona è il marchio LBS con un LED di stato: verde = pronto, ambra = qualcuno sta controllando
questo computer, arancio = permessi macOS mancanti, rosso = errore (es. porta occupata).
Quando qualcuno si collega o si scollega compare una notifica sul PC controllato.
Serve solo per trasparenza, non è un controllo di accesso.

### Sul PC da cui controlli
Avvia `python lbs_labs_remote.py` (o `--viewer` se non vuoi che anche questo PC sia controllabile).
Compare **una sola finestra**, nello stile grafico LBS: campo IP (precompilato con l'ultimo IP
usato con successo) e pulsante **CONNECT**. Premi **Invio** o clicca *CONNECT*. In alto a destra
il chip *THIS COMPUTER: READY* conferma che anche questo PC è controllabile.

Se nella rete ci sono PC con l'agente attivo, sotto il campo appare l'elenco **"PC trovati in
rete"**, ad es. `DEMO-PC1 (192.168.1.50)`. Un clic sulla voce compila il campo e connette subito.
Il campo manuale funziona sempre, anche quando l'auto-discovery non trova nulla
(il broadcast non attraversa i router, quindi non funziona fra subnet diverse).
Il PC su cui stai lavorando non compare nell'elenco.

Puoi scrivere anche `IP:porta` (es. `192.168.1.50:6000`). *Impostazioni avanzate ▸*
(nascoste di default) contiene porta, qualità immagine, fotogrammi/s e larghezza massima.

Se l'app è già attiva (ad esempio perché avviata al login), lanciandola di nuovo si apre
solo la finestra di connessione.

---

## 3. Comportamento della finestra remota (focus, ESC, schermo intero)

- **Mentre la finestra del viewer ha il focus**, tutto quello che fai sopra l'immagine
  (movimento del mouse, click sinistro/destro/centrale, rotella, tasti) va al PC remoto e
  **non** al tuo.
- **Clicca fuori dalla finestra** (o passa a un'altra app con Alt+Tab / Cmd+Tab): la finestra perde
  il focus e torni a controllare il tuo PC. Non servono combinazioni di tasti speciali. Al momento
  della perdita del focus, i tasti e i pulsanti ancora premuti vengono rilasciati anche sul PC
  remoto, così nessun Ctrl/Shift resta "incollato".
- **Il clic che riattiva la finestra non viene inoltrato.** Serve solo a riprendere il controllo,
  così non sposti per sbaglio un fader. Dal clic successivo tutto passa al PC remoto.
- **ESC è riservato al viewer** e non viene mai inviato al PC remoto: in schermo intero
  riporta la finestra alla modalità normale.
- **Schermo intero**: pulsante *⛶ Schermo intero* nella barra in alto. In schermo intero la barra
  sparisce e l'intero schermo mostra il PC remoto; **ESC** per uscire.
- **Indicatore di stato** (a destra nella barra): `● Connesso · 4 ms` (latenza misurata),
  oppure `● Riconnessione…`.
- **Connessione persa**: il viewer ritenta da solo per circa 15 secondi. Se non riesce, torna alla
  schermata iniziale con il motivo.
- **Un solo client per volta**: se un secondo client si collega, prende il controllo e il primo
  torna alla schermata iniziale con il messaggio *"Il controllo è stato preso da un altro
  client"*. Così una connessione rimasta "appesa" non blocca mai l'accesso.
- I tasti vengono inoltrati così come arrivano, senza conversione Cmd↔Ctrl: da un Mac verso
  Windows, per copiare usa Ctrl+C.

---

## 4. Avvio automatico al login

### Il modo semplice (Windows e macOS)
Con i pacchetti pronti è **già attivo**: su Windows lo imposta l'installer, sul Mac l'app al primo
avvio. Si attiva/disattiva dal menu dell'icona (**Start at login**) oppure da riga di comando:
```bash
python lbs_labs_remote.py --install-autostart     # attiva
python lbs_labs_remote.py --uninstall-autostart   # disattiva
```
All'avvio automatico parte la modalità `--agent`: solo icona, nessuna finestra.

**Windows**: viene creato il valore `LBS Labs Remote` in
`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`. Il comando usa `pythonw.exe`,
quindi non apre console. Lo trovi anche in *Gestione attività > App di avvio*.

**macOS**: viene creato `~/Library/LaunchAgents/com.lbslabs.remote.agent.plist`. Se l'agente va in
crash, macOS lo riavvia da solo; se esci dal menu, resta chiuso fino al prossimo login.
Ha effetto dal login successivo. Per avviarlo subito senza riavviare la sessione:
```bash
launchctl load ~/Library/LaunchAgents/com.lbslabs.remote.agent.plist
```

> Se sposti la cartella `lbs-labs-remote` o ricrei l'ambiente virtuale, disattiva e riattiva
> l'avvio automatico: il percorso viene salvato al momento dell'attivazione.

### Alternativa manuale su Windows
`Win+R` → `shell:startup` → crea un collegamento con destinazione:
`"C:\percorso\pythonw.exe" "C:\percorso\lbs-labs-remote\lbs_labs_remote.py" --agent`

---

## 5. Permessi su macOS (da fare una volta sul Mac da controllare)

Per catturare lo schermo e muovere mouse e tastiera, macOS richiede due permessi:

| Permesso | Se manca |
|---|---|
| **Registrazione schermo** (*Screen Recording*) | lo schermo appare nero o con il solo sfondo |
| **Accessibilità** (*Accessibility*) | mouse e tastiera non hanno effetto |

L'agente controlla entrambi all'avvio. Se ne manca uno:
- macOS mostra la richiesta di sistema e aggiunge l'app all'elenco;
- l'icona nella menu bar diventa **arancione** e il menu offre *⚠ Concedi "…"*, che apre
  direttamente la pagina giusta delle Impostazioni;
- chi si collega vede un **avviso giallo** nel viewer con il permesso mancante.

### Passo-passo
1. Avvia l'agente una prima volta nel modo in cui lo userai (da Terminale **oppure** con l'avvio
   automatico al login). Il permesso va dato al programma che lo esegue:
   - avviato dal *Terminale* (o da iTerm): il permesso va a **Terminale**;
   - avviato al login (LaunchAgent): il permesso va a **Python**.
2. Apri  → **Impostazioni di Sistema** → **Privacy e sicurezza** → **Registrazione schermo**
   (su alcune versioni: *Registrazione schermo e audio di sistema*).
3. Attiva l'interruttore accanto a **Terminale** / **Python**. Se non è in elenco, clicca **+**,
   premi `Cmd+Shift+G`, incolla il percorso di Python e conferma. Per conoscere il percorso esatto:
   ```bash
   python3 -c "import sys, os; print(os.path.realpath(sys.executable))"
   ```
   (per Python di python.org è di solito
   `/Library/Frameworks/Python.framework/Versions/3.x/Resources/Python.app`).
4. Torna a **Privacy e sicurezza** → **Accessibilità** e ripeti il punto 3.
5. **Esci dall'agente e riavvialo**: macOS applica i nuovi permessi solo ai processi avviati dopo.
6. Verifica: l'icona torna **blu** e collegandoti vedi lo schermo e controlli il mouse.

Note:
- Da macOS 15 (Sequoia), il sistema può chiedere periodicamente di riconfermare la registrazione
  dello schermo, con un avviso che va accettato sul Mac stesso. Su un Mac demo non presidiato
  conviene verificarlo prima di lasciarlo da solo.
- Il **Mac che controlla** (solo viewer) non ha bisogno di permessi. Se però lanci l'app in modalità
  normale, l'agente parte e macOS chiede i permessi anche lì. Per evitarlo usa `--viewer`.

### Se il Mac mostra uno schermo grigio e l'avviso "permission missing"
Succede quando i permessi risultano attivi in Impostazioni di Sistema ma macOS non li considera più
validi (accade dopo un aggiornamento fatto con versioni precedenti alla 1.2.1, la cui firma cambiava
a ogni build). Dal menu dell'icona scegli **Reset permissions…** (compare solo se manca qualcosa),
consenti i due permessi quando macOS li chiede, poi **Quit** e riapri l'app. In alternativa, da
Terminale (con l'app chiusa):
```bash
tccutil reset ScreenCapture com.lbslabs.remote
tccutil reset Accessibility com.lbslabs.remote
```
Dalla 1.2.1 l'app è firmata con un'identità stabile (`packaging/macos/lbs-labs-codesign.p12`): i
permessi concessi restano validi anche dopo gli aggiornamenti. Il passaggio da una versione precedente
alla 1.2.1 richiede un'ultima volta questa procedura.

---

## 6. Rete e firewall

- Porte predefinite: **TCP 5970** (sessione) e **UDP 5901** (auto-discovery).
  Per cambiarle: `--port N --discovery-port M --save` sull'agente e *Impostazioni avanzate > Porta*
  sul viewer (oppure `IP:porta` nel campo).
- **Windows**: al primo avvio, Windows Defender Firewall chiede se consentire a Python l'accesso
  alla rete. Consenti almeno le reti **private**, sia sul PC controllato sia su quello che controlla
  (il viewer deve ricevere i broadcast UDP). Se la rete è classificata "Pubblica", passala a
  "Privata" o consenti anche quella.
- **macOS**: se il firewall è attivo, alla prima connessione compare "Consentire a Python di
  accettare connessioni in entrata?" → *Consenti*.
- La porta 5970 è scelta apposta per non entrare in conflitto con VNC e con la *Condivisione
  schermo* di macOS, che usano la 5900. Se un altro programma occupa comunque la porta, l'app lo
  segnala nella finestra di connessione e l'icona diventa rossa: in quel caso usa un'altra porta
  (`--port N --save` sull'agente, *Impostazioni avanzate > Porta* sul viewer).
- Le versioni 1.0.0 usavano la porta 5900: aggiorna l'app su **tutti** i computer.
---

## 7. Opzioni dell'agente

```text
python lbs_labs_remote.py --agent [opzioni]
  --port N            porta TCP (predefinita 5970)
  --discovery-port N  porta UDP degli annunci (5901)
  --fps N             fotogrammi al secondo (12)
  --quality N         qualità JPEG 10-95 (50, medio-bassa per privilegiare la fluidità)
  --max-width N       larghezza massima dei frame in px, 0 = originale (1920; su Retina riduce 2880 → 1920)
  --monitor N         schermo da catturare (1 = principale)
  --no-adaptive       qualità fissa (di default si adatta alla congestione)
  --no-discovery      non annunciare il PC in rete
  --no-notify         nessuna notifica alla connessione
  --no-tray           niente icona, esecuzione in console (Ctrl+C per uscire)
  --save              salva le opzioni in ~/.lbslabs-remote/server.json
  -v                  log dettagliato
```

Dal viewer, *Impostazioni avanzate* può chiedere all'agente una qualità, fps o larghezza diversa
solo per quella sessione.

**Qualità adattiva** (attiva di default): se l'invio dei frame rallenta perché la rete è satura,
l'agente abbassa la qualità JPEG e poi la risoluzione, e risale gradualmente quando il canale
torna libero. Se lo schermo resta fermo non invia nulla. Dopo mezzo secondo di immagine statica
manda un fotogramma a qualità piena, così il testo torna nitido.

File utili in `~/.lbslabs-remote/` (su Windows `C:\Users\<nome>\.lbslabs-remote\`):
`client.json` (ultimo IP e impostazioni del viewer), `server.json` (impostazioni dell'agente),
`agent.log` e `viewer.log` (log, da guardare in caso di problemi).

---

## 8. Limiti noti

- **Windows, finestre "come amministratore"**: Windows impedisce a un programma normale di inviare
  mouse e tastiera a finestre avviate con privilegi elevati. Il blocco riguarda anche i prompt UAC,
  che compaiono su un desktop protetto. Se il software audio gira come amministratore, avvia anche
  l'agente come amministratore.
- **Schermata di blocco / login**: l'agente gira nella sessione dell'utente, quindi non vede né
  controlla la schermata di blocco. Sul PC demo conviene disattivare blocco automatico,
  sospensione e salvaschermo con password.
- **Scorciatoie di sistema del PC locale**: Alt+Tab, Cmd+Tab, Ctrl+Alt+Canc, il tasto Windows
  e Cmd+Q le intercetta il sistema operativo locale prima del viewer. Non vengono inoltrate
  (o solo in parte).
- Il **puntatore del mouse remoto non è disegnato** nell'immagine: vedi il tuo puntatore locale,
  che sopra la finestra coincide con la posizione remota.
- Viene catturato **un solo schermo** (il principale, oppure quello scelto con `--monitor`).
- Layout di tastiera diversi fra i due PC (es. italiano ↔ US) possono dare caratteri diversi sui
  tasti di punteggiatura: i caratteri vengono inviati così come digitati.

---

## 9. Struttura del codice

```text
lbs_labs_remote.py        punto di ingresso unico (python lbs_labs_remote.py --help)
lbsremote/
  app.py                modalità (normale / --agent / --viewer), avvio del viewer come processo figlio
  protocol.py           protocollo TCP condiviso: framing, tipi di messaggio, eventi di input
  discovery.py          broadcast UDP: annunci (agente) e ascolto (viewer)
  server.py             agente: listener TCP, cattura mss → JPEG, qualità adattiva, sessione unica
  injector.py           iniezione mouse/tastiera con pynput (Quartz su macOS per doppio click/drag)
  server_main.py        avvio agente: impostazioni, log, tray o console
  tray.py               icona tray/menu bar (pystray) con stato e menu
  autostart.py          avvio al login (registro di Windows / LaunchAgent di macOS)
  viewer.py             finestra (pywebview) + server locale che fornisce pagina e frame
  ui/                   interfaccia web: index.html, app.css, app.js (input, focus, ESC), icons.js
  client.py             rete del viewer: connessione, riconnessione automatica, ultimo frame
  resources.py          percorsi di interfaccia e stile, lettura dei token di colore
  platform_utils.py     DPI su Windows, permessi e notifiche su macOS
  config.py             file JSON in ~/.lbslabs-remote/
LBS-Stile-Grafico/       stile grafico LBS Labs (token, CSS, font Barlow, logo, icone): l'interfaccia
                        usa direttamente questi file; vale per tutti i programmi LBS Labs
CLAUDE.md               istruzioni per chi lavora al progetto (compreso lo stile obbligatorio)
tests/test_protocol.py  test senza display: python -m unittest discover -s tests
packaging/              PyInstaller (.spec), icone, script DMG (macOS), installer Inno Setup (Windows)
packaging/mobile/       prepare_assets.py: copia interfaccia e stile LBS nelle app Android/iPad
android/                app Android (Java): codice di rete, WebView, Gradle, chiave di firma
ios/                    app iPad/iPhone (Swift): rete con socket POSIX, WKWebView, XcodeGen
tools/                  agente di prova (fake_agent.py) e script delle prove su emulatore/simulatore
.github/workflows/      build automatica di DMG e installer
```

### Protocollo (TCP)
Ogni messaggio è: **4 byte big-endian con la lunghezza del payload** + **1 byte di tipo** +
**payload**. Per i frame video il payload è direttamente il JPEG. Il byte di tipo permette di
far passare sullo stesso socket anche ping/pong, avvisi e comandi di input (JSON). Le coordinate
del mouse viaggiano come **frazione 0–1** dell'immagine remota, e l'agente le converte nelle
coordinate del proprio schermo. Così funzionano con qualsiasi risoluzione o DPI:
- su Retina, mss cattura in pixel fisici (es. 2880×1800) ma il mouse lavora in punti (1440×900);
- su Windows il processo è reso *DPI-aware*, quindi cattura e mouse usano gli stessi pixel
  fisici anche con scaling al 125–150%.

Dettagli completi in `lbsremote/protocol.py`.
