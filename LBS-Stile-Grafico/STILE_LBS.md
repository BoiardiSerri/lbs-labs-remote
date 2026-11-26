# LBS Labs · Stile grafico "Graphite hardware"

Guida completa allo stile visivo dei programmi LBS Labs, ricavata da **Moviola**, il primo programma della famiglia. Serve a fare in modo che ogni nuovo programma, chiunque lo scriva (una persona, Claude o un altro assistente), abbia lo stesso aspetto e si comporti allo stesso modo.

**Come si usa:** questo file descrive *cosa* e *perché*; i valori esatti sono in `tokens/lbs-tokens.css` (o `tokens/lbs-tokens.json`); il codice pronto è in `css/` e `react/`; `anteprima.html` mostra tutto dal vivo. Se un valore qui e nei token non coincide, **vincono i token**.

Misure in **px logici a 96 dpi** (scala 100 %; sul Mac 1 px = 1 punto). Griglia di **4 px**.

---

## 1. L'idea in dieci righe

1. **Tema solo scuro**, superfici color **grafite** (finestra `#26282c`, pannelli `#303338`), un solo colore d'accento: **ambra `#f5a800`**, con testo quasi nero `#1f1f1f` sopra.
2. **Aspetto da apparecchio** (hardware): pannelli in rilievo con sfumatura verticale, filo di luce in alto, ombra netta a due strati e **4 viti** negli angoli.
3. Tutto ciò che si **legge** (liste, monitor, grafici, timeline, numeri, vumeter) sta in un **display incassato**: più scuro, con ombra interna in alto.
4. **Pulsanti a pillola** alti 26 px con sfumatura; il pulsante **principale** e gli stati **accesi** sono ambra con un leggero bagliore.
5. Font **Barlow Semi Condensed** (incluso, uguale su Mac e Windows). Etichette, pulsanti e intestazioni in **MAIUSCOLO spaziato**, semi-grassetto 600. Numeri a **cifre tabulari**.
6. **Raggi**: campi 6 · display 10 · pannelli 14 · pillole = metà dell'altezza.
7. **Nessuna animazione di transizione**: hover, clic e selezione cambiano lo stato all'istante. Si muovono solo i contenuti vivi (video, testina, vumeter, barre di avanzamento).
8. **Il colore non è mai l'unica informazione**: ogni stato ha anche un testo, un'icona o un numero (un chip è "LED + testo").
9. **Semplicità prima di tutto**: pochi pulsanti visibili, nomi chiari, frasi brevi, niente gergo tecnico se non serve.
10. Interfaccia **in italiano e in inglese**, con le stesse regole di maiuscolo.

---

## 2. Colori

Tutti i colori stanno in `tokens/lbs-tokens.css` come variabili `--color-…`. **Mai scrivere un colore esadecimale nel codice di un'interfaccia**: si usa sempre la variabile. Se un colore manca, si aggiunge un token (con nome e motivo), non un valore sparso.

Le trasparenze si ottengono dai token con `color-mix(in srgb, var(--token) N%, transparent)`, dove N% = alfa/255 (esempio: α70 = 27,5 %).

### 2.1 Superfici (dal più scuro al più chiaro)

| token | valore | uso |
|---|---|---|
| `--color-bg-topbar-top` | `#1a1c1f` | barra superiore, colore alto |
| `--color-bg-0` | `#1b1d20` | fondo "profondo": pillole dei chip, binari, interruttori spenti, segmentati |
| `--color-bg-display` | `#1d1f22` | display incassato (alto), testate dei pannelli, tooltip |
| `--color-bg-topbar-bottom` | `#212327` | barra superiore, colore basso |
| `--color-bg-field` | `#222428` | campi di testo e menu a tendina |
| `--color-bg-io-bar` | `#222428` | barra di stato in basso |
| `--color-bg-window` | `#26282c` | **fondo della finestra** |
| `--color-bg-display-bottom` | `#282b30` | display incassato (basso) |
| `--color-bg-elevated` | `#2b2d31` | hover delle righe, voce disabilitata attiva nei menu |
| `--color-bg-alt` / `--color-bg-panel-bottom` | `#2b2e33` | righe alterne; pannello (basso) |
| `--color-bg-panel` / `--color-bg-surface` | `#303338` | **pannello**; fondo dei menu |
| `--color-bg-panel-top` | `#3a3d43` | pannello (alto) |

### 2.2 Bordi e fili

| token | valore | uso |
|---|---|---|
| `--color-edge-lo` | `#16181a` | bordo scuro di pannelli, pulsanti, menu |
| `--color-edge-field-top` | `#131416` | bordo alto dei campi (effetto incassato) |
| `--color-edge-hi` | `#42454c` | filo di luce: alto dei pannelli, contorno dei display, basso dei campi |
| `--color-border` | `#3b3e44` | separatori, tooltip, campi disabilitati |
| `--color-border-field` | `#464950` | bordo al passaggio del mouse dei pulsanti "ghost" |
| `--color-border-field-hover` | `#a0a2a8` | bordo dei campi al passaggio del mouse |
| `--color-divider` | `#33353a` | linea divisoria sottile |
| `--color-screw` | `#4c4f56` | viti dei pannelli |

### 2.3 Testo

| token | valore | uso |
|---|---|---|
| `--color-text` | `#f1f1f1` | testo principale |
| `--color-text-2` | `#c8c9cd` | testo secondario: menu, intestazioni di lista, marchio |
| `--color-text-muted` | `#9a9ca3` | etichette, didascalie, segnaposto, scorciatoie |
| `--color-text-disabled` | `#62646b` | disabilitato (basso contrasto voluto) |

### 2.4 Accento e selezione

| token | valore | uso |
|---|---|---|
| `--color-accent` | `#f5a800` | **ambra**: pulsante principale, selezione, testina, focus |
| `--color-accent-hover` | `#ffb81f` | ambra al passaggio del mouse; nome della riga selezionata |
| `--color-accent-top` / `--color-accent-bottom` | `#ffbd2e` / `#e09a00` | sfumatura delle pillole ambra |
| `--color-on-accent` | `#1f1f1f` | testo e icone sopra l'ambra |
| `--color-selection` / `--color-on-selection` | `#f5a800` / `#1f1f1f` | voce attiva dei menu, selezione piena |
| `--color-selected-row` | `#40351d` | riga selezionata nelle liste lunghe (ambra scuro), con nome in `--color-accent-hover` |

### 2.5 Controlli

| token | valore | uso |
|---|---|---|
| `--color-pill-top` / `--color-pill-bottom` | `#43464d` / `#33363b` | pillola normale |
| `--color-pill-hover-top` / `-bottom` | `#4d5058` / `#3b3e44` | pillola al passaggio del mouse |
| `--color-button` | `#3a3d43` | maniglia delle barre di scorrimento, piccoli pulsanti |
| `--color-button-disabled` | `#2c2f33` | pillola disabilitata |
| `--color-button-text` | `#f1f1f1` | testo dei pulsanti |
| `--color-mute-top` / `--color-mute-bottom` | `#ff6b6b` / `#d94444` | pillola "MUTE" accesa (rossa) |
| `--color-mute-text` | `#ffffff` | testo sulla pillola rossa |
| `--color-slider-track` / `--color-slider-thumb` | `#8d9099` / `#e8e8e8` | cursori |
| `--color-knob-hi` / `-lo` / `-track` | `#45484f` / `#1c1e21` / `#17191b` | manopole |
| `--color-control` | `#a0a2a8` | bordi dei controlli generici |

### 2.6 Stati

| token | valore | significato |
|---|---|---|
| `--color-ok` | `#5cc76e` | tutto a posto, pronto, salvato |
| `--color-warn` | `#ff7a45` | attenzione, modifiche non salvate, avvisi |
| `--color-error` | `#ff5c5c` | errore, mancante, registrazione in corso |
| `--color-busy` | `#9fc3e6` | in lavorazione, informazione |
| `--color-text-muted` | `#9a9ca3` | inattivo |
| `--color-info-bg` / `--color-warn-bg` | `#2f363d` / `#3d2c27` | sfondo dei banner informativi / di avviso |
| `--color-meter-yellow` | `#f5d000` | zona gialla dei vumeter; bordo tratteggiato "in attesa" |
| `--color-led-off` | `#2c2f34` | LED spento |
| `--color-mute-fill` | `#4a2020` | fondo di un oggetto silenziato |
| `--color-flash` | `#4a3c12` | lampo di evidenza (ambra scuro) |

### 2.7 Grafici

| token | valore | uso |
|---|---|---|
| `--color-plot-top` / `--color-plot-bottom` | `#1d1f22` / `#282b30` | area del grafico |
| `--color-plot-frame` | `#3b3e44` | cornice |
| `--color-grid-major` / `--color-grid-minor` | `#4e5156` / `#32353b` | griglia |
| `--color-zero-line` | `#82848a` | linea dello zero |
| `--color-meter-bg` / `--color-meter-tick` | `#26292d` / `#26282c` | fondo e tacche dei meter orizzontali |
| `--color-cable` / `--color-cable-hot` | `#696b70` / `#f1f1f1` | collegamenti in uno schema |

### 2.8 Colori di categoria (da Moviola)

Per distinguere **tipi di oggetti** (in Moviola: video, foto, audio, musica, titoli in timeline). Toni desaturati e scuri: il testo `--color-text` si legge sopra (contrasto ≥ 4,5:1) e non si confondono con l'ambra né con i colori di stato. Si usano come sfumatura alto → basso, sempre con icona e nome.

| token | alto → basso | Moviola |
|---|---|---|
| `--lbs-cat-1-*` | `#3d5266` → `#2f4152` (blu ardesia) | video |
| `--lbs-cat-2-*` | `#3d5c5a` → `#2f4746` (verde acqua) | foto |
| `--lbs-cat-3-*` | `#3b5543` → `#2e4335` (verde bosco) | audio |
| `--lbs-cat-4-*` | `#4f4562` → `#3e364d` (viola) | musica |
| `--lbs-cat-5-*` | `#5c5040` → `#483e31` (bronzo) | titoli |

Trasparenze ricorrenti: `--lbs-wave` (forme d'onda), `--lbs-shade` (oscuramento e sfondo dei dialog), `--lbs-accent-range` (zona scelta su una scala), `--lbs-accent-mark` (tratti evidenziati).

### 2.9 Palette speciali (solo per programmi audio)

Nei token ci sono anche quattro palette nate per un programma audio: 8 colori di **banda EQ** (`--color-band-0…7`), 4 di **categoria blocchi** (`--color-category-*`), 6 di **sezione** (`--color-section-*`) e 4 **LED limiter** (`--color-limiter-0…3`). Si usano **solo** per quello scopo e mai per altro; un programma che non ne ha bisogno le ignora (Moviola non le usa).

### 2.10 Contrasto

- Testo normale sui display e sui pannelli: contrasto **≥ 4,5:1**.
- Il rosso `--color-error` sul pannello arriva a 4,2:1: va bene per LED, icone e testo grande o in grassetto; per frasi lunghe meglio il banner di avviso.
- Il testo disabilitato è volutamente poco contrastato (2,15:1).

---

## 3. Gradienti, ombre, bagliori

| token | definizione | dove |
|---|---|---|
| `--gradient-panel` | `panel-top` 0 → `panel` a 40 px → `panel-bottom` 100 % | corpo dei pannelli |
| `--gradient-panel-qss` | come sopra, con il secondo stop al 14 % | dialog e schede alte |
| `--gradient-display` | `display` fino al 45 % → `display-bottom` | display incassati |
| `--gradient-pill` / `--gradient-pill-hover` | `pill-top` → `pill-bottom` | pulsanti normali |
| `--gradient-accent` / `--gradient-accent-hover` | `accent-top` → `accent-bottom` | pulsanti principali, selezioni, barre di avanzamento |
| `--gradient-mute` | `mute-top` → `mute-bottom` | MUTE acceso |
| `--gradient-topbar` | `topbar-top` → `topbar-bottom` | barra superiore |
| `--gradient-thumb` | orizzontale chiaro | maniglia dei cursori |
| `--shadow-panel` | `0 2px 0 rgba(0,0,0,.275), 0 1px 0 rgba(0,0,0,.353)` | ombra **netta**, senza sfocatura, sotto pannelli e dialog |
| `--shadow-display-inset` | ombra interna sugli 8 px alti | display incassati |
| `--glow-accent` | `0 0 0 2.5px rgba(255,189,46,.235)` | bagliore delle pillole ambra e delle card scelte |

Regola: niente ombre morbide e sfocate "da sito web". Le ombre sono nette, come su un pannello di metallo.

---

## 4. Tipografia

### 4.1 Font

- **Barlow Semi Condensed** (licenza SIL Open Font, file in `font/`), pesi 300, 400, 600, 700. Va **incluso nel programma** e messo **primo** nella catena, su tutti i sistemi:
  `font-family: 'LBS Barlow Semi Condensed', "Bahnschrift", "Segoe UI", "Inter", "Noto Sans", "DejaVu Sans", sans-serif;` (variabile `--lbs-ui-font`).
- Bahnschrift (Windows) è solo una riserva: è il font su cui il design system è nato, Barlow è il suo equivalente libero e uguale ovunque.
- Interlinea: **1,35**. Testo con antialiasing (`-webkit-font-smoothing: antialiased`).
- I font scelti dall'utente per i suoi contenuti (per esempio i titoli di un video) non seguono il design system.

### 4.2 Ruoli tipografici

Ogni testo appartiene a un ruolo; nel CSS ci sono le classi `.t-<ruolo>`.

| ruolo | px | peso | MAIUSCOLO | spaziatura | uso |
|---|---|---|---|---|---|
| `caption` | 10 | 400 | no | — | didascalie, note, assi, chip |
| `body` | 12 | 400 | no | — | testo normale, campi, voci di menu |
| `label` | 12 | 400 | no | — | etichette dei campi (colore muted) |
| `value` | 12,67 | 700 | no | — | valori in evidenza |
| `section` | 12,67 | 600 | **sì** | 0,0703 em | titoli di sezione |
| `eyebrow` | 10,67 | 600 | **sì** | 0,0949 em | etichette sopra i campi, gruppi, intestazioni di lista |
| `button` | 11,33 | 600 | **sì** | 0,0555 em | pulsanti, schede, segmentati |
| `heading` | 14,67 | 600 | **sì** | 0,0832 em | testate dei pannelli e delle finestre |
| `title` | 17,33 | 700 | no | — | titoli grandi |
| `page` | 17,33 | 600 | **sì** | 0,0569 em | titolo di pagina |
| `display` | 21,33 | 700 | no | — | numeri grandi (il timecode di Moviola) |
| `readout` | 37,33 | 300 | no | — | numeri giganti (riservato) |

### 4.3 Regole

- **MAIUSCOLO solo** nei ruoli `section`, `eyebrow`, `button`, `heading`, `page`. Nomi di file, nomi di progetti e testi scritti dall'utente restano come sono.
- Dentro un ruolo maiuscolo, unità e sigle che hanno una forma propria non si alzano: `kHz`, `1080p`, `fps` (classe `.keep-case`).
- **Numeri** (tempi, durate, dB, contatori, dimensioni): sempre a cifre tabulari (`font-variant-numeric: tabular-nums`, classe `.num`), così non "ballano".
- Barra superiore più leggibile: in Moviola le voci del menu sono a 14 px e i chip a 12 px.
- Testi lunghi troncati con "…" (in mezzo per i percorsi dei file, così si vedono inizio e nome); il testo intero va nel tooltip.

---

## 5. Spazi, griglia, raggi, linee

| cosa | valore |
|---|---|
| unità | **4 px**; spazi usati 4 · 8 · 12 · 16 · 20 · 24 (`--space-1…6`) |
| raggi | campi e voci **6** (`--radius-s`) · display e card **10** (`--radius-m`) · pannelli **14** (`--radius-l`) |
| pillole | raggio = metà altezza: 26 → 13, 22 → 10/11; segmentato esterno 14, voce scelta 11 |
| riga di lista | **26** px |
| linee | 1 px per fili, griglie e bordi; 2 px per la testina e per la sottolineatura delle schede; 3 px per il bordo sinistro dei banner |
| margini della finestra | 12 px attorno ai pannelli; 8–12 px tra un pannello e l'altro |
| interno dei pannelli | 20 px (testo della testata a 24 px dal bordo esterno) |
| interno dei dialog | 22 px ai lati |

---

## 6. Componenti

Stati da prevedere sempre: **N** normale · **H** passaggio del mouse · **P** premuto · **F** focus da tastiera · **C** acceso/selezionato · **D** disabilitato. Il markup di ogni componente è in `anteprima.html`, lo stile in `css/lbs-components.css`, la versione React in `react/components.tsx`.

### 6.1 Pannello (`.ds-panel`)
- Fondo `--gradient-panel`, bordo 1 px `--color-edge-lo`, raggio 14, ombra `--shadow-panel` + filo interno in alto `--color-edge-hi`.
- **4 viti**: centro a 10 px dagli angoli, diametro 4,8 px, sfumatura radiale `slider-track → screw`, piccola ombra sotto.
- Testata facoltativa alta **38 px**, fondo `--color-bg-display`, linea sotto `--color-edge-lo`, titolo nel ruolo `heading`, elementi di comando a destra.
- Corpo con 20 px di margine (10 sopra se c'è la testata).
- **Rientranza** facoltativa su un lato: trapezio dal 34 % al 66 % dell'altezza, profondo 10 px (in Moviola tra il pannello Media e il monitor).
- Usato per: zone della finestra principale, dialog, finestre flottanti, schermata iniziale.

### 6.2 Display incassato (`.ds-display`)
- Fondo `--gradient-display`, bordo 1 px `--color-edge-hi`, raggio 10, ombra interna nera sugli 8 px alti.
- Contiene tutto ciò che si legge: liste, tabelle, monitor video, timeline, grafici, numeri, vumeter, riepiloghi.

### 6.3 Pulsanti a pillola (`.ds-btn`)

| variante | aspetto | quando |
|---|---|---|
| **normale** | sfumatura grigia, bordo `edge-lo` con il bordo alto più chiaro, testo `button` maiuscolo | azioni comuni, compreso **Annulla** |
| **principale** (`--primary`) | sfumatura ambra, testo `#1f1f1f`, bagliore `--glow-accent` | l'azione principale: **una sola per finestra** (Salva, Esporta, OK) |
| **acceso** (`.is-checked`) | come il principale, senza bagliore | interruttori a pulsante attivi (es. calamita, vista) |
| **ghost** (`--ghost`) | trasparente, testo muted; bordo `border-field` al passaggio | piccoli comandi di contorno, pulsanti icona nelle testate, chiudi banner |
| **mute** (`--mute`) | pillola scura alta 22; accesa: rossa con bagliore e testo bianco | silenziare (audio); in attesa: bordo tratteggiato giallo |
| **piccolo** (`--small`) | alto 22, raggio 10, padding 2×10 | barre degli strumenti fitte, piè di pannello |
| **solo icona** (`--icon`) | quadrato 26 (o 22) con icona 16 | sempre con tooltip che dice nome e scorciatoia |

- Alto **26**, padding 4×14, raggio 13; icona 16 px a sinistra del testo, spazio 6.
- Stati: H sfumatura più chiara · P fondo pieno `pill-bottom` · F bordo ambra · D fondo `button-disabled`, testo `text-disabled`.
- Nei dialog i pulsanti stanno **in basso a destra**, nell'ordine: [azione distruttiva o secondaria a sinistra, staccata] · Annulla · **Principale**. Invio = principale, Esc = Annulla.
- I pulsanti secondari dei dialog (per esempio **Non salvare**) hanno il **contorno come Annulla** (variante normale), non ghost: si riconoscono subito come pulsanti.
- Tooltip con nome e scorciatoia: "Dividi alla testina (S)".

### 6.4 Segmentato (`.ds-seg`)
- Gruppo su fondo `--color-bg-0`, raggio esterno 14; ogni voce alta 28, testo `button`, colore `text-2`.
- Voce scelta: pillola ambra (raggio 11) con testo scuro. Può mostrare un contatore (`VIDEO 2`).
- Per scegliere tra 2–5 opzioni che si escludono (filtri, formati, dimensioni). Variante piccola alta 26.

### 6.5 Interruttore (`.ds-toggle`)
- Pillola 30×16: spenta = fondo `bg-0` con pallino muted a sinistra; accesa = fondo ambra con pallino scuro a destra; disabilitata = grigio.
- Testo a destra, nel ruolo `body`. Si attiva con clic, Spazio o Invio.

### 6.6 Campi (`.ds-field`, `.ds-search`, `.ds-combo`)
- Alti **24**, fondo `--color-bg-field`, raggio 6, padding 2×6; bordo incassato (alto `edge-field-top`, basso `edge-hi`).
- H bordo `border-field-hover` · F bordo ambra · D trasparente con bordo `border`.
- Segnaposto in muted. Numeri allineati a destra con cifre tabulari.
- Ricerca: campo con la crocetta per svuotare a destra; Esc svuota.
- Menu a tendina (combo): come un campo, valore a sinistra, freccia 10 px muted a destra.
- L'etichetta sta **sopra** il campo, nel ruolo `eyebrow`, colore `text-2`, 12 px sopra e 4 sotto.

### 6.7 Cursore (`.ds-slider`)
- Binario alto 6 `slider-track`, maniglia 12×18 chiara con raggio 4; H/F bordo ambra.
- Per i valori continui non principali (volume, zoom). In Moviola lo zoom della timeline ha "–" e "+" ai lati.

### 6.8 Manopola (knob)
Per i parametri principali di programmi audio: 270° (da 135° a 405° in CSS/canvas), arco ambra con alone, tacca ambra chiaro, corpo in rilievo; misure 64 / 52 / 40 / 30. Trascinamento verticale (220 px = corsa intera, Shift più fine), doppio clic = scrivi il valore. Specifica completa: `riferimento-originale/DESIGN_SYSTEM.md` §4.7.

### 6.9 Chip di stato (`.ds-chip`)
- Pillola su `--color-bg-0`, alta 24 (26 nella barra superiore), raggio = metà altezza.
- **LED** a sinistra (pallino 7 px con alone 12 px al 27,5 %) del colore di stato + **testo** caption `text-2`, troncato con "…" (testo intero nel tooltip).
- Colori: ok verde · warn arancio · error rosso · busy azzurro · idle grigio.
- In Moviola, in alto a destra: `● PROXY PRONTI` · `● MODIFICHE NON SALVATE` · `● 1080p · 30 fps · 48 kHz`. Un chip può essere cliccabile (apre il dettaglio).

### 6.10 Banner (`.ds-banner`)
- Riga con bordo sinistro 3 px del colore, raggio 6, padding 4×8, alta almeno 28.
- **Info**: testo e bordo azzurro (`busy`) su `--color-info-bg`. **Avviso**: arancio (`warn`) su `--color-warn-bg`.
- Può avere pulsanti piccoli a destra e la crocetta (ghost) per chiuderlo. Si usa per spiegare una situazione dentro un pannello o un dialog, mai come finestra a sé.

### 6.11 Tooltip (`.ds-tooltip`)
- Fondo `--color-bg-display`, bordo 1 px `--color-border`, padding 4, testo `body`, larghezza massima 320.
- Compare su tutti i pulsanti icona e sui testi troncati; contiene nome + scorciatoia, oppure il testo intero.

### 6.12 Menu, barra dei menu, menu contestuale (`.ds-menu`, `.ds-menubar`)
- **Barra dei menu** dentro la barra superiore, a sinistra dopo il marchio: voci `File · Modifica · Effetti · Aiuto` (in Moviola), testo `text-2`, padding 4×10, raggio 6; menu aperto = fondo ambra, testo scuro.
- **Menu a discesa e contestuale**: fondo `--color-bg-surface`, bordo 1 px `edge-lo`, padding 4, larghezza minima 200, nessuna ombra morbida.
- Voce: altezza 24, padding 4 / 24 / 4 / 12, raggio 6, testo `body`; **scorciatoia a destra** in muted con cifre tabulari, nella forma del sistema (⌘ sul Mac, Ctrl su Windows).
- Voce attiva (mouse o frecce) = fondo ambra, testo e scorciatoia scuri. Disabilitata = `text-disabled` (attiva: fondo `bg-elevated`). Spunta a sinistra in uno spazio di 12 px.
- Separatore: linea 1 px `--color-border` con margine 4×8. Sottomenu con freccia `chevron_right`.
- Tastiera: frecce, Invio, Esc; lettere per saltare alla voce.

### 6.13 Liste e tabelle (`.ds-row`)
- Dentro un display: righe alte **26**, righe alterne `--color-bg-alt`, nessuna griglia.
- Intestazione: fondo `display`, testo `eyebrow` `text-2`, freccia d'ordinamento accanto alla colonna attiva.
- Selezione: nelle liste lunghe **ambra scuro** `--color-selected-row` con il nome in `accent-hover`; negli elenchi brevi dei dialog selezione piena ambra con testo scuro.
- **Gruppi richiudibili** (es. "REGISTRAZIONI", "VIDEO USATI" in Moviola): intestazione `eyebrow` con freccia, icona e contatore a destra.
- Miniature 16:9 con raggio 4; numeri (date, durate) allineati a destra con cifre tabulari.

### 6.14 Schede (tab)
- Testo `button` muted, padding 6×14, sottolineatura 2 px: trasparente, ambra se scelta (testo `text`). Pannello sotto con raggio 14.

### 6.15 Barre di scorrimento
- 10 px, fondo trasparente, maniglia `--color-button` raggio 4 con margine 2, altezza minima 24; H `pill-hover-top`. Nessuna freccia.

### 6.16 Dialog (`.ds-backdrop` + `.ds-panel.ds-dialog`)
- Sfondo della finestra oscurato con `--lbs-shade`; il dialog è un **pannello con viti** e testata (titolo `heading`), al centro.
- Corpo con 22 px ai lati; etichette `eyebrow` sopra i campi; pulsanti in basso a destra (§6.3).
- Larghezza fissa adatta al contenuto (Moviola: 360–600 px); i dialog con molti controlli si possono ridimensionare.
- Conferme **solo** quando un'azione non si può annullare (es. chiudere con modifiche non salvate). Tutto il resto si annulla con ⌘Z / Ctrl+Z senza chiedere.
- Durante un lavoro lungo il dialog mostra percentuale grande (ruolo `display`), barra di avanzamento, file corrente e il pulsante Annulla; alla fine "Mostra file".

### 6.17 Finestre flottanti
- Pannelli con viti senza cornice di sistema, con testata trascinabile (ruolo `heading`) e crocetta a destra: in Moviola anteprima, titolo, mixer, registrazione, riduzione rumore, coda dei proxy.
- Restano sopra la finestra principale ma si possono portare **anche su un altro monitor**; ricordano posizione e dimensione.
- Angoli ridimensionabili quando serve; corpo con padding 10 / 20 / 14.

### 6.18 Barra superiore (`.ds-topbar`)
- Alta **48**, fondo `--gradient-topbar`, linea sotto `edge-lo`, padding 8×12, spazi 8. Trascina la finestra.
- **Sinistra**: [Mac: 64 px per i tre pallini] · logo LBS 32 px · nome del programma (`heading`, peso 400, `text-2`) · barra dei menu.
- **Centro**: `‹ Nome documento * ›` (heading +2 px; bordo al passaggio del mouse, doppio clic per rinominare; l'asterisco = modifiche non salvate; le frecce passano tra documenti recenti).
- **Destra**: i chip di stato. Su Windows lasciare 150 px liberi per – ▢ ✕ (il riquadro dei pulsanti di sistema alto quanto la barra, cioè 48 × ingrandimento).

### 6.19 Barra di stato in basso (`.ds-iobar`)
- Alta **32**, fondo `--color-bg-io-bar`, linea 1 px `edge-lo` e sotto 1 px `edge-hi`.
- Due **fasce a righe oblique ambra** al 30 % e al 70 % della larghezza (parallelogramma largo 70 px, righe 2 px a 60°, passo 9 px, ambra al 45 %): è il segno distintivo dei programmi LBS. Codice nel componente `IoBar` e in `anteprima.html`.
- A sinistra l'ultimo messaggio ("Proxy pronto: …", "Progetto salvato"), a destra un dato fisso (in Moviola: "Durata 00:00:32:26"). Testo `text-2`.

### 6.20 Barra di avanzamento (`.ds-progress`)
Binario alto 14 raggio 7 su `bg-0` con bordo `edge-lo`; riempimento `--gradient-accent`. Con la percentuale scritta accanto.

### 6.21 Card di scelta (`.ds-card`)
Riquadro su display con bordo `border`, raggio 10; scelta: bordo ambra 2 px con bagliore. Per formati, preset e modelli (in Moviola: formati di progetto, preset di esportazione), con disegno, nome e una riga di spiegazione.

### 6.22 Vumeter
- Verticali: colonne di **LED** da 4 px distanziati 3 px (2 colonne se c'è spazio); verde sotto −12 dB, giallo fino a −3 dB, rosso sopra; LED spenti `--color-led-off`; alone del colore al 27,5 %.
- Orizzontali: binario scuro arrotondato con sfumatura delle zone.
- Movimento: aggiornamento ogni 33 ms, salita immediata, discesa 30 dB/s, picco fermo 1,2 s poi 18 dB/s.

### 6.23 Stati vuoti (`.ds-empty`)
Al centro della zona vuota: icona grande muted, una riga in `heading` muted ("TRASCINA QUI I TUOI VIDEO"), una riga `caption` che spiega, e il pulsante dell'azione (es. "+ IMPORTA"). Mai una zona vuota senza indicazioni.

### 6.24 Timeline e oggetti colorati (da Moviola)
- Tracce con intestazione a sinistra (sigla `eyebrow` + nome; pulsanti occhio/MUTE), corpo su display.
- Oggetti (clip) con la sfumatura del loro colore di categoria (§2.8), bordo `edge-lo`, raggio 6, nome in caption con icona; miniature o forma d'onda (`--lbs-wave`) dentro.
- Oggetto selezionato: bordo ambra. **Testina** 2 px ambra con la maniglia in alto. Righello con tempi a cifre tabulari in caption muted.

---

## 7. Disposizione delle finestre

### 7.1 Struttura tipo (Moviola)

```
+-- barra superiore 48 --------------------------------------------------------------+
| (LBS) MOVIOLA  File Modifica Effetti Aiuto      ‹ Nome progetto * ›   (●chip)(●chip)(●chip) |
+------------------------------------------------------------------------------------+
|  12 +-- pannello MEDIA ---------+ 8 +-- pannello MONITOR ------------------------+ 12 |
|     | [IMPORTA]                 |>  |   +-- display: video -----------------+   |    |
|     | (VIDEO 2|AUDIO|FOTO)      |   |   +-----------------------------------+   |    |
|     | [Cerca…] [Data ripresa v] |   |  |◀ ◀ ▶ ▶| ●REC     [ 00:00:32:26 ]       |    |
|     | display: lista media      |   +-------------------------------------------+    |
|     +---------------------------+                                                    |
|     +-- pannello TIMELINE --------------------------------------------------------+  |
|     | [TAGLIA][COPIA][INCOLLA][CANCELLA][DIVIDI] [DISSOLVENZA v] …   [MIXER] (U) –o+ |  |
|     | display: righello, tracce V3 V2 V1 A1 A2 A3, clip, testina                    |  |
|     +-----------------------------------------------------------------------------+  |
+-- barra di stato 32 ----------- //// ---------------------- //// --------------------+
| messaggio …                                                       Durata 00:00:32:26 |
+------------------------------------------------------------------------------------+
```

- Finestra di default 1480×900, minima 1180×720 (cresce con l'ingrandimento), ricorda posizione, misura e stato massimizzato.
- I divisori tra i pannelli si trascinano e la proporzione viene ricordata; i pannelli si possono nascondere (pulsante con icona `sidebar`).
- Schermata iniziale: pannello centrale 720×460 con logo grande, pulsanti "Nuovo" (principale) e "Apri", elenco dei recenti con miniatura.

### 7.2 Mac e Windows
- Stessa interfaccia sui due sistemi: stesso font (Barlow incluso), stessi colori, stessa barra superiore disegnata dal programma (niente barra del titolo di sistema).
- Mac: tre pallini della finestra in alto a sinistra (64 px riservati). Windows: – ▢ ✕ in alto a destra, nel colore della barra (150 px riservati).
- Scorciatoie: ⌘ sul Mac, Ctrl su Windows; nei testi si mostrano nella forma del sistema.
- **Dimensione di testi e finestre** nelle Preferenze: 100 · 115 · 125 · 140 · 160 %. Di base **125 % sul Mac** e **100 % su Windows** (Windows ingrandisce già con la scala dello schermo). Ingrandisce tutto in modo uniforme, finestre flottanti comprese.
- Tutto vettoriale o disegnato alla densità dello schermo: nitido su Retina e con la scala di Windows al 125/150 %.

---

## 8. Icone

- **16×16**, monocromatiche in `currentColor` (prendono il colore del testo), tratto **1,4 px** con terminali e giunzioni **tondi**; frecce e "+" a 2 px. Pieni solo dove serve (play, pausa, stop, REC).
- Disegno in `icone/*.svg` e in `react/icons.tsx` (43 icone): `plus`, `chevron_down/up/right`, `close`, `check`, trasporto (`play`, `pause`, `step_back`, `step_fwd`, `to_start`, `to_end`), modifica (`scissors`, `split`, `copy`, `paste`, `trash`), effetti (`fade`, `crossfade`, `kenburns`, `denoise`, `refresh`), `rec`, `stop`, strumenti (`magnet`, `mixer`, `title`, `sidebar`, `sort`, `scenes`, `folder`), tipi (`film`, `wave`, `photo`), `link`, `unlink`, `eye`, `eye_off`, `speaker`, `speaker_off`, `warning`, `in_point`, `out_point`.
- Le icone nuove si disegnano nello stesso stile, sulla stessa griglia di 16.
- Nei pulsanti: icona a sinistra del testo; da sole: pulsante icona con tooltip.
- REC: icona `rec` in rosso `--color-error`; durante la registrazione un chip o un'etichetta rossa con il tempo che scorre, senza effetti animati.

---

## 9. Marchio LBS

- Disco chiaro `#f1f1f1` con anello sottile e le lettere **L B S** nere, disegnate a tracciati (nessun font). File: `logo/lbs-logo.svg`, componente `react/Logo.tsx`.
- Misure: **32 px** nella barra superiore, **64 px** in "Informazioni" e nella schermata iniziale, grande e al 10–15 % di opacità come filigrana nei monitor vuoti.
- Accanto al logo: il nome del programma in maiuscolo (ruolo `heading`, peso 400, `text-2`).
- Icona dell'applicazione (`logo/lbs-icona-app.svg` / `.png`): quadrato arrotondato grafite con il marchio al centro e un filo ambra in basso. Per ogni nuovo programma si tiene la stessa base e si cambia al massimo il dettaglio in basso.

---

## 10. Comportamento

- **Niente animazioni** di passaggio: nessuna dissolvenza, scivolamento o rimbalzo. Gli stati cambiano subito.
- **Focus da tastiera** sempre visibile: bordo ambra (o anello ambra sottile). Tutto si usa anche da tastiera.
- **Tooltip** su ogni pulsante icona e su ogni testo troncato, con la scorciatoia.
- **Annulla senza limiti** (⌘Z / Ctrl+Z) al posto delle domande di conferma.
- **Messaggi** nella barra di stato in basso; problemi in un banner dentro la zona interessata; mai finestre di avviso a sorpresa.
- **Chip** per gli stati che durano (salvataggio, lavori in background, formato); un chip cliccabile apre il dettaglio.
- **Lavori lunghi** in background con avanzamento visibile e possibilità di pausa/annulla.
- **Salvataggio di recupero** automatico e domanda di recupero alla riapertura.
- Doppio clic su un nome = rinominare. Trascinare = spostare. Esc = annullare o chiudere.

## 11. Testi

- **Italiano semplice** (e inglese con le stesse regole): frasi brevi, verbi all'imperativo nei pulsanti ("ESPORTA", "IMPORTA", "SALVA").
- Spiegare con parole di tutti i giorni: "copie leggere" invece di "proxy" nelle spiegazioni (il termine tecnico può restare nei chip).
- Nei pulsanti dei dialog: Annulla / Cancel (non Undo); Undo / Annulla solo nel menu Modifica.
- Numeri e date nel formato della lingua: `25/11/2026`, `3,1 GB`, `00:00:32:26`.
- Stati vuoti e banner dicono sempre **cosa fare**, non solo cosa manca.

---

## 12. Checklist prima di consegnare una schermata

- [ ] Nessun colore, raggio, font o spazio fuori dai token (cerca `#[0-9a-f]{6}` nei sorgenti dell'interfaccia).
- [ ] Barlow Semi Condensed incluso e primo nella catena, su Mac e Windows.
- [ ] Maiuscolo solo nei ruoli `eyebrow / section / button / heading / page`; numeri a cifre tabulari.
- [ ] Pannelli con viti e sfumatura; tutto ciò che si legge su un display incassato.
- [ ] Un solo pulsante principale (ambra) per finestra; Annulla e i secondari con il contorno.
- [ ] Ogni stato colorato ha anche testo, icona o numero; contrasto del testo ≥ 4,5:1.
- [ ] Stati N / H / P / F / C / D presenti per ogni controllo; focus da tastiera visibile.
- [ ] Nessuna animazione di transizione.
- [ ] Barra superiore 48 con logo, menu, nome documento, chip; barra di stato 32 con le due fasce ambra.
- [ ] Tooltip su pulsanti icona e testi troncati; stati vuoti con indicazione e azione.
- [ ] Confronto affiancato con `anteprima.html` e con le schermate in `esempi/`, alla scala 100 %.
