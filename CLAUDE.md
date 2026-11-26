# LBS Labs Remote – note per chi lavora al progetto

Controllo remoto in LAN (Mac/Windows). Stessa app su tutti i PC: agente (icona tray/menu bar,
`lbsremote/server.py`, `tray.py`) + finestra di connessione/visualizzazione (`lbsremote/viewer.py`,
interfaccia web in `lbsremote/ui/` mostrata con pywebview). Build automatica di DMG e installer
Windows con `.github/workflows/build.yml`, pubblicati nella pagina Releases.

- App per tablet: `android/` (Java) e `ios/` (Swift) mostrano la **stessa interfaccia web** (`lbsremote/ui/`,
  con `bridge.js` e `touch.js`) e implementano lo stesso "api" del desktop (`viewer.py`) con la logica di rete
  portata da `client.py`. I tablet sono solo viewer. `packaging/mobile/prepare_assets.py` copia interfaccia e
  stile LBS nelle app a ogni build (niente copie nel repository). Se cambi il protocollo (`protocol.py`) o
  l'`api` dell'interfaccia, aggiorna **tutte e tre** le implementazioni (Python, Java, Swift).
- `tools/fake_agent.py` è un agente di prova per le prove automatiche (emulatore Android, simulatore iPad).
- Il ramo `mobile` compila e prova tutto senza pubblicare; si pubblica solo da `main`.
- Interfaccia in **inglese** (testi visibili all'utente); commenti e documentazione in italiano.
- L'interfaccia usa direttamente `LBS-Stile-Grafico/tokens`, `css`, `font`, `logo`, `icone`
  (serviti dal server locale del viewer sotto `/lbs/`): non duplicare quei file.

## Stile grafico LBS Labs "Graphite hardware" (obbligatorio)

Questo programma segue lo stile grafico di LBS Labs, lo stesso di Moviola. Riferimenti nella cartella `LBS-Stile-Grafico/`:
`STILE_LBS.md` (regole e componenti), `tokens/lbs-tokens.css` / `lbs-tokens.json` (valori), `css/` (fogli di stile pronti),
`react/` (componenti React), `anteprima.html` (verità visiva: aprila nel browser), `esempi/` (schermate di Moviola),
`font/` (Barlow Semi Condensed da includere), `logo/`, `icone/`.

Regole:
- Usa SOLO i token di `lbs-tokens.css`. Nessun colore, raggio, font o spaziatura fuori dai token. Se manca un token, chiedi.
- Tema solo scuro. Finestra `--color-bg-window` #26282c, pannelli `--gradient-panel` (#3a3d43 → #303338 → #2b2e33),
  accento ambra `--color-accent` #f5a800 con testo #1f1f1f.
- Font **Barlow Semi Condensed** incluso nel programma e primo nella catena su Mac e Windows (`--lbs-ui-font`).
  Base 12 px, interlinea 1,35. Etichette, pulsanti, intestazioni in MAIUSCOLO spaziato, peso 600, nei ruoli
  eyebrow / section / button / heading / page. Numeri a cifre tabulari.
- Griglia 4 px. Raggi: campi 6, display 10, pannelli 14, pillole = metà altezza.
- Pannelli in rilievo: gradiente, bordo #16181a, filo #42454c in alto, ombra netta a 2 strati, 4 viti a 10 px dagli angoli.
- Liste, monitor, grafici, numeri e meter stanno in display incassati (gradiente scuro, ombra interna 8 px, contorno #42454c).
- Pulsanti a pillola alti 26 (piccoli 22): normale grigio; UN solo principale ambra con bagliore per finestra;
  Annulla e i secondari con il contorno (variante normale); ghost solo per comandi di contorno e icone.
- Chip di stato = LED colorato + testo (ok #5cc76e, warn #ff7a45, error #ff5c5c, busy #9fc3e6, idle #9a9ca3).
  Il colore non è mai l'unica informazione.
- Barra superiore alta 48: logo LBS 32 px + nome programma + menu a sinistra, "‹ Nome documento ›" al centro, chip a destra.
  Barra di stato alta 32 con le due fasce a righe oblique ambra al 30 % e 70 %.
- Menu: fondo #303338, voci alte 24 raggio 6, voce attiva ambra con testo scuro, scorciatoie a destra in grigio.
- Dialog = pannello con viti su sfondo oscurato; pulsanti in basso a destra: [secondario] · Annulla · Principale.
- Nessuna animazione di transizione: gli stati cambiano all'istante (si muovono solo video, testine, meter, avanzamenti).
- Interfaccia uguale su Mac e Windows; dimensione dell'interfaccia regolabile (100–160 %), di base 125 % Mac, 100 % Windows.
- Testi in italiano semplice (e inglese), frasi brevi; stati vuoti con indicazione e pulsante d'azione.

Checklist prima di consegnare una schermata: nessun HEX fuori dai token; Barlow incluso; maiuscolo solo nei ruoli giusti;
pannelli con viti; letture su display; un solo pulsante ambra; stati N/H/P/F/C/D; focus visibile; nessuna animazione;
confronto con `anteprima.html` ed `esempi/` alla scala 100 %.
