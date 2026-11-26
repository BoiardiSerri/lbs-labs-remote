# SpeakerNet · Design system "Graphite hardware"

Fonte: codice di SpeakerNet (Python 3 + PySide6 6.12, Qt Widgets). Percorsi relativi alla radice del progetto; `theme.py` = `speakernet/ui/theme.py`, `hardware.py` = `speakernet/ui/hardware.py`, ecc. Misure in **px logici a 96 dpi (scala 100%)**; Qt usa punti: px = pt × 96/72. Valori dedotti marcati `[STIMATO]` con il metodo. Dettagli completi (ogni costante e formula con file:riga) in `details/charts_chain_badges.md` (grafici, grafo della catena, badge) e `details/screens_cards_editors.md` (pagine, schede, editor, finestre), estratti dal codice e verificati a campione.

## 1. Sintesi

1. Tema scuro unico, superfici **grafite** (#26282c finestra, #303338 pannelli) con accento **ambra RDNet #f5a800**; testo sull'accento #1f1f1f.
2. Look **hardware/scheumorfico**: pannelli in rilievo con gradiente, filo di luce in alto, ombra a 2 strati, **4 viti** negli angoli e **rientranze trapezoidali** sui lati.
3. Elementi incassati (**display**) per grafici, meter, testate: più scuri in alto, ombra interna di 8 px, filo chiaro in basso.
4. Controlli a **pillola** con gradiente verticale; primario/selezionato = pillola ambra con bagliore; **mute** = pillola rossa con bagliore.
5. **Knob** vettoriali da 270° (Qt 225° → −45°), arco ambra con alone, corpo radiale in rilievo, tacca ambra chiaro; 64/52/40/30 px.
6. **Vumeter verticali a LED** (puntini 4 px, passo 7 px, 2 colonne) verde→giallo (−12 dB)→rosso (−3 dB); GR rossa dall'alto; barre orizzontali incassate.
7. Tipografia **Bahnschrift** (fallback Segoe UI); base 9 pt = 12 px; etichette, pulsanti, testate in **MAIUSCOLO spaziato** (DemiBold 600); cifre tabulari.
8. Griglia di **4 px**; raggi 6 (campi) / 10 (display) / 14 (pannelli) / altezza÷2 (pillole).
9. Palette **funzionali intoccabili**: 8 colori banda EQ, 4 categorie blocchi, 6 sezioni preset, 4 LED limiter; il colore non è mai l'unica informazione (sempre testo/numero).
10. Nessuna animazione di transizione: solo la balistica dei meter (33 ms, rilascio 30 dB/s, picco 1.2 s).

## 2. Token

Tutti i valori sono in `tokens.json` / `tokens.css` (generati da `tools/build_tokens.py` leggendo il tema dell'app). Struttura delle palette in `theme.py`: `RDNET` (righe 45-58, storica, fonte di accento e stati) → `GRAPHITE` (60-66, palette attiva = RDNET + superfici grafite) → `HARDWARE` (73-99, componenti disegnati) → `derive()` (126-160, derivati con mix/lighter/darker di Qt) → `tokens()` = `with_derived(GRAPHITE)` (163-165, 184).

### 2.1 Colori

Profondità (dal più incassato al più in rilievo): `bg-0` #1b1d20 → `bg-topbar-top` #1a1c1f / `bg-display` #1d1f22 → `bg-field` = `bg-io-bar` #222428 → `bg-window` #26282c → `bg-panel-bottom` = `bg-alt` #2b2e33 → `bg-panel` = `bg-surface` #303338 → `bg-panel-top` #3a3d43.

| CSS `--color-…` | HEX | token app | sorgente | uso |
|---|---|---|---|---|
| `bg-0` | `#1b1d20` | `deep` | `theme.py:74` | incassi: binario dei segmentati, chip, mute spento, binari meter |
| `bg-topbar-top` | `#1a1c1f` | `topbar_top` | `theme.py:95` | barra superiore, gradiente (alto) e QMenuBar |
| `bg-topbar-bottom` | `#212327` | `topbar_bottom` | `theme.py:95` | barra superiore, gradiente (basso) |
| `bg-display` | `#1d1f22` | `display` | `theme.py:81` | display incassati, grafici (alto), testate pannello, tooltip, header tabelle |
| `bg-display-bottom` | `#282b30` | `display_bottom` | `theme.py:82` | display/grafici (basso del gradiente) |
| `bg-field` | `#222428` | `field` | `theme.py:83` | campi di input |
| `bg-io-bar` | `#222428` | `io_bar` | `theme.py:96` | barra I/O in basso |
| `bg-window` | `#26282c` | `window` | `theme.py:62` | fondo finestra, rientranze dei pannelli |
| `bg-panel-bottom` | `#2b2e33` | `panel_bottom` | `theme.py:77` | pannello, fine gradiente |
| `bg-alt` | `#2b2e33` | `alt` | `theme.py:62` | righe alternate, tessere senza dati |
| `bg-panel` | `#303338` | `panel` | `theme.py:76` | pannello, corpo |
| `bg-surface` | `#303338` | `surface` | `theme.py:62` | liste/tabelle, popup combo, menu, fondo PlotWidget |
| `bg-panel-top` | `#3a3d43` | `panel_top` | `theme.py:75` | pannello, luce in alto (stop 0) |
| `bg-elevated` | `#2b2d31` | `elevated` | `theme.py:138` | hover pulsanti spin, etichette flottanti grafici |
| `edge-hi` | `#42454c` | `panel_edge_hi` | `theme.py:78` | filo chiaro in alto (pannelli) / in basso (incassi) |
| `edge-lo` | `#16181a` | `panel_edge_lo` | `theme.py:79` | bordo scuro dei pannelli e dei controlli |
| `edge-field-top` | `#131416` | `field_edge` | `theme.py:84` | bordo alto dei campi incassati |
| `border` | `#3b3e44` | `border` | `theme.py:63` | bordi neutri, griglia tabelle, separatori menu |
| `border-field` | `#464950` | `field_border` | `theme.py:133` | bordo campi in tabella (hover), popup combo |
| `border-field-hover` | `#a0a2a8` | `field_hover` | `theme.py:134` | bordo campo in hover |
| `divider` | `#33353a` | `divider` | `theme.py:140` | QFrame[divider] |
| `screw` | `#4c4f56` | `screw` | `theme.py:80` | testa delle viti (bordo del gradiente) |
| `text` | `#f1f1f1` | `text` | `theme.py:48` | testo primario (ereditato da RDNET in GRAPHITE) |
| `text-2` | `#c8c9cd` | `text_2` | `theme.py:85` | testo secondario, etichette maiuscole |
| `text-muted` | `#9a9ca3` | `muted` | `theme.py:63` | testo terziario, assi, unita', placeholder |
| `text-disabled` | `#62646b` | `text_dis` | `theme.py:86` | testo disabilitato |
| `accent` | `#f5a800` | `accent` | `theme.py:50` | ambra RDNet: selezione, focus, arco knob, primario |
| `accent-hover` | `#ffb81f` | `accent_hover` | `theme.py:50` | accento hover, tacca knob |
| `accent-top` | `#ffbd2e` | `accent_top` | `theme.py:92` | pillola primaria/checked, gradiente alto |
| `accent-bottom` | `#e09a00` | `accent_bottom` | `theme.py:92` | pillola primaria/checked, gradiente basso e bordo |
| `on-accent` | `#1f1f1f` | `accent_text` | `theme.py:50` | testo su accento |
| `selection` | `#f5a800` | `selection` | `theme.py:51` | selezione liste/menu |
| `on-selection` | `#1f1f1f` | `selection_text` | `theme.py:51` | testo su selezione |
| `button` | `#3a3d43` | `button` | `theme.py:64` | maniglie scrollbar, close-button hover |
| `button-disabled` | `#2c2f33` | `button_disabled` | `theme.py:65` | fondo controlli disabilitati, LED spento in tessera |
| `pill-top` | `#43464d` | `pill_top` | `theme.py:90` | pillola normale, gradiente alto |
| `pill-bottom` | `#33363b` | `pill_bottom` | `theme.py:90` | pillola normale, gradiente basso; pressed |
| `pill-hover-top` | `#4d5058` | `pill_hover_top` | `theme.py:91` | pillola hover alto; filo di luce; bordo alto |
| `pill-hover-bottom` | `#3b3e44` | `pill_hover_bottom` | `theme.py:91` | pillola hover basso |
| `button-text` | `#f1f1f1` | `button_text` | `theme.py:65` | testo dei pulsanti |
| `mute-top` | `#ff6b6b` | `mute_top` | `theme.py:93` | mute acceso, gradiente alto |
| `mute-bottom` | `#d94444` | `mute_bottom` | `theme.py:93` | mute acceso, gradiente basso e bordo |
| `knob-hi` | `#45484f` | `knob_hi` | `theme.py:87` | corpo knob, luce (stop 0 radiale) |
| `knob-lo` | `#1c1e21` | `knob_lo` | `theme.py:88` | corpo knob, ombra (stop 1 radiale) |
| `knob-track` | `#17191b` | `knob_track` | `theme.py:89` | binario dell'arco del knob |
| `slider-track` | `#8d9099` | `slider_track` | `theme.py:94` | binario slider; riflesso delle viti |
| `slider-thumb` | `#e8e8e8` | `slider_thumb` | `theme.py:94` | cursore slider, stop 0.4 |
| `led-off` | `#2c2f34` | `led_off` | `theme.py:97` | LED spenti dei vumeter verticali |
| `ink` | `#000000` | `ink` | `theme.py:98` | nero delle ombre (sempre con alpha) |
| `ok` | `#5cc76e` | `ok` | `theme.py:56` | stato ok, LED attivo, verde vumeter |
| `warn` | `#ff7a45` | `warn` | `theme.py:56` | stato warning |
| `error` | `#ff5c5c` | `error` | `theme.py:56` | errore, rosso vumeter, GR |
| `busy` | `#9fc3e6` | `busy` | `theme.py:56` | stato in corso / info |
| `control` | `#a0a2a8` | `control` | `theme.py:57` | bordi controlli Fusion, SumItem, LinkToggle |
| `flash` | `#4a3c12` | `flash` | `theme.py:57` | token presente, uso non trovato nei moduli ui [vedi Lacune] |
| `meter-yellow` | `#f5d000` | `meter_yellow` | `theme.py:69` | giallo vumeter; bordo 'pending' |
| `mute-fill` | `#4a2020` | `mute_fill` | `theme.py:70` | fondo tessera catena in mute |
| `plot-top` | `#1d1f22` | `plot_top` | `theme.py:142` | grafico, gradiente alto |
| `plot-bottom` | `#282b30` | `plot_bottom` | `theme.py:143` | grafico, gradiente basso; contorno nodi |
| `plot-frame` | `#3b3e44` | `plot_frame` | `theme.py:144` | cornice grafico |
| `grid-major` | `#4e5156` | `grid_major` | `theme.py:145` | griglia principale; tacche scala meter |
| `grid-minor` | `#32353b` | `grid_minor` | `theme.py:146` | griglia secondaria |
| `zero-line` | `#82848a` | `zero_line` | `theme.py:147` | linea 0 dB (1.2 px) |
| `lane` | `#282a2f` | `lane` | `theme.py:149` | corsia catena (non piu' usato: corsie = display) |
| `cable` | `#696b70` | `cable` | `theme.py:151` | cavi della catena |
| `cable-hot` | `#f1f1f1` | `cable_hot` | `theme.py:152` | cavo evidenziato |
| `info-bg` | `#2f363d` | `info_bg` | `theme.py:154` | banner info |
| `warn-bg` | `#3d2c27` | `warn_bg` | `theme.py:155` | banner warning |
| `meter-bg` | `#26292d` | `meter_bg` | `theme.py:157` | separatori segmenti barre orizzontali |
| `meter-tick` | `#26282c` | `meter_tick` | `theme.py:158` | tacche -12/-3 dB barre orizzontali |
| `shadow` | `#0d0d0f` | `shadow` | `theme.py:139` | ombre tessere catena (alpha 60/80) |
| `selected-row` | `#40351d` | `fills.selected_row` | `theme.py:379` | riga scelta barra laterale: mix(accent, display, 0.84) |
| `mute-text` | `#ffffff` | `literal` | `theme.py:483; hardware.py:304` | testo del mute acceso |
| `thumb-edge-left` | `#cfd2d8` | `literal` | `theme.py:380` | cursore slider stop 0 |
| `thumb-edge-right` | `#b6b9c0` | `literal` | `theme.py:381` | cursore slider stop 1 |

Trasparenze ricorrenti (`alpha(colore, N)` con N su 255, `theme.py:168-172`): ombre `ink` 70/90 (pannello), 90 (vite), 110→0 (ombra interna display), 120 (knob); bagliori 60 (pillole, `paint_led`), 70 (LED meter, chip, arco knob), 120 (arco knob in trascinamento); selezione tessera accent 45/90.

### 2.2 Palette funzionali (non modificare)

| gruppo | valori | sorgente | regola |
|---|---|---|---|
| Bande EQ 0-7 (8-15 ripetono, tratteggiate) | #3987e5 #d95926 #199e70 #c98500 #d55181 #2aa52a #9085e9 #e66767 | `plots.py:347-348`, `band_color` 361, `band_dashed` 365 | numero della banda sempre sul punto |
| Categorie blocchi | user #5cc76e · user_preset #9fc3e6 · preset #e8a655 · hardcoded #8a8c92 | `chain_view.py:78-79` | bordo tessera e legenda |
| Sezioni preset | N #129cff · C #ff36ff · 1 #1affd5 · 2 #ffd21f · 3 #ff681c · 4 #7dff4d | `section_badge.py:28-29` | testo sopra = `text_on()` nero/bianco per contrasto WCAG (33-49) |
| LED limiter 0-3 | GREY #8a8c92 · GREEN #5cc76e · YELLOW #f5d000 · RED #ff5c5c | `meters.py:32-33` | sempre col nome accanto |
| Inchiostri | INK_DARK #000000 · INK_LIGHT #ffffff | `section_badge.py:30` | |

### 2.3 Gradienti

| nome | definizione | sorgente |
|---|---|---|
| pannello disegnato | verticale: 0 `panel_top` · min(0.5, 40/altezza) `panel` · 1 `panel_bottom` | `hardware.py:90-93` |
| pannello QSS (card, dialog, tab pane) | verticale: 0 `panel_top` · 0.14 `panel` · 1 `panel_bottom` | `theme.py:371-372` |
| display | verticale: 0 e 0.45 `display` · 1 `display_bottom` | `hardware.py:179-182` |
| pillola / hover | `pill_top`→`pill_bottom` / `pill_hover_top`→`pill_hover_bottom` | `theme.py:373-374`, `hardware.py:308-309` |
| accento / hover | `accent_top`→`accent_bottom` / `accent_hover`→`accent` | `theme.py:375-376` |
| mute | `mute_top`→`mute_bottom` | `theme.py:377` |
| barra superiore | `topbar_top`→`topbar_bottom` | `theme.py:378` |
| cursore slider | orizzontale: 0 #cfd2d8 · 0.4 `slider_thumb` · 1 #b6b9c0 | `theme.py:380-381` |
| corpo knob | radiale, centro e fuoco (x+0.38w, y+0.32h), raggio 0.75w: 0 `knob_hi` (hover `pill_hover_top`) · 1 `knob_lo` | `hardware.py:660-665` |
| anello knob | conico da 90° (ore 12): 0 `panel_edge_hi` α200 · 0.5 `panel_edge_lo` α200 · 1 `panel_edge_hi` α200, tratto 1.2 | `hardware.py:667-673` |
| testa vite | radiale centro (−0.8,−0.8), raggio 3.84: 0 `slider_track` · 1 `screw` | `hardware.py:141-144` |
| zone meter | lungo la scala −60…0 dB: 0 `ok` · 0.775 `ok` · 0.8 `meter_yellow` · 0.925 `meter_yellow` · 0.95 `error` · 1 `error` | `meters.py:101-113` |
| tessera catena (senza sezione) | verticale: 0 fill.lighter(116) · 1 fill.darker(108) (QColor HSV) | `chain_view.py:759-763` |
| curva totale EQ (area) | verticale: 0 `text` α40 · a quota 0 dB `text` α4 · 1 `text` α40 | `plots.py:1037-1041` |

### 2.4 Spaziature, griglia, raggi, linee

| token | valore | sorgente |
|---|---|---|
| unità | `SPACE` = 4 px; usati 4, 8, 12, 16 (SPACE×1-4) | `theme.py:42` |
| raggi | S 6 · M 10 · L 14 | `theme.py:43` |
| pillola QPushButton | 13 (altezza 26 = 16 min + 2×4 padding + 2 bordo) | `theme.py:455-458` |
| compact/small | 10 | `theme.py:487-488, 510` |
| segmentato | esterno 14 · selezionato 11 · con `small` ogni segmento 10 (la regola `small` viene dopo e prevale) | `theme.py:498-510` |
| riga tabella | 26 (`ROW_HEIGHT`) | `theme.py:40` |
| tessera catena / grafico | 8 / 6 | `chain_view.py:75`, `plots.py:119` |
| linee | 1 px (fili, griglie, bordi); 1.2 zero dB; 1.6 bordo tessera; 2.4 tessera selezionata; 2 sottolineatura scheda; 3 banner (bordo sinistro) | vari, vedi componenti |

### 2.5 Ombre e bagliori

| elemento | definizione | sorgente |
|---|---|---|
| pannello | due copie della forma in `ink` α70 a dy +2 e α90 a dy +1, senza sfocatura; il corpo occupa altezza −3 px | `hardware.py:84-89` |
| display | ombra interna: gradiente `ink` α110→α0 sugli 8 px alti; contorno `panel_edge_hi` 1 px | `hardware.py:184-192` |
| vite | `ink` α90, cerchio r 3.0 a dy +0.6 | `hardware.py:139-140` |
| knob | `ink` α120, corpo traslato dy +2 e allargato 1 px per lato | `hardware.py:657-659` |
| bagliore pillola primaria/mute | rettangolo +2.5 px per lato, colore `top` α60, raggio r+2.5 | `hardware.py:311-314` |
| bagliore arco knob | tratto `accent` α70 (α120 in drag), spessore ring×2.4, estremità tonde | `hardware.py:649-653` |
| LED meter | alone colore α70, raggio d×0.95 | `meters.py:155-159` |
| tessera catena | `shadow` α60 dy 3, α80 dy 1.5; selezione `accent` α45 tratto 8 + α90 tratto 4.5 | `chain_view.py:748-757` |
| anello scheda unità selezionata | esterno `accent` α70 tratto 4, raggio 15; interno `accent` tratto 1.6, raggio 14 (errore: `error`) | `system_view.py:423-427` |

## 3. Tipografia

Famiglia `UI_FAMILIES` = Bahnschrift, Segoe UI, Inter, Noto Sans, DejaVu Sans (prima disponibile, `theme.py:203`, `pick_family` 256-258). Bahnschrift è un font di sistema Windows 10+ (variabile, DIN), licenza Microsoft: **non incluso** negli asset. Base = font dell'app Qt su Windows, 9 pt [ricavato a runtime, `QApplication.font()`]. Ruoli = base + scarto (`TYPE_SCALE` 205-218), minimo 6 pt (239); ruoli in `TYPE_CAPS` (220-221) → MAIUSCOLO + spaziatura percentuale Qt e peso DemiBold 600 (241-247); `readout` Light 300 (243-244). Numeri: `numeric_font` = ruolo + OpenType `tnum` (225-253). Interlinea: quella di default del font (nessun valore impostato) [vedi Lacune].

| ruolo | pt | px | peso | maiuscolo | spaziatura Qt | ≈ em (misurato) | uso | sorgente |
|---|---|---|---|---|---|---|---|---|
| `caption` | 7.5 | 10.0 | 400 | no | 100% |  | assi, unità, note, chip | `theme.py:206` |
| `body` | 9.0 | 12.0 | 400 | no | 100% |  | testo, campi, valori knob | `theme.py:207` |
| `label` | 9.0 | 12.0 | 400 | no | 100% |  | etichette campi (muted) | `theme.py:208` |
| `value` | 9.5 | 12.67 | 700 | no | 100% |  | valori in evidenza | `theme.py:210` |
| `section` | 9.5 | 12.67 | 600 | sì | 112% | 0.0703 | titoli di sezione, voce corrente breadcrumb, radice albero | `theme.py:209` |
| `eyebrow` | 8.0 | 10.67 | 600 | sì | 116% | 0.0949 | etichette pannelli/knob/gruppi | `theme.py:213` |
| `button` | 8.5 | 11.33 | 600 | sì | 110% | 0.0555 | pulsanti, schede | `theme.py:216` |
| `heading` | 11.0 | 14.67 | 600 | sì | 114% | 0.0832 | testate pannelli, titoli schede, barra | `theme.py:214` |
| `title` | 13.0 | 17.33 | 700 | no | 100% |  | segnaposto grandi | `theme.py:211` |
| `page` | 13.0 | 17.33 | 600 | sì | 110% | 0.0569 | titolo pagina Unit e blocco | `theme.py:215` |
| `display` | 16.0 | 21.33 | 700 | no | 100% |  | anteprime valori nelle tessere | `theme.py:212` |
| `readout` | 28.0 | 37.33 | 300 | no | 100% |  | definito ma non usato da nessun widget (§8) | `theme.py:217` |

Spaziatura Qt in percentuale (100 = normale; 116 = +16% dell'avanzamento di ogni carattere); l'equivalente CSS in `em` è **misurato** con Bahnschrift su "A-Z 0-9" (`tools/build_tokens.py`, metrica `letter_spacing_em_measured`). Pulsanti e schede ricevono il ruolo `button` da `HardwareStyle.polish` (`theme.py:613-630`) se il widget non ha un font proprio. Marchio "SPEAKERNET" nella barra: ruolo heading con peso Normal 400 e spaziatura 132% (`main_window.py:1339-1344`). Etichette delle tessere della catena: font della scena, 8 pt grassetto (10.67 px), corsivo se duplicato (`chain_view.py:727-732`); testi sulla scena 7.5 pt (`SCREEN_FONT_PT`, 70).

## 4. Componenti

Stati: N = normale, H = hover, P = premuto, F = focus da tastiera, C = selezionato/acceso (checked), D = disabilitato. Render reali di ogni stato in `screenshots/components/` (widget veri dell'app; i file `*_simulated` applicano al widget le proprietà della regola `:hover`/`:pressed` di `theme.py` perché offscreen il mouse non si simula).

### 4.1 Pannello (`paint_panel`, `Panel`) — `hardware.py:47-128, 196-224`

Anatomia: ombra (2 strati) → corpo con gradiente e bordo `panel_edge_lo` 1 px → filo `panel_edge_hi` 1 px sul bordo alto interno (archi degli angoli alti + linea) → [testata] → [rientranze] → viti.

| proprietà | valore | riga |
|---|---|---|
| raggio | 14 (`RADIUS_L`) | 47 |
| corpo | rect inset 0.5 px, altezza −3 px con ombra | 84 |
| testata (`head`) | alta 38 (`HEAD_H`), fondo `display` ritagliato nella forma, linea `panel_edge_lo` sotto, titolo ruolo heading `text` a x+24, centrato in verticale | 31, 107-122 |
| viti | 4, centro a 10 px dai bordi (`SCREW_INSET`), raggio 2.4 (`SCREW_R`) + ombra | 29-30, 131-146 |
| rientranza | trapezio sul lato, da 34% a 66% dell'altezza, profonda 10 (`NOTCH_W`), smusso 14% dell'altezza della rientranza; riempita `window`, bordo `panel_edge_lo` | 32, 149-170 |
| margini contenuto (`Panel`) | 20 px laterali (con viti; 12 senza); sopra 48 con testata, 20 senza | 207-210 |
| cache | pixmap per misura/dpr/font (prestazioni) | 44-73 |
| card QSS + viti | `QFrame[card]` gradiente QSS, bordo `panel_edge_lo`, bordo alto `panel_edge_hi`, raggio 14; viti da `decorate()` (sovrapposte, trasparenti al mouse; margini laterali portati ad almeno 22) | `theme.py:407-414`, `hardware.py:240-281` |

Stati: nessuno. Varianti: con/senza viti, testata, rientranze sx/dx.

### 4.2 Display incassato (`paint_display`, `Display`) — `hardware.py:173-193, 227-237`

Raggio 10 (corsie della catena 10, gruppi uscite 8); contorno `panel_edge_hi` 1 px; gradiente display; ombra interna 8 px. Margini `Display`: 12/10/12/10. Usi: grafici (via `PlotWidget`), corsie della catena, gruppi uscite, meter, testate, chip.

### 4.3 Pulsanti

**QPushButton (foglio di stile, `theme.py:455-510`)** — altezza 26, padding 4×14, raggio 13, testo ruolo `button` (MAIUSCOLO 8.5 pt 600).

| stato | fondo | testo | bordo | riga |
|---|---|---|---|---|
| N | grad. pill | `button_text` #f1f1f1 | 1 px `panel_edge_lo`, alto `pill_hover_top` | 455-458 |
| H | grad. pill hover | = | = | 459 |
| P | `pill_bottom` piatto | = | alto `panel_edge_lo` | 460 |
| F | = | = | tutto `accent` | 461 |
| C | grad. accento | `accent_text` | `accent_bottom`, alto `accent_hover` | 462-465 |
| D | `button_disabled` | `text_dis` | `button_disabled` | 466-468 |
| primary N/H/D | grad. accento / grad. accento hover / come D | `accent_text` | come C | 469-476 |
| ghost N/H/C | trasparente | `muted` / `text` / `accent` | trasparente / `field_border` / `accent` | 489-493 |
| compact/small | padding 2×10, min 14 → alto 22, raggio 10 | | | 487-488, 510 |
| mute N/H/C | `deep` / = / grad. mute | `muted` / `text` / #ffffff | `panel_edge_lo` / = / `mute_bottom` (alto `mute_top`) | 477-485 |
| mute in attesa | | | 1 px **tratteggiato** `meter_yellow` | 486 |

Nota: il mute ha raggio 11 con padding 1×8 e min 16: alla sua altezza naturale (20 px) il raggio supera metà altezza e Qt disegna angoli vivi; nelle schede Unit è fissato a 84×22 (`unit_view.py:115-119`) [render: `button_mute_*_natural_size.png` vs `button_mute_*.png`].

**Segmentato** (`theme.py:498-510`): pulsanti affiancati con spaziatura 0, fondo e bordo 3 px `deep` (il bordo dello stesso colore fa sembrare il selezionato incassato), padding 2×14, min larghezza 48, esterni raggio 14; C: grad. accento, `accent_text`, raggio 11; H: testo `text`; D: `text_dis`.

**Pillola disegnata** (`paint_pill`, `hardware.py:287-334`) per schede e tessere: raggio = altezza/2; tipi `normal` (grad. pill o hover, filo `pill_hover_top` α200 a y+1), `primary`, `mute` (testo #ffffff), `off` (`deep`, testo `muted`), disabilitato (`button_disabled`/`text_dis`); bagliore per primary e mute; `pending` = bordo 1.2 px tratteggiato `meter_yellow`; testo ruolo button, −1 pt se l'altezza è < 20.

### 4.4 Interruttore a pillola (QCheckBox) — `theme.py:284-308, 431-436`

SVG 30×16: rettangolo 29×15 a (0.5, 0.5) raggio 7.5, pallino r 5 a cx 8 (off) / 22 (on), cy 8. Spaziatura dal testo 8.

| stato | binario | pallino | bordo |
|---|---|---|---|
| off | `deep` | `muted` | `field_edge` |
| on | `accent` | `accent_text` | `accent_bottom` |
| off D / on D | `button_disabled` | `text_dis` | `field_edge` / `accent_bottom` |

Checkbox negli alberi: quadrato 13×13 raggio 4, bordo `control`, fondo `field`; H bordo `accent`; C fondo `accent` + `assets/check.svg` (`theme.py:423-430`). Checkbox disegnata sulla scena (LinkToggle) 12×12 raggio 2.5: vedi `details/charts_chain_badges.md` §16.

### 4.5 Campi (QLineEdit, QComboBox, QAbstractSpinBox) — `theme.py:511-558`

Altezza 24 (min 18 + padding 2×2 + bordo 2), padding 2×6, raggio 6, fondo `field`; bordo `panel_edge_lo` con alto `field_edge` e basso `panel_edge_hi` (effetto incassato); selezione `selection`/`selection_text`.

| stato | bordo | fondo/testo |
|---|---|---|
| N | come sopra | `field` / `text` |
| H | `field_hover` #a0a2a8 | = |
| F | `accent` | = |
| D | `border` | trasparente / `text_dis` |
| in tabella | raggio 0, bordo trasparente; H `field_border`; F `accent` | |

Combo: padding destro 20, freccia `chevron_down` 10×10 in `muted` (disabilitata in `button_disabled`); elenco aperto fondo `surface`, bordo `field_border`. Spin: padding destro 18, pulsanti 16 px con bordo sinistro `border`, frecce 8×8, H fondo `elevated`; numeri allineati a destra, cifre tabulari, larghezza min 110 (`forms.py`) o 104/88 sotto un knob. **Trascinamento sui numeri** (DragSpinBox, `forms.py:89-156`): soglia 3 px; lineare 4 px per passo, log 120 px per raddoppio; Ctrl ×0.1, Shift ×10; clic senza trascinare = scrivere.

### 4.6 Slider orizzontale — `theme.py:559-572`

Binario alto 6, raggio 3, `slider_track` con bordo alto 1 px `muted`; parte riempita uguale al binario (nessun colore di riempimento). Cursore 12×18, raggio 4, grad. cursore, bordo `panel_edge_lo`; H bordo `accent_hover`; F `accent`; D binario `button_disabled`, cursore `text_dis`. Usato solo per i ritardi (`forms.py:230`, `SliderNumberEditor`).

### 4.7 Knob — `hardware.py:453-702` (+ editor `forms.py:273-324`, barra EQ `block_window.py:375-386`)

Geometria per diametro D (`size`): area (larghezza W) = max(D+16, 72 se c'è l'etichetta, larghezza etichetta+8); altezza = D + 8 + 16×righe (etichetta, valore). Quadrato del quadrante a x=(W−D)/2, y=4.

| parte | valore | riga |
|---|---|---|
| spessore anello `ring` | max(3, D×0.055) | 635 |
| cerchio dell'arco | quadrante rientrato di ring/2+1 | 636 |
| corpo | cerchio dell'arco rientrato di ring+3 | 637 |
| angoli (Qt: 0° = ore 3, positivi antiorari) | inizio 225° (in basso a sinistra), corsa 270° in senso orario fino a −45°. In CSS/canvas (0° = ore 3, orario): **da 135° a 405°** | 453, 641 |
| binario | `knob_track`, tratto ring, estremità tonde | 639-641 |
| arco valore | da 225° (unipolare) o da 90° (bipolare, ore 12) fino a 225°−270°×pos; `accent`, tratto ring, estremità tonde; disegnato se \|Δ\| > 0.3° | 643-655 |
| alone arco | `accent` α70 (α120 in drag), tratto ring×2.4 | 649-653 |
| corpo | ombra (§2.5) + gradiente radiale + anello conico 1.2 px | 657-673 |
| tacca | da 0.45r a 0.82r del corpo, all'angolo del valore; `accent_hover`, tratto max(2, D×0.035), tonda | 675-681 |
| focus | ellisse tratteggiata (punti) a D+4, `accent` α160, 1 px | 683-685 |
| etichetta | ruolo eyebrow, `text_2` (D `text_dis`), centrata, riga di 16 a y = fondo quadrante + 4 | 687-693 |
| valore | ruolo body con cifre tabulari, `muted`; in drag `accent`; D `text_dis` | 697-701 |
| misure in uso | 64 (default) · 52 maschere (`KNOB_PX`) · 40 pannelli stretti (`KNOB_SMALL_PX`) · 30 barra EQ (`KNOB_BAR_PX`), gli ultimi tre senza valore (c'è il campo sotto/accanto) | `forms.py:278-279`, `block_window.py:57` |

| stato | differenza |
|---|---|
| H | luce del corpo `pill_hover_top` invece di `knob_hi` |
| P (drag) | alone arco α120, valore in `accent` |
| F | ellisse puntinata |
| D | arco e tacca `text_dis`, senza alone; testi `text_dis` |

Interazione: trascinamento **verticale** (su = aumenta), 220 px = corsa intera (`DRAG_PX`), Shift ×10 più fine; rotella 1% della corsa per scatto (Shift 0.2%); frecce ±1% (Shift 0.2%), PgUp/PgDn ±10%, Home/End; Invio o **doppio clic = scrivere il valore** (segnale `edit_requested`, il campo accanto prende il fuoco): **nessun reset al default**. Scala logaritmica per le frequenze (`log`), bipolare per i guadagni con minimo < 0 < massimo. Valori quantizzati al passo del campo (`forms.py:306-309`). Accessibilità: nome = etichetta, descrizione = valore, tooltip "Etichetta: valore". Nessuna filmstrip: tutto vettoriale.

### 4.8 Vumeter e LED — `meters.py`

| proprietà | valore | riga |
|---|---|---|
| scala livello | −60…0 dBFS; giallo da −12, rosso da −3 | 28-31 |
| scala GR | 0…24 dB, rossa, cresce dall'alto (verticale) o da destra (orizzontale) | 29, 214-226 |
| **verticale = LED** | diametro 4 (`LED_D`), distanza 3 (`LED_GAP`); 2 colonne se larghezza ≥ 10 (passo orizzontale d+2), altrimenti 1; d = min(4, (w−(col−1)×2)/col), min 1.5; righe = int((h+3)/(d+3)), distribuite su tutta l'altezza | 116-126 |
| LED spento / acceso | `led_off` / colore della zona al centro del LED (livello) o `error` (GR), con alone α70 r d×0.95 | 129-162 |
| picco | il LED del picco resta acceso | 140, 150 |
| orizzontale | binario `deep` raggio h/2; riempimento gradiente delle zone (GR `error` da destra); `segments`: linee `meter_bg` ogni 4 px; picco 2 px; tacche −12/−3 dB in `meter_tick` | 194-263 |
| LED singolo (`paint_led`) | alone colore α60 r+2, disco con bordo `border` 1 px; r 5 default (3 schede unità, 4 Unit, 4.5 tessere, 6 pannello blocco) | 266-276 |
| balistica | passo 33 ms (~30 fps, timer attivo solo se qualcosa si muove); attacco immediato; rilascio 30 dB/s; picco fermo 1.2 s poi 18 dB/s; dt max 0.2 s | 36-39, 73-99, 279-306 |
| testo valore | "—" senza dati; livello "-inf" ≤ −60 altrimenti 1 decimale; GR 1 decimale; cifre tabulari; GR attiva (> 0.05) in `error` | 64-69 |
| pannello meter del blocco (`MeterPanel`) | alto 168, colonne 112, barra 14, scala a sinistra (tacche `grid_major`, numeri caption `muted`), su display r 10; LED stato limiter con nome | 316-429 |

### 4.9 Chip di stato — `hardware.py:337-397`, `system_view.py:230-240`

Pillola `deep` raggio h/2, alta 22 (schede) o 24 (barra superiore, `StatusChip`); LED a x+12: alone α70 r 6, disco r 3.5; testo caption `text_2` da x+22, elisione a destra con "…" (testo intero nel tooltip). Colori di stato: OK `ok`, WARN `warn`, ERROR `error`, BUSY `busy`, IDLE `muted` (`theme.py:175-181`). Larghezza = testo + 32/34, minimo 64 nella barra.

### 4.10 Schede, tabelle, alberi, menu, tooltip, banner, scrollbar

| componente | specifica | riga theme.py |
|---|---|---|
| schede (QTabBar) | testo `muted` ruolo button, padding 6×14, sottolineatura 2 px trasparente; selezionata `text` + 2 px `accent`; H `text`; pannello sotto = grad. QSS, raggio 14; chiusura `assets/close.svg`, H fondo `button` raggio 3 | 582-593 |
| schede di sezione (finestra blocchi) | riempite col colore della sezione, angoli alti 6, testo `text_on()`, sottolineatura 3 px d'inchiostro se selezionata | `block_window.py:162-183` |
| tabelle/liste | fondo `surface`, righe alterne `alt`, bordo `panel_edge_lo` raggio 10, riga 26, niente griglia; intestazione fondo `display`, `text_2` 600, padding 4×8, bordi `panel_edge_lo` sotto e `border` a destra; selezione `selection`/`selection_text` | 437-441, 450-454, 691-697 |
| barra laterale (albero) | fondo `display`, bordo `panel_edge_lo` (basso `panel_edge_hi`), raggio 10, padding 6×2; voce alta 24 raggio 6; selezione `selected_row` #40351d testo `accent_hover`; rientro 14; LED di stato 8 px | 442-449, `navigation.py:164-169` |
| menu | fondo `surface`, bordo `panel_edge_lo`, padding 4; voce 4/24/4/12 raggio 6; selezionata `selection`; D `text_dis`; separatore 1 px `border`, margine 4×8 | 601-606 |
| barra dei menu | trasparente nella barra superiore; voce 4×8; selezionata `selection` raggio 6 | 597-600 |
| tooltip | fondo `display`, testo `text`, bordo 1 px `border`, padding 4 | 608 |
| banner info / warning | testo `busy`/`warn`, fondo `info_bg`/`warn_bg`, bordo sinistro 3 px del colore, raggio 6, padding 4×8 | 399-406 |
| scrollbar | 10 px, fondo trasparente; maniglia `button` raggio 4 margine 2 min 24; H `pill_hover_top`; niente frecce | 573-581 |
| titolo di sezione | ruolo section (MAIUSCOLO), `text_2`, padding 12 sopra 4 sotto | 387, 700-704 |
| separatore | `QFrame[divider]` 1 px `divider` | 420 |

### 4.11 Dialog e popup — `theme.py:385, 613-630`

Ogni QDialog (anche QMessageBox, QInputDialog) ha fondo grad. QSS e le 4 viti di `decorate`; margini laterali portati ad almeno 22 px; contenuto con margini/spaziature Qt di default (non impostati). Pulsanti come §4.3. Menu contestuali come §4.10.

### 4.12 Grafici — `plots.py`, `dynamics.py`, `drex.py`, `multiband.py`

Base `PlotWidget` (`plots.py:39-207`): margini 40 (sx; dx 40 se scala a destra, altrimenti 12) / 10 sopra / 22 sotto; fondo widget `surface`; area con gradiente `plot_top`→`plot_bottom` raggio 6; griglia secondaria `grid_minor` e principale `grid_major` 1 px (allineate al mezzo pixel); linea 0 dB `zero_line` 1.2; etichette assi caption `muted`; cornice `plot_frame` 1 px (con fuoco: `accent` α170); serie `accent` 1.5 con area `accent` α46.

Editor EQ (`plots.py:436-1285`): asse X logaritmico 20 Hz–20 kHz, linee principali 100/1k/10k; scala Y automatica max(18, …) fino a 36 dB o fissa ±6/12/18/24; curve di banda: area α64 (banda attiva) / α30 / α14 (attenuata), linea 2.0 / 1.2, tratteggiata per le bande 8-15; curva totale `text` 2.2 con aloni α22 tratto 7 e α46 tratto 4; punti banda r 9 colore banda, contorno `plot_bottom` 1.5, numero `text_on`; selezionato: alone α70 r 16 + anello `text` 2.0 r 12; hover anello `text` α150 r 12; bande spente: cerchi r 6.5 sullo 0 dB; maniglie Q a rombo r 5; etichetta del valore su fondo `elevated` α238 bordo colore banda α220. Interazione completa in `details/charts_chain_badges.md` §4.

Curve di compressione (`dynamics.py:56-257`, `multiband.py:245-398`), filtro di drive (`drex.py:118-248`), spettro FIR (`multiband.py:137-237`), taps FIR (`plots.py:210-229`): colori e misure in `details/screens_cards_editors.md` §7-9.

### 4.13 Grafo della catena — `chain_view.py`

Tessera 120×80 raggio 8; fondo `surface` (dati) / `alt` (nessun dato) con gradiente lighter(116)→darker(108), oppure colore di sezione **pieno**; bordo colore categoria 1.6 (tratteggiato se duplicata dal DSP), selezionata `accent` 2.4 + alone; hover fondo lighter(125) (112 sulle sezioni); mute fondo `mute_fill` #4a2020 e LED `error`; icona 13 px a (8,6) tratto 1.4; etichetta 2 righe a (25,5) larga 77; LED a (108,12); angolo giallo 16 px per le modifiche offline; meter interni barre alte 6, righe ogni 11. Corsie = display r 10 con striscia di 4 px (colore della via o `control`); cavi `cable` 1.6 (o colore via α200), evidenziati `cable_hot` 2.2, angoli r 6, freccia 7×8. Costanti e formule di layout: `details/charts_chain_badges.md` §5-16.

### 4.14 Barra superiore — `main_window.py:1328-1363`, `navigation.py:105-152`

Fondo grad. barra superiore, linea inferiore 1 px `panel_edge_lo`, margini 12/8/12/8, spaziatura 8. Da sinistra: logo 32 px · "SPEAKERNET" (heading, peso 400, spaziatura 132%, `text_2`) · 12 · menu (File, Settings, View, Window, Help) · stretch 1 · navigazione ‹ posto › (pulsanti ghost larghi 34, testo heading +1.5 pt, mai troncato) stretch 2 · stretch 1 · 3 chip di stato (alti 24, si accorciano con "…"). Sotto, riga breadcrumb (margini 8/4/12/4): pulsante "◀" small, voci ghost separate da "›" `muted`, voce corrente ruolo section, suggerimento caption a destra.

### 4.15 Barra I/O (status bar) — `hardware.py:400-446`

Alta 32, fondo `io_bar`; linea 1 px `panel_edge_lo` a y 0 e `panel_edge_hi` a y 1; due fasce a righe oblique al 30% e al 70% della larghezza: parallelogramma largo 70 (vertici x+21 / x+70 in alto, x+49 / x in basso), righe `accent` α115 tratto 2 a 60°, passo 9 px. Messaggi e campi fissi della QStatusBar sopra, testo `text_2`, padding 0×8.

### 4.16 Schede delle unità e delle catene

Scheda unità (System, `system_view.py`): larga ≥ 300, alta 196, distanza 12; pannello con rientranza a sinistra; contenuto rientrato 22/9/22/13; titolo heading + chip a destra; riga info caption; striscia uscite (4 colonne) con gruppi su display r 8, etichetta eyebrow, per uscita LED livello 8 px + GR 5 px, LED limiter r 3 + "LIM", pillola mute alta 16; pulsanti 84×26 (Lock primario / Unlock / Bind to…) e Open 70×26. Selezionata: anello ambra; allarme: anello rosso; unità assente o virtuale: display con bordo tratteggiato `muted`; modifiche offline: triangolo `meter_yellow` 16 px nell'angolo. Scheda catena (Unit, `unit_view.py`): alta max(130, 120+28×righe), righe IN/OUT ogni 28 su display r 10, barre orizzontali alte 10, mute 84×22, "Open the chain ›" primario. Tutte le formule: `details/screens_cards_editors.md` §1-2.

### 4.17 Logo e icone

Logo `assets/logo_rcf.svg` (134×134 pt, bianco e nero) a 32 px nella barra e 64 px in Informazioni. Icone 16×16 monocromatiche in `currentColor`, tinte a runtime col token (`themed_icon`/`themed_svg`, `theme.py:268-328`): chevron_down, chevron_up (`muted`), crosshair (`muted`), plus, presets (`button_text`). Icone dei blocchi della catena disegnate come tracciati normalizzati (`chain_view.py:459-583`, coordinate in `details/charts_chain_badges.md` §10). Pallino di stato degli alberi: 8 px (`theme.py:677-688`).

## 5. Layout

Finestra principale 1480×860 di default (`main_window.py:238`), ridimensionabile, nessuna dimensione minima impostata; scala con il DPI del sistema (Qt high-DPI; disegno con device pixel ratio, cache per dpr). Struttura: barra superiore · breadcrumb · splitter [barra laterale 170-260 (iniziale 200) | pila delle pagine] · barra I/O.

```
+-- 1480 x 860 ----------------------------------------------------------------------+
| [logo32] SPEAKERNET [12] File Settings View Window Help   ‹ SYSTEM · 6 UNITS ›  (chip)(chip)(chip) |  12/8/12/8
| [◀] System › Stage-L › Chain C (2Way)                         Esc / Alt+← back …    |  8/4/12/4
+----------------+-------------------------------------------------------------------+
| SYSTEM         | Pagina (System | Unit | Chain)                                    |
| ● Stage-L      |                                                                   |
|   AB · 2Way    |                                                                   |
| 170..260 (200) |                                                                   |
+----------------+-------------------------------------------------------------------+
| messaggio …        ////             ////        Discovery from … | Local port …   | 32
+------------------------------------------------------------------------------------+
```

System (margini 12/12/12/0, spaziatura 8): barra strumenti (filtro ≤ 260, Sort, combo, "N selected", 4 pulsanti, ultimo primario) e griglia di schede: colonne = max(1, (larghezza−12)//312), larghezza scheda = (larghezza − 12×(colonne+1))/colonne, cella 208 alta.

```
| [Filter units…][8]Sort[Custom v] N selected ……… [ADD OFFLINE UNIT][LOCK SELECTED][UNLOCK SELECTED][LOCK ALL] |
| +-- scheda ≥300 x 196 ----------------+ 12 +-- … --+                       |
| | 22 STAGE-L               (● Locked) |                                   |
| |    192.168.1.31 · XPS 16K · fw 23   |                                   |
| |    [A B · 2WAY      ][C D · 2WAY   ]| strip alta (196−2)−22−78           |
| |    [UNLOCK 84x26]       [OPEN 70x26]|                                   |
```

Unit (margini 16/12/16/8): titolo pagina, chip, segmentato delle casse, "Outputs…", Lock; info; banner; schede catena in griglia a 2 colonne (spaziatura 16). Chain (margini 12/8/12/8): "DSP CHAIN", suggerimento, legenda 640×22, "Presets…"; grafo (adattato alla vista, zoom max 1.6). Finestra parametri 820×860: schede in alto, pannello con margini 12 e spaziatura 8: titolo pagina, dettaglio, sezione preset, banner, meter (168), card EQ (barra delle bande + grafico) e maschera in area scorrevole. Presets 1320×640. Schemi ASCII quotati di ogni schermata: `details/screens_cards_editors.md` (§1.6, 2.3, 2.4, 4, 5.3, 5.4, 10). Screenshot reali: `screenshots/screens/`.

## 6. Animazioni

Nessuna transizione animata: hover, pressione, focus, selezione cambiano lo stato all'istante (nessuna QPropertyAnimation nel codice). Animati solo i meter (§4.8) e l'inseguimento del punto di lavoro nei grafici di compressione (stessa balistica, `dynamics.py:260-285`); EQ dinamico: smorzamento 0.1 s (`block_window.py:64, 1072-1080`). Aggiornamento dati dell'interfaccia 25 Hz (40 ms, `config.py:84`).

## 7. Asset

Vedi `assets/MANIFEST.md`. 8 SVG (logo, check, close, 5 icone 16×16). Nessun PNG, nessun font incluso, nessuna filmstrip.

## 8. Incoerenze trovate (verifica §4 del compito)

| # | cosa | dove |
|---|---|---|
| 1 | `close.svg` ha il colore fisso #8a94a3, non presente nei token (le altre icone usano `currentColor`) | `speakernet/assets/close.svg` |
| 2 | due colori del cursore slider (#cfd2d8, #b6b9c0) e il bianco del mute (#ffffff) sono letterali nel foglio di stile/disegno, non token | `theme.py:380-381, 483`; `hardware.py:304` |
| 3 | pulsante mute QSS: raggio 11 > metà dell'altezza naturale (20) → angoli vivi se non viene forzato a 22 px | `theme.py:477-480` |
| 4 | token definiti ma non usati da nessun widget: `flash`, `lane`, `lane_label`, `card_border` (il grafo usa display al posto di `lane`); `divider` solo nella regola QSS; ruolo tipografico `readout` (28 pt Light) mai usato | `theme.py:57, 137, 149-150, 217` |
| 5 | contrasto: rosso `error` sul pannello 4.19:1 (sotto AA 4.5 per testo normale, scelta "A fedele"); testo disabilitato 2.15:1 (voluto); bianco sul mute in alto 2.78:1 / in basso 4.32:1 | calcolato, `tools/` |
| 6 | `[small]` sui segmentati annulla gli angoli 14 del gruppo (ogni segmento raggio 10) | `theme.py:502-510` |

## 9. Lacune

- **Interlinea**: non impostata in nessun punto; vale quella di Bahnschrift a ciascuna dimensione (Qt `QFontMetrics.height()`); nei CSS di riferimento `line-height` 1.35 [STIMATO, a occhio dai render].
- **Base 9 pt**: è il font dell'app di Qt su Windows (Segoe UI 9 pt di sistema), non scritta nel codice; su altri sistemi la base cambia.
- **Spaziatura lettere in em**: Qt usa una percentuale sull'avanzamento dei caratteri, non un valore fisso; gli `em` dei token sono misurati su "A-Z 0-9" e sono medie (le singole lettere variano).
- **Altezze di barra superiore, breadcrumb, header**: dipendono dalle metriche del font (barra ≥ 48 con il logo).
- **Margini dei dialog** e di alcune finestre: default dello stile Qt (Fusion), non impostati.
- **Hover/pressed dei widget a foglio di stile**: i PNG `*_simulated` applicano le proprietà della regola, non sono catture col mouse vero.
- **Tooltip**: il render è una replica della regola `QToolTip` (il tooltip vero non si cattura offscreen).
- **Scrollbar**: nei render di `reference.html` sono nascoste (Edge headless); la regola CSS è in `reference.html`.
- **Licenza Bahnschrift**: non ridistribuibile; su sistemi senza il font l'aspetto cambia (fallback Segoe UI/Inter).
- `BlockItem.warning` è memorizzato ma non ha resa grafica (`chain_view.py:899, 961`).
- **Radio button**: usato solo nelle righe dei preset ("default", `preset_window.py:153-157`); nessuna regola nel foglio di stile, quindi resta il disegno Fusion con la palette (`Highlight` = `accent`, bordi `control`). Non documentato oltre.
- **Pulsanti solo/icon-only dedicati**: non esistono nell'app (le icone stanno in pulsanti normali o ghost).
