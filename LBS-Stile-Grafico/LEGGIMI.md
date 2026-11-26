# LBS Labs · Stile grafico – LEGGIMI

Questa cartella contiene tutto lo stile grafico dei programmi LBS Labs: colori, font, misure, componenti, menu, icone e logo.
È ricavata da **Moviola** (versione 0.1, novembre 2026) e serve a dare lo **stesso aspetto** a ogni programma futuro.

## Cosa c'è dentro

| file / cartella | a cosa serve |
|---|---|
| `STILE_LBS.md` | **la guida completa**: idea generale, tutti i colori con l'uso, font e ruoli, misure, ogni componente, finestre, icone, logo, comportamento, testi, checklist |
| `ISTRUZIONI_PER_AI.md` | versione breve da dare a Claude o a un altro assistente all'inizio di un progetto (si può incollare nel file `CLAUDE.md` del nuovo progetto) |
| `anteprima.html` | **pagina da aprire nel browser**: mostra dal vivo palette, font, pulsanti, campi, chip, menu, dialog, liste, barre, icone |
| `tokens/lbs-tokens.css` | tutti i valori come variabili CSS (`--color-…`, `--font-…`, `--space-…`, `--radius-…`, gradienti, ombre) |
| `tokens/lbs-tokens.json` | gli stessi valori in JSON, per programmi non web (Python, Swift, C#, Figma…) |
| `css/lbs-base.css` | font incluso, ruoli tipografici (`.t-heading`, `.t-button`…), barre di scorrimento, regole di base |
| `css/lbs-components.css` | i componenti pronti (`.ds-panel`, `.ds-btn`, `.ds-chip`, `.ds-menu`, `.ds-topbar`, `.ds-dialog`…) |
| `react/` | i componenti React di Moviola (`components.tsx`, `icons.tsx`, `Logo.tsx`) da copiare in un progetto React |
| `font/` | Barlow Semi Condensed (4 pesi) con la licenza libera OFL: va incluso in ogni programma |
| `logo/` | marchio LBS in SVG e l'icona dell'applicazione (SVG e PNG 1024) |
| `icone/` | le 43 icone 16×16 in SVG |
| `esempi/` | schermate reali di Moviola, da usare come confronto |
| `riferimento-originale/` | il design system di partenza ("Graphite hardware") con tutti i dettagli: manopole, vumeter, grafici, schermate dei componenti |

## Come usarla con un nuovo programma

1. Copia la cartella `LBS-Stile-Grafico` dentro la cartella del nuovo progetto.
2. All'inizio del lavoro di' a Claude (o all'assistente che usi): *"Segui lo stile grafico in `LBS-Stile-Grafico/`: leggi `ISTRUZIONI_PER_AI.md` e `STILE_LBS.md`"*.
   In alternativa copia il contenuto di `ISTRUZIONI_PER_AI.md` nel file `CLAUDE.md` del progetto, così vale in ogni sessione.
3. Per un programma web o Electron basta collegare, in quest'ordine, `tokens/lbs-tokens.css`, `css/lbs-base.css`, `css/lbs-components.css`.
4. Per vedere com'è fatto un componente apri `anteprima.html` nel browser.

## Da sapere

- Il font **Barlow Semi Condensed** è libero (SIL Open Font License): si può includere e distribuire nei programmi, tenendo il file `font/OFL.txt`.
- Se cambi un colore o una misura, cambialo nei token e annota la modifica qui sotto, così tutti i programmi restano allineati.

## Modifiche

- 26/11/2026 – prima versione, ricavata da Moviola 0.1.
