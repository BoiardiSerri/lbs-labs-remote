# Asset di SpeakerNet

Copiati da `speakernet/assets/` senza modifiche. Proprietà di RCF S.p.A. (marchio e logo RCF: usarli solo in prodotti RCF).

| file | dimensioni | colori | uso nell'app | sorgente |
|---|---|---|---|---|
| `logo_rcf.svg` | viewBox 134×134 (width/height 134 pt), 1857 B | #FFFFFF, #000000 | icona finestre, barra superiore 32 px, Informazioni 64 px | `speakernet/ui/branding.py:10`, `main_window.py:68-69` |
| `check.svg` | 16×16, 215 B | #1f1f1f (tratto) | spunta delle checkbox degli alberi | `theme.py:103, 429` |
| `close.svg` | 16×16, 191 B | #8a94a3 fisso (fuori palette, vedi DESIGN_SYSTEM §8) | chiusura schede | `theme.py:102, 592` |
| `icons/chevron_down.svg` | 16×16, 225 B | `currentColor` | freccia combo/spin (10×10 e 8×8), tinta `muted` / `button_disabled` | `theme.py:362-365` |
| `icons/chevron_up.svg` | 16×16, 227 B | `currentColor` | freccia spin | `theme.py:362-365` |
| `icons/crosshair.svg` | 16×16, 295 B | `currentColor` | mirino del grafico EQ, tinta `muted` | `block_window.py` (BandBar) |
| `icons/plus.svg` | 16×16, 194 B | `currentColor` | "Add band", tinta `button_text` | `block_window.py` (BandBar) |
| `icons/presets.svg` | 16×16, 370 B | `currentColor` | pulsante "Presets…", tinta `button_text` | `main_window.py:285-290` |

Le icone `currentColor` vanno tinte col token indicato (`themed_icon`/`themed_svg`, `theme.py:268-328`).

**Font**: Bahnschrift (Microsoft, incluso in Windows 10/11, file `C:\Windows\Fonts\bahnschrift.ttf`, font variabile). **Non incluso**: la licenza Microsoft dei font di Windows non ne consente la ridistribuzione. Fallback dell'app: Segoe UI, Inter, Noto Sans, DejaVu Sans (`theme.py:203`). Inter (SIL OFL) è il sostituto libero più vicino per un progetto non Windows [scelta da verificare: metriche diverse].

**Filmstrip / PNG**: nessuno. Knob, meter, pannelli, viti, LED sono disegnati in codice.
