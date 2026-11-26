# SpeakerNet: views design-system extraction (read-only)

Root: `C:\Users\andrea.capra\Documents\CLAUDE\SpeakerNet-main\speakernet\ui\`
File abbreviations used in citations:
`sv`=system_view.py, `uv`=unit_view.py, `nav`=navigation.py, `mw`=main_window.py, `bw`=block_window.py,
`fm`=forms.py, `dy`=dynamics.py, `dx`=drex.py, `mb`=multiband.py, `pw`=preset_window.py, `th`=theme.py,
`hw`=hardware.py, `cfg`=../config.py, `pl`=plots.py.
Colours are token names: `t["x"]` = `tokens()["x"]` (th:187). `alpha(c, N)` = same colour with alpha N/255 (th:168-172).

## 0. Shared constants (from theme / config, referenced by these files)

| property | value | file:line |
|---|---|---|
| SPACE | 4 px | th:42 |
| RADIUS_S / RADIUS_M / RADIUS_L | 6 / 10 / 14 px | th:43 |
| ROW_HEIGHT | 26 | th:40 |
| STATUS_DOT_PX | 10 | th:41 |
| Font families (first available) | Bahnschrift, Segoe UI, Inter, Noto Sans, DejaVu Sans | th:203 |
| Type scale (delta pt vs app font, bold) | caption -1.5 / body 0 / label 0 / section +0.5 B / value +0.5 B / title +4 B / display +7 B / eyebrow -1 B / heading +2 B / page +4 B / button -0.5 B / readout +19 Light | th:205-218 |
| Caps roles + letter spacing % | eyebrow 116, heading 114, page 110, section 112, button 110 (AllUppercase; bold caps roles use DemiBold) | th:220-221, th:241-247 |
| ui_font fallback size / floor | base 9.0 pt if app font has none; min 6.0 pt | th:238-239 |
| numeric_font | ui_font + OpenType `tnum` | th:225-253 |
| Status -> token | IDLE "muted", BUSY "busy", OK "ok", WARN "warn", ERROR "error" | th:175-181 |
| status_icon | pixmap 20x20 device px, DPR 2.0 (10 logical), ellipse (2,2,16,16) device px, no pen, status colour | th:677-688 |
| primary(btn) | property primary=True (style from stylesheet) | th:652-655 |
| role(w,name) | property role=name; "eyebrow" also sets ui_font("eyebrow") | th:658-667 |
| card(w) | property card=True + hardware.decorate (screws) | th:670-674 |
| section_title(w) | objectName "sectionTitle", ui_font("section") | th:700-704 |
| GUI_REFRESH_HZ | 25 -> timers 1000/25 = 40 ms | cfg:84, mw:108, mw:349 |
| CHAIN_LINGER_S | 60.0 s | cfg:116 |
| hardware.LEFT / RIGHT notch ids | "left" / "right" | hw:33 |
| EQ_SCALES | (6.0, 12.0, 18.0, 24.0) | pl:235 |
| DYNAMIC_MIN_DB | 0.05 | pl:358 |

Painting helpers used but defined outside scope (geometry not extracted here): `paint_panel` hw:47, `paint_screws` hw:131, `paint_display` hw:173, `Panel` hw:196, `paint_pill` hw:287, `hardware.paint_chip` hw:337, `StatusChip` hw:360, `IoBar` hw:424, `Knob` hw:457, `MeterTimer` meters.py:279, `MeterPanel` meters.py:316, `band_color` pl:361, `paint_bar/paint_led/LIMITER_COLORS/GR/LEVEL` meters.py, `CATEGORY_COLORS/LEGEND` chain_view.py, `SECTION_COLORS/text_on` section_badge.py.

---

## 1. System page (level 1) — system_view.py

### 1.1 Constants
| property | value | file:line |
|---|---|---|
| CARD_MIN_W | 300 | sv:37 |
| CARD_H | 196 | sv:38 |
| GAP | 12 | sv:39 |
| LABEL_H (group label row) | 18 | sv:257 |
| MUTE_H (mute pill) | 16 | sv:258 |
| Offline corner size | 16 (default arg) | sv:247 |
| Chip height | 22 | sv:237 |
| Chip width | min(horizontalAdvance(label, ui_font("caption")) + 32, max_w); max_w default 220, on card = inner.width*0.55 | sv:235-236, sv:431-432 |

### 1.2 Card geometry (CardDelegate) — formulas; O = option.rect
| element | formula | file:line |
|---|---|---|
| sizeHint | (int(card_w), CARD_H=196) | sv:366-367 |
| card | O.adjusted(1,1,-1,-1) | sv:374-375 |
| inner_rect | card.adjusted(22, 9, -22, -13) (inside corner screws) | sv:261-263 |
| strip_rect | (inner.left, inner.top+44, inner.width, inner.height-44-34) | sv:266-269 |
| column width | col_w = strip.width/4 | sv:273, sv:298 |
| output_cell(i) | (strip.left + i*col_w + 6, strip.top + LABEL_H + 2 (=+20), col_w-12, strip.height - LABEL_H - 6 (=h-24)) | sv:272-275 |
| mute_rect | (cell.left, cell.bottom-16, cell.width, 16) | sv:278-279 |
| group box | (strip.left + base*col_w + 2, strip.top, col_w*ways - 4, strip.height) | sv:313-314 |
| group label | (box.left+8, box.top+2, box.width-16, 18), font eyebrow | sv:320-322 |
| meter_h | cell.height - MUTE_H - 4 | sv:328 |
| level bar (vertical) | (mx-9, cell.top, 8, meter_h), mx = cell.center.x | sv:329-330 |
| GR bar (vertical) | (mx+2, cell.top, 5, meter_h) | sv:331 |
| limiter LED | centre (mx+16, cell.top+5), radius 3 | sv:334 |
| LIM label rect | (mx+21, cell.top, cell.right+4-(mx+21), 11) | sv:335 |
| chip | right edge = inner.right, top = inner.top, h 22 | sv:431-432, sv:237 |
| title | (inner.left, inner.top, chip.left - inner.left - 8, 22), font heading | sv:433-434 |
| info line | (inner.left, inner.top+22, inner.width, 18), font caption, t["muted"] | sv:435-436 |
| buttons y | inner.bottom - 26 | sv:380 |
| left button (Lock/Unlock/Bind) | (inner.left, y, 84, 26) | sv:381 |
| Open button | (inner.right-70, y, 70, 26) | sv:382 |
| pending text | (left.right+10, left.top, open.left - left.right - 14, 26), caption, t["meter_yellow"], text "◤ N block(s) to send" | sv:446-448 |
| offline corner | triangle at card.adjusted(3,3,0,0).topLeft, legs 16 px, no pen, brush t["meter_yellow"] | sv:247-254, sv:429 |

Derived at O = 300 x 196 (card_w = CARD_MIN_W): card 298x194; inner 254x172 (O-relative x 23..277, y 10..182); strip 254x94 (y 54..148); col_w 63.5; cell 51.5x70 (y 74..144); meter_h 70-16-4 = 50; mute y 128..144; buttons y 156..182; gap strip->buttons = 182-26-148 = 8 px. (Derived from sv:263, 269, 274-275, 328, 380.)
Note: whether option.rect equals sizeHint or gridSize cell is Qt-internal (setGridSize sv:516); not determinable from project code.

### 1.3 Card painting / states
| state | painting | file:line |
|---|---|---|
| present unit | paint_panel(card, RADIUS_L=14, notches=(LEFT,)) | sv:421-422 |
| absent or virtual | paint_display(card, RADIUS_L) + dashed border card.adjusted(0.5,0.5,-0.5,-0.5) pen t["muted"] w 1.0 DashLine, radius 14 + paint_screws(card) | sv:415-420, sv:222-229 |
| selected / alarm (status ERROR) ring | ring = t["accent"] if selected else t["error"]; outer: card.adjusted(-0.5,-0.5,0.5,-1.5), alpha(ring,70), radius RADIUS_L+1 = 15, width 4; inner: card.adjusted(0.5,0.5,-0.5,-2.5), ring, radius 14, width 1.6 | sv:423-427 |
| pending offline | yellow corner + pending text | sv:428-429, sv:443-448 |
| title colour | t["muted"] if absent else t["text"] | sv:434 |
| antialiasing | on | sv:409 |
| _text helper | ui_font(role), optional bold override, pen colour, ElideRight to rect width, default align Left|VCenter | sv:208-219 |
| _rounded helper | pen colour/width (default 1.0, radius RADIUS_M=10), DashLine if dashed, NoPen/NoBrush when None | sv:222-229 |

Outputs strip (paint_outputs sv:294-340):
| case | painting | file:line |
|---|---|---|
| no groups | 4 cells (rect.left + i*col_w + 2, rect.top, col_w-4, rect.h), dashed t["border"], radius RADIUS_S=6; letter at cell.adjusted(0,4,0,0) caption bold t["muted"] HCenter|Top; hint at rect.adjusted(0,16,0,0) caption t["muted"] centered: "Choose a speaker" / "Lock the unit to read its outputs" / "Reading the outputs" | sv:300-310 |
| group box background | paint_display(box, RADIUS_S+2 = 8) if present or virtual | sv:315-316 |
| unknown proto / absent | dashed border radius 8, colour t["border"] if known else t["warn"] | sv:317-318 |
| group label text | "A B · Alias" or "A B · ⚠ name"; eyebrow; t["text"] if known else t["muted"] | sv:319-322 |
| LED colour | LIMITER_COLORS[limiter] (default LIMITER_COLORS[0]) or t["meter_bg"] when no data | sv:332-333 |
| mute cell | if can_mute: paint_pill(rect, "X MUTED"/"X MUTE", kind "mute"/"off", pending) else caption t["muted"] centered output letter | sv:287-291, sv:336-340 |
| data live only if unit.locked | | sv:311, sv:325-327 |
| LIM label | caption font shrunk by 0.5 pt steps while advance("LIM") > rect.width and size > 5.0; t["muted"]; Left|VCenter | sv:343-353 |
| buttons | paint_pill kind "primary" for lock, else "normal"; labels Open/Lock/Unlock/"Bind to…"; enabled: lock only if present and lock_state in (UNLOCKED, LOCK_LOST) | sv:438-442, sv:394-400 |

Status text/colour (unit_status sv:54-70, LOCK_TEXT sv:42-49):
| condition | Status | text |
|---|---|---|
| virtual | IDLE | Offline unit |
| not present and not locked | IDLE | Not on network |
| in_use | WARN | In use by another client |
| locked + phase FAILED | ERROR | Error |
| locked + busy phase | BUSY | Reading the outputs / Confirming / Assigning / Verifying (sv:50-51) |
| UNLOCKED / LOCKING / LOCKED / LOCK_STALE / LOCK_LOST / UNLOCKING | IDLE / BUSY / OK / WARN / ERROR / BUSY | Unlocked / Locking / Locked / Stale / Lost / Unlocking |
| any + overview fault | ERROR | "<text> · fault" |
Sort rank: ERROR 0, WARN 1, BUSY 2, OK 3, IDLE 4 (sv:76).
Info line: "<ip | last ip | never seen on the network> · <model> · fw <rev>"; virtual: "prepared offline · bind it to a unit when it is on the network" (sv:473-481). Tooltip HTML lines (sv:165-178).

### 1.4 Grid (UnitGrid)
| property | value | file:line |
|---|---|---|
| view mode / flow / wrapping | ListMode, LeftToRight, wrap True | sv:493-495 |
| resize / uniform sizes | Adjust, True | sv:496-497 |
| selection | ExtendedSelection (Ctrl/Shift), rubber band visible | sv:498-499 |
| drag-drop | InternalMove, default MoveAction; enabled only when sort=="Custom" and filter empty | sv:500-501, sv:643-646 |
| mouse tracking / frame / scroll | True / NoFrame / ScrollPerPixel vertical | sv:502-504 |
| objectName | "unitGrid" | sv:505 |
| fit_cards width | width = max(CARD_MIN_W + 2*GAP = 324, viewport.width) | sv:512 |
| columns | cols = max(1, int((width - 12) // 312)) | sv:513 |
| card_w | (width - 12*(cols+1)) / cols | sv:514 |
| gridSize | (int(card_w + 12), 196 + 12 = 208) | sv:516 |
| drop | emits moved(uid, target ORDER row or rowCount-1); sets IgnoreAction | sv:519-529 |
| repaint | viewport().update() at 25 Hz via MainWindow.refresh | sv:608-610, mw:676-677 |
Example: viewport 1240 -> cols = int(1228//312) = 3, card_w = (1240-48)/3 = 397.33 (illustrative, viewport width not fixed by code).

### 1.5 Interaction
| input | effect | file:line |
|---|---|---|
| left mouse release on a button/mute rect | emits action(uid, name) if enabled ("mute:<n>" toggles mute) | sv:451-470, sv:651-664 |
| double-click card | open_requested | sv:553 |
| right click | context menu: Open; Bind to… / Unlock / Lock (disabled if not present); Rename… (shortcut text F2); separator + "Remove from the list" if not present and not locked | sv:666-693 |
| F2 | rename first selected | sv:695-701 |
| hover | tooltip HTML (ToolTipRole) | sv:154-155 |

### 1.6 Toolbar & page layout (SystemView)
| widget | property | file:line |
|---|---|---|
| filter QLineEdit | placeholder "Filter units…", clear button, max width 260 | sv:560-564 |
| "Sort" label | role muted | sv:587 |
| sort QComboBox | Custom, Name, IP, Status | sv:565-566, sv:182-183 |
| selected_label | role muted, stretch 1, text "N selected" | sv:568, sv:589, sv:627 |
| buttons | "Add offline unit", "Lock selected", "Unlock selected", "Lock all" (primary) | sv:569-575 |
| empty label | role muted, centered, word wrap, stretch 1 | sv:579-582 |
| bar spacing | SPACE*2 = 8 | sv:585 |
| page margins | (SPACE*3, SPACE*3, SPACE*3, 0) = (12,12,12,0) | sv:593 |
| page spacing | SPACE*2 = 8 | sv:594 |

ASCII (System page inside the stack):
```
+-- SystemView ------------------------------------------------------------+
| 12px margin (L/T/R), bottom 0                                             |
| [Filter units…  <=260][8]Sort[8][Custom v][8]N selected (stretch)[8]      |
|   [Add offline unit][8][Lock selected][8][Unlock selected][8][LOCK ALL]   |
| 8px                                                                       |
| UnitGrid (stretch 1)  gridSize = (card_w+12) x 208                        |
|  +-card_w x 196 (item)------+ 12 +-------------------------+              |
|  | 1px | card (card_w-2)x194 |    | ...                     |              |
|  |  22 | inner: TITLE    (chip)| 22 px rows: title h22, info h18          |
|  |     | info line             |                                          |
|  |     | strip (h = inner.h-78 = 94): 4 cols col_w = strip.w/4           |
|  |     |  [grp label h18][cells: bars 8+5, LED r3, LIM, mute pill h16]   |
|  |     | 8px                                                             |
|  |     | [LOCK 84x26] pending text      [OPEN 70x26]   13 px bottom pad  |
|  +---------------------------+                                            |
+---------------------------------------------------------------------------+
```

---

## 2. Unit page (level 2) — unit_view.py

### 2.1 Constants
| property | value | file:line |
|---|---|---|
| CHAIN_CARD_MIN_H | 130 | uv:30 |
| MUTE_W | 84 | uv:31 |
| Chain status | RUNNING OK, SUBSCRIBING BUSY ("subscribing a+f/total"), STANDBY IDLE, WAITING_LOCK IDLE, FAILED ERROR; offline/virtual -> IDLE "offline" | uv:32-44 |

### 2.2 ChainCard geometry (widget rect R)
| element | formula | file:line |
|---|---|---|
| min width | 320 | uv:67 |
| fixed height | max(130, 120 + rows*28), rows = ways+1 (0 without chain) -> 1W 176, 2W 204, 3W 232, 4W 260, none 130 | uv:66-68 |
| size policy | Expanding x Fixed | uv:69 |
| card | R.adjusted(1,1,-1,-1); paint_panel(card, RADIUS_L=14, notches=(LEFT,)) | uv:129-130 |
| inner | card.adjusted(24,12,-24,-16) (= R.adjusted(25,13,-25,-17), uv:115) | uv:131 |
| Open button | primary "Open the chain  ›", sizeHint, at (R.w - hint.w - 16, R.h - hint.h - 14) | uv:70, uv:112-114 |
| mute buttons | QPushButton objectName "muteButton", property mute=True, checkable, pointing hand; geometry (inner.right-84, inner.top + 56 + row*28, 84, 22), row = 1 + output - base | uv:76-84, uv:115-119 |
| chip | paint_chip(right=inner.right, top=inner.top) h 22 | uv:148 |
| title | (inner.left, inner.top, chip.left - inner.left - 8, 24), heading, t["text"]: "Chain A · outputs A B" | uv:149-150 |
| subtitle | (inner.left, inner.top+24, inner.width, 20), body, t["muted"]: "alias · chain title" | uv:151-152 |
| rows start y | inner.top + 56; pitch 28 | uv:155, uv:191 |
| right limit | right = inner.right - MUTE_W - 8 = inner.right - 92 | uv:170 |
| meters display | paint_display((inner.left-8, y0-4, right - inner.left + 12, n_rows*28 + 2), RADIUS_M=10) | uv:172-173 |
| bar_w | (right - inner.left - 92) * 0.48 | uv:174 |
| row label | (inner.left, y, 84, 22), eyebrow, t["text"] (IN: t["muted"]) | uv:176-177 |
| level bar | (inner.left+92, y+6, bar_w, 10), LEVEL, segments=True | uv:178-179 |
| level value | (bar.right+8, y, 52, 22), caption, t["muted"], "{:.0f} dB" or "–" | uv:180-181 |
| GR bar (OUT rows) | (bar.right+62, y+6, max(24, right - bar.right - 62 - 104), 10), GR | uv:183-184 |
| GR text | (gbar.right+6, y, 50, 22), caption muted, "GR {:.1f}" / "GR –" | uv:185-186 |
| LED | centre (right-38, y+11), r 4; colour LIMITER_COLORS or t["meter_bg"] | uv:187-189 |
| "LIM" | (right-30, y, 30, 22), caption muted | uv:190 |
| pending text | (inner.left, inner.bottom-28, inner.width/2, 28), body, t["meter_yellow"] | uv:192-195 |
| offline corner | paint_offline_corner(card.adjusted(3,3,0,0)) | uv:145-146 |
| unknown group | "Outputs A B" (inner.left, inner.top, inner.w, 24) section t["text"]; message (inner.left, inner.top+30, inner.w, 40) body t["warn"] Left|Top | uv:133-143 |

States / interaction:
| item | value | file:line |
|---|---|---|
| mute text | "X MUTED" checked / "X Mute"; tooltip "Mute/Unmute output X" + " (being written or waiting to be sent)" if pending | uv:97-105 |
| mute pending | dynamic property "pending" + unpolish/polish | uv:106-109 |
| card click | left mouse release anywhere -> open chain (if chain) | uv:121-123 |
| cursor | PointingHand if chain else Arrow | uv:86-87 |

### 2.3 UnitView (page) layout
| widget | property | file:line |
|---|---|---|
| title | QLabel, ui_font("page") | uv:278-279 |
| status | QLabel objectName "statusChip", rich text `<span style='color:{t[c]}'>●</span>&nbsp; text`, c in ok/warn/error/busy/muted | uv:280-281, uv:363-366 |
| info | role muted, selectable by mouse; "info_line · UID x · output_mode n: text" | uv:282-283, uv:367-373 |
| message | role "banner-info", word wrap, hidden when empty | uv:284-285, uv:374-376 |
| lock_button | "Lock"/"Unlock"/"Bind to…", min width 96 | uv:286-288, uv:378-379 |
| prototype segments | checkable QPushButton per prototype, property segment first/mid/last, pointing hand, layout spacing 0 | uv:291-306 |
| "Speaker" label | role muted, ui_font("section") | uv:313-314 |
| "Outputs…" button | opens LayoutDialog | uv:317-321 |
| head row spacing | SPACE*3 = 12; extra addSpacing SPACE*2 = 8 before lock button | uv:309, uv:322 |
| cards grid | margins 0, spacing SPACE*4 = 16; columns 2 if >1 group else 1 | uv:326-328, uv:424-429 |
| scroll | widgetResizable, NoFrame; holder VBox margins 0 + stretch | uv:332-341 |
| page margins | (SPACE*4, SPACE*3, SPACE*4, SPACE*2) = (16,12,16,8) | uv:344 |
| page spacing | SPACE*2 = 8 | uv:345 |

ASCII:
```
+-- UnitView --------------------------------------------------------------+
| margins L16 T12 R16 B8                                                    |
| TITLE(page) [12] ● status [12] <stretch> SPEAKER [12] [1W|2W|..](0 gap)   |
|                                     [12][Outputs…][12 + 8][Lock >=96]     |
| 8  info (muted)                                                           |
| 8  [banner-info message]                                                  |
| 8  QScrollArea (stretch 1)                                                |
|    +-- ChainCard (>=320 x 120+28*(ways+1)) --+ 16 +-- ChainCard --+       |
|    | 25 | TITLE(heading)h24        (chip h22)|    |               |       |
|    |    | subtitle h20                       |    |               |       |
|    |    | y=inner.top+56: rows pitch 28      |    |               |       |
|    |    | IN   [lvl bar h10] -- dB           |    |               |       |
|    |    | OUT A[lvl][GR] GR x  ●LIM [A Mute 84x22]                 |       |
|    |    |                 [OPEN THE CHAIN ›] 16 from right, 14 bottom|     |
|    +-----------------------------------------+    +---------------+       |
+---------------------------------------------------------------------------+
```

### 2.4 Outputs dialog (LayoutDialog)
| property | value | file:line |
|---|---|---|
| window title | "Outputs of {unit}" | uv:206 |
| mode combo | items LAYOUT_TEXT (text, mode) in form row "Outputs" | uv:207-209, uv:220-221 |
| rows | QFormLayout, one combo per group "Outputs A B", items "{alias} · {model_name}" filtered by ways | uv:210, uv:242-254 |
| note | role "banner-warning", word wrap, visible only for MIXED_MODES | uv:212-214, uv:255 |
| buttons | Ok | Cancel | uv:215-218 |
| layout | QVBoxLayout default margins/spacing (not set: style default, not determinable) | uv:219-225 |
ASCII:
```
+ Outputs of <unit> --------------+
| Outputs  [AB | CD          v]   |
| Outputs A B [2Way · model  v]   |
| Outputs C D [2Way · model  v]   |
| [banner-warning: mixed modes]   |
|                 [OK] [Cancel]   |
+---------------------------------+  (margins/spacings: Qt defaults)
```

---

## 3. Navigation — navigation.py
| component | property | value | file:line |
|---|---|---|---|
| Breadcrumb | margins / spacing | 0 / SPACE = 4 | nav:38-39 |
| Breadcrumb | separator | QLabel "›" role muted | nav:58-59 |
| Breadcrumb | current (last) | QLabel ui_font("section") | nav:60-63 |
| Breadcrumb | earlier parts | QPushButton property ghost=True, PointingHand, click -> chosen | nav:64-69 |
| Breadcrumb | trailing stretch | 1 | nav:70 |
| PlaceNav | margins / spacing | 0 / SPACE*2 = 8 | nav:117-118 |
| PlaceNav | prev/next | "‹" / "›", ghost, fixed width 34, font heading, tooltip "Previous/Next: <place>", disabled when no sibling | nav:119-120, nav:128-133, nav:143-147 |
| PlaceNav | label | centered, font = heading + 1.5 pt, size policy Minimum x Preferred, stretch 1 | nav:121-127, nav:135 |
| PlaceNav | text | "System · N unit(s)" / unit title / "unit · chain A · alias" | nav:76-87 |
| Sidebar | objectName | "sidebar" | nav:164 |
| Sidebar | header / root decorated / indentation | hidden / True / 14 | nav:165-167 |
| Sidebar | min / max width | 170 / 260 | nav:168-169 |
| Sidebar | root item | "System", ui_font("section"), always expanded | nav:186-189, nav:205 |
| Sidebar | unit item | icon status_icon(status), tooltip "title: text"; IDLE & not present -> foreground palette placeholderText | nav:192-197 |
| Sidebar | chain child | "{outputs} · {alias}" | nav:199 |
| Sidebar | interaction | itemClicked and itemActivated -> chosen; expansion state preserved; current unit expanded | nav:170-171, nav:181-183, nav:204 |

---

## 4. Main window / chrome — main_window.py

### 4.1 Constants & timings
| property | value | file:line |
|---|---|---|
| default size | 1480 x 860 | mw:238 |
| ERROR_DISPLAY_MS | 10 000 | mw:66 |
| INFO_DISPLAY_MS | 2 000; status() = INFO*3 = 6 000; "Open a chain…" = INFO*2 = 4 000 | mw:67, mw:957, mw:872-873 |
| HEADER_LOGO_PX / ABOUT_LOGO_PX | 32 / 64 | mw:68-69 |
| refresh timer | 1000/GUI_REFRESH_HZ = 40 ms | mw:348-351 |
| WorkerBridge flush timer | 40 ms | mw:107-110 |
| window titles | "SpeakerNet" / "SpeakerNet · <project file>" | mw:236, mw:1104-1106 |

### 4.2 Header (top bar, `_header`)
| item | value | file:line |
|---|---|---|
| frame objectName | "header" | mw:1330 |
| margins | (SPACE*3, SPACE*2, SPACE*3, SPACE*2) = (12,8,12,8) | mw:1332 |
| spacing | SPACE*2 = 8 | mw:1333 |
| logo | QLabel pixmap logo_pixmap(32), hidden if null | mw:1334-1336 |
| title | "SpeakerNet", objectName "appTitle", ui_font("heading") weight Normal, letter spacing 132 % (uppercase from heading role) | mw:1339-1344 |
| spacing after title | SPACE*3 = 12 | mw:1351 |
| menu bar | QMenuBar objectName "headerMenu", size policy Fixed x Fixed, AlignVCenter (menuBar() returns it) | mw:1346-1348, mw:1352, mw:355-357 |
| stretches | stretch 1, PlaceNav stretch 2, stretch 1 | mw:1353-1357 |
| chips | 3x StatusChip AlignVCenter: units, pending (hidden when 0, "◤ N block(s) to send" WARN), place/phase | mw:1359-1363, mw:1370-1384 |
| units chip status | ERROR if lost, WARN if in_use, OK if locked, else IDLE; "No unit · offline" IDLE when none | mw:1371-1377 |
| place chip text | "<unit>[ · outputs alias] · <phase text>[ — message][ · N blocks to send]"; "System" IDLE | mw:1386-1407 |

### 4.3 Nav row, splitter, body
| item | value | file:line |
|---|---|---|
| sidebar_button | "◀" (visible) / "▶" (hidden), property small=True, tooltip "Show or hide the units (Ctrl+B)" | mw:308-311, mw:443 |
| back_hint | role caption "Esc / Alt+← back · Ctrl+B sidebar" | mw:312 |
| nav margins | (SPACE*2, SPACE, SPACE*3, SPACE) = (8,4,12,4) | mw:314 |
| nav spacing | 8 | mw:315 |
| nav order | sidebar_button, breadcrumb (stretch 1), back_hint | mw:316-318 |
| splitter | [Sidebar, Stack], stretchFactor(1,1), sizes [200, 1280], children not collapsible | mw:319-324 |
| body | margins 0, spacing 0: header, nav, splitter (stretch 1) | mw:326-333 |
| status bar | IoBar; permanent widgets "Discovery from: …", "Local port N · units on port M" | mw:335-339, mw:575-581 |

### 4.4 Menus & shortcuts
| item | value | file:line |
|---|---|---|
| &File | Save (StandardKey.Save), Save as… (StandardKey.SaveAs), separator, Load… (StandardKey.Open) | mw:360-370 |
| &Settings | Network ports… | mw:371-372 |
| &View | System; Units sidebar (checkable, checked); submenu "Detailed meters on the cards": Automatic (up to 4 units) [default checked] / On / Off (exclusive QActionGroup); separator; Block parameters; Presets | mw:373-391 |
| &Window | dynamic list of visible parameter windows; empty -> "No parameter window open" disabled | mw:392-393, mw:552-559 |
| &Help | About SpeakerNet (QMessageBox, logo 64, rich text) | mw:394-395, mw:1410-1420 |
| Esc | go_up | mw:342 |
| Alt+Left | go_up | mw:343 |
| Ctrl+B | toggle sidebar | mw:344-345 |
| confirmations | QMessageBox Warning, Yes/No, default No | mw:587-595 |

### 4.5 Chain page (level 3)
| item | value | file:line |
|---|---|---|
| title row spacing | SPACE*2 = 8 | mw:278-279 |
| "DSP chain" | section_title | mw:280 |
| hint | role muted "Click a block to open its parameters", policy Ignored x Preferred, stretch 1 | mw:281-283 |
| Legend | see 4.6 | mw:284 |
| Presets… button | icon themed_icon("presets","button_text") | mw:285-290 |
| page margins | (SPACE*3, SPACE*2, SPACE*3, SPACE*2) = (12,8,12,8) | mw:293 |
| page spacing | SPACE = 4 | mw:294 |
| chain_view / placeholder | stretch 1 each (one visible); placeholder "This unit has no chain on these outputs." centered, role muted, ui_font("title") | mw:273-277, mw:296-297 |

### 4.6 Legend widget (painted)
| property | value | file:line |
|---|---|---|
| sizeHint | 640 x 22 | mw:126-127 |
| items | CATEGORY_COLORS[key] per LEGEND entry + ("preset" colour, "Duplicated by DSP", dashed) | mw:123-124 |
| swatch | rounded rect (x, y-6, 18, 12), radius 3, pen category colour width 1.6 (DashLine for dup), brush t["surface"]; y = height/2 | mw:135-142 |
| label | pen t["muted"], baseline (x+24, y + ascent/2 - 1), widget font | mw:143-144 |
| advance | x += 24 + advance(text) + 18 | mw:145 |
| LEDs | paint_led(centre (x+5, y), r 4.5) t["ok"] "Active", t["error"] "Muted"; text at x+14; x += 14 + advance + 18 | mw:146-150 |

ASCII (whole window, System level):
```
+-- MainWindow 1480 x 860 ----------------------------------------------------------+
| header (objName header) margins 12/8/12/8, spacing 8; height >= 32+16 = 48 (logo)   |
| [logo32][SPEAKERNET][12][File Settings View Window Help] <s1> [‹][PLACE][›] (s2) <s1>|
|                                              [units chip][pending chip][place chip] |
+-------------------------------------------------------------------------------------+
| nav margins 8/4/12/4 spacing 8: [◀] System › Unit › Chain (stretch)  Esc / Alt+← … |
+--------------+----------------------------------------------------------------------+
| Sidebar      | QStackedWidget: SystemView | UnitView | Chain page                    |
| 170..260 w   | splitter initial sizes 200 / 1280                                    |
| (init 200)   |                                                                      |
+--------------+----------------------------------------------------------------------+
| IoBar status bar: messages … | Discovery from: … | Local port N · units on port M   |
+-------------------------------------------------------------------------------------+
```
Chain page:
```
+-- chain page margins 12/8/12/8, spacing 4 -------------------------------+
| DSP CHAIN [8] Click a block… (stretch) [8] Legend(640x22) [8] [Presets…] |
| 4                                                                        |
| ChainView (stretch 1)   | or placeholder (title font, muted, centered)   |
+--------------------------------------------------------------------------+
```

---

## 5. Block parameters window — block_window.py

### 5.1 Constants
| property | value | file:line |
|---|---|---|
| CURVE_POINTS | 160 | bw:56 |
| KNOB_BAR_PX | 30 | bw:57 |
| GEOMETRY_KEY | "blockWindow/geometry" | bw:58 |
| DYNAMIC_EQ_BLOCKS / DYNAMIC_KIND | {"fact_dynpeq"} / "Dynamic PEQ" | bw:62-63 |
| DYNAMIC_SMOOTH_S | 0.1 s; k = min(1, dt/0.1); settle when |target-shown| < 0.01 | bw:64, bw:1072-1080 |
| BAND_DEFAULTS | enable 0, type 0, order 1, q 0.707, gain 0, freq 1000, threshold 0, ratio 1 | bw:65-66 |
| default size | 820 x 860 (geometry restored from QSettings if saved; saved on close) | bw:1191-1195, bw:1342-1345 |
| window title | "SpeakerNet · Block parameters" / "SpeakerNet · <unit> · <A> (<alias>) · Block parameters" / "SpeakerNet · <alias> · Block parameters" | bw:1180, bw:1233-1241 |
| window flag | Qt.Window (parented) | bw:1173 |

### 5.2 Tabs
| item | value | file:line |
|---|---|---|
| QTabWidget | SectionTabWidget with SectionTabBar; tabsClosable False (custom close), movable, documentMode, scroll buttons | bw:1181-1185 |
| window layout | margins 0, tabs only | bw:1188-1190 |
| tab title | node label or "Meter thresholds" (OUTPUT); multi-way: " · <way name>" | bw:77-81 |
| tab tooltip | panel URI | bw:1296 |
| closing last tab | hides window | bw:1311-1316 |
| SectionTabBar plain tab | default style CE_TabBarTab | bw:162-164 |
| section tab body | rect = option.rect.adjusted(1,2,-1,0); brush SECTION_COLORS[section], no pen; drawRoundedRect(rect.adjusted(0,0,0,6), 6, 6) (bottom corners hidden) | bw:165-169 |
| section tab text | colour text_on(fill); bold when selected; text rect (rect.left+10, rect.top, rect.width-14-room, rect.height), room = close.width+6 = 22; VCenter|Left; ElideRight | bw:170-180 |
| selected underline | rect (rect.left, rect.bottom-2, rect.width, 3), brush ink | bw:181-183 |
| TabCloseButton | fixed 16x16, PointingHand, tooltip "Close" | bw:92-94 |
| close ink | section text colour, else t["text"] on hover / t["muted"] | bw:115-117 |
| close hover halo | ellipse rect.adjusted(1,1,-1,-1), ink with alpha 50, no pen | bw:120-125 |
| close X | pen ink width 1.8; two lines centre ±3 px | bw:126-129 |

### 5.3 BlockPanel layout
| item | value | file:line |
|---|---|---|
| margins / spacing | SPACE*3 = 12 all sides / SPACE*2 = 8 | bw:682-683 |
| title | ui_font("page"); "<context> · <name>" | bw:606-607, bw:734 |
| detail | role muted, wrap: "uri · category[ · duplicated…][ · read HH:MM:SS]" | bw:608-609, bw:735-740 |
| section_row | margins 0: "Preset section" QLabel, SectionCombo, note (role muted, wrap, stretch 1) | bw:617-627 |
| mirror | role "banner-info", wrap, hidden by default | bw:610-612 |
| warning | role "banner-warning", wrap, hidden when empty | bw:613-615, bw:747-764 |
| meters | MeterPanel | bw:616 |
| EQ card | card(QFrame), margins SPACE*2 = 8, spacing 8: BandBar, EqEditor (stretch 1); card stretch 3 | bw:692-698 |
| params scroll | QScrollArea resizable NoFrame, stretch 2 with EQ else 3 | bw:675-679, bw:699 |
| form choice | mb_compr -> MultibandForm; drex_lim -> DrexForm; out_lim/dyn_compr -> CompressorForm; else RequestForm | bw:632-647 |
| writable | form enabled only if writable & has_data & group=="config" & write methods | bw:801-809 |
| refusal | QMessageBox.warning "<title>: filter not available" | bw:925-927, bw:1306-1308 |

ASCII:
```
+-- BlockWindow 820 x 860 (margins 0) -------------------------------+
| [tab][SECTION TAB (fill)  x][tab x] ...  (document mode, movable)  |
+--------------------------------------------------------------------+
| BlockPanel margins 12, spacing 8                                   |
| TITLE (page)                                                       |
| uri · category · read hh:mm:ss (muted)                             |
| Preset section [SectionCombo] note…                                |
| [banner-info mirror] [banner-warning]                              |
| MeterPanel                                                         |
| +-- EQ card (margins 8, spacing 8) ---------- stretch 3 ---------+ |
| | BandBar (3 rows, spacing 8)                                     | |
| | EqEditor (stretch 1)                                            | |
| +----------------------------------------------------------------+ |
| QScrollArea: form ------------------------------- stretch 2 (3)    |
+--------------------------------------------------------------------+
```

### 5.4 BandBar
| item | value | file:line |
|---|---|---|
| outer VBox | margins 0, spacing SPACE*2 = 8: top_row, fields, view | bw:492-497 |
| top_row | spacing 8: BandStrip (stretch 1), "Add band" (icon themed_icon("plus","button_text")) | bw:389-391, bw:431-434 |
| fields row | spacing SPACE = 4: band_label (section font, min width 64, "● Band n" coloured / "No band"), "On" checkbox, +4; per field: +4, muted label, [knob], widget; +SPACE*2 = 8; live label (stretch 1); addStretch(0 if extras else 1) | bw:354-357, bw:452-472, bw:537 |
| field order | Type, Order, Freq, Gain, Q, Threshold, Ratio (hidden if field absent) | bw:457-464 |
| type/order combos | AdjustToMinimumContentsLengthWithIcon, min contents 9, guard_wheel | bw:358-365, bw:387-388 |
| spins (_spin) | DragSpinBox, min width 84, numeric_font("body"), keyboardTracking False, range field min/max or ±1e9, guard_wheel | bw:499-513 |
| freq | 0 decimals, " Hz", step 1.0, log drag | bw:366 |
| gain | 1 decimal, " dB", step 0.1 | bw:367 |
| q | 3 decimals, "", step 0.01, log drag; disabled when type has no Q | bw:368, bw:548 |
| threshold / ratio (dyn EQ) | 1 dec " dB" 0.1 / 1 dec ":1" 0.1 | bw:438-444 |
| knobs | Knob size KNOB_BAR_PX = 30, show_value False; freq log if min>0; gain bipolar; accessible names Frequency/Gain; knob<->spin two-way; double-click -> focus spin + selectAll | bw:375-386 |
| live label | role muted, numeric_font("caption"), policy Ignored, hidden unless text: "side-chain x dBFS  ·  threshold t  ·  GR g dB" | bw:446-451, bw:1125-1127 |
| view row | spacing 4: hint (role caption + ui_font caption, Ignored, stretch 1) "Drag: Shift freq only · Alt gain only · Ctrl fine · double-click a value to type it"; "Scale" muted; segments spacing 0; +8; crosshair; +8; Bands; Combined | bw:473-491 |
| scale buttons | "±6","±12","±18","±24","Auto"; checkable, exclusive QButtonGroup, segment first/mid/last, small=True; Auto default checked | bw:404-418 |
| crosshair | ghost, checkable, icon themed_icon("crosshair","muted") | bw:398-403 |
| Bands / Combined | QCheckBox, both checked | bw:392-397 |
| enable states | On always enabled when a band is selected; others only if band enabled; Add enabled if any band off | bw:548-554 |

ASCII:
```
[ BandStrip chips (stretch) .................................. ][8][+ Add band]
8
● BAND n[4][On][4][4]Type[combo][4]Order[combo][4]Freq(knob30)[spin>=84][4]Gain(knob30)[spin][4]Q[spin] [8] live… <stretch>
8
hint (caption, stretch) …  Scale [±6|±12|±18|±24|Auto] [8] [⌖] [8] [x]Bands [x]Combined
```

### 5.5 BandStrip (painted)
| property | value | file:line |
|---|---|---|
| CHIP_H / CHIP_MIN_W / CHIP_W | 40 / 30 / 64 | bw:202-204 |
| fixed height | 40; policy Expanding x Fixed; cursor PointingHand; mouse tracking | bw:212-215 |
| sizeHint / min | (n*64, 40) / (n*30, 40), n = max(1, bands) | bw:222-226 |
| chip_rect(i) | w = min(widget.w / n, 64*1.6 = 102.4); (i*w + 1, 1, w-3, 38) | bw:228-231 |
| border | t["accent"] width 1.6 if selected else t["field_border"] width 1 | bw:279-280 |
| fill | t["elevated"] if selected or hover else t["field"] | bw:281 |
| shape | rect.adjusted(0.5,0.5,-0.5,-0.5), radius RADIUS_S = 6 | bw:282 |
| colour bar (enabled) | (left+3, top+2, w-6, 3), radius 1.5, band_color(index), no pen | bw:283-287 |
| number dot | r 7, centre (left+4+7, top+7+7) = (left+11, top+14); enabled: filled band colour, ink text_on(colour); off: pen t["control"] 1.2, no brush, ink t["muted"] | bw:290-300 |
| number font | numeric_font("caption") bold; centered in dot | bw:272-273, bw:301-304 |
| value font | numeric_font("caption") | bw:274 |
| first line rect | (cx+r+3, cy-r, rect.right - cx - r - 5, 2r) — frequency (t["text"]) | bw:307-308, bw:317-320 |
| second line rect | (left+5, cy+r+1, w-9, bottom - cy - r - 2) — gain "+x.x dB" (or "+x.x" if too wide), dyn: live gain or "dyn —"; off: "off" muted | bw:309-315, bw:321-331 |
| narrow chip | if freq doesn't fit first line, freq drawn in second line instead of gain | bw:317, bw:326-327 |
| gain colour | band colour if fixed_gain and |live| >= DYNAMIC_MIN_DB (0.05), else t["muted"] | bw:328-329 |
| interaction | hover -> tooltip + repaint; left press -> chosen(index); double-click -> toggled(index, !enabled) if widget enabled | bw:246-266 |
| tooltip | "Band n · off\nClick: select · double-click: switch on" / "Band n · kind · freq · ±g dB · Q q (or N dB/oct)\nClick: select · double-click: switch off" | bw:239-244 |

---

## 6. Form editors — forms.py

### 6.1 Constants
| property | value | file:line |
|---|---|---|
| FLOAT_DISPLAY_LIMIT | 1e12 | fm:33 |
| TABLE_MIN_VISIBLE_ROWS | 6 | fm:34 |
| COMPACT_COMBO_CHARS | 9 | fm:35 |
| HEX_PREVIEW_BYTES | 48 (declared; unused in file) | fm:36 |
| LARGE_VECTOR | 32 | fm:38 |
| SLIDER_FIELDS | {"gain","delay","post_gain"} | fm:230 |
| SLIDER_MAX_STEPS | 100 000 | fm:231 |
| KNOB_NAME | `(^|_)(gain|freq|threshold|ratio|attack|release)(_high|_low)?$` (search) | fm:277 |
| KNOB_PX / KNOB_SMALL_PX | 52 / 40 | fm:278-279 |

### 6.2 WheelGuard / guard_wheel
Wheel events ignored (passed to page scroll) unless widget has focus; focus policy StrongFocus (fm:62-78).

### 6.3 DragSpinBox
| property | value | file:line |
|---|---|---|
| DRAG_START_PX | 3 | fm:89 |
| PX_PER_STEP | 4.0 (linear: px per singleStep) | fm:90 |
| PX_PER_OCTAVE | 120.0 (log: px to double) | fm:91 |
| modifiers | Ctrl factor 0.1 (fine), Shift factor 10 (fast), else 1 | fm:122-123 |
| log drag | value' = max(value, 10^-decimals) * 2^(dy*factor/120) | fm:124-127 |
| linear drag | acc += dy*factor/4; apply int(acc) steps * singleStep | fm:128-132 |
| dy | last_y - y (upward drag = positive = increase) | fm:147 |
| active only | when enabled and NOT focused (filter on lineEdit) | fm:135-136 |
| click without drag | setFocus + selectAll (enter typing) | fm:150-155 |
| cursor | SizeVerCursor unfocused, IBeamCursor focused | fm:107-117 |

### 6.4 Editors
| editor | properties | file:line |
|---|---|---|
| NumberEditor | DragSpinBox, align Right|VCenter, numeric_font("body"), decimals_for(f), range clipped ±1e12, singleStep f.step or 1.0, suffix " unit", keyboardTracking False, min width 110, guard_wheel; keeps exact device value until edited; out-of-range read widens range | fm:184-226 |
| decimals_for | step<1 -> min(6, ceil(-log10 step)); step>=1 -> 0; scale<1 -> min(6, ceil(-log10|scale|)); float32 -> 3; else 0 | fm:174-181 |
| SliderNumberEditor | horizontal QSlider min width 120, range 0..min(round((hi-lo)/step), 100000), pageStep max(1, max//20), guard_wheel; row margins 0 spacing 8 (literal), spin + slider (stretch 1); tooltip "Drag to set <name>; the arrow keys move it by one step" | fm:234-271 |
| KnobNumberEditor | spin min width 0, fixed width 104 if size >= 52 else 88; Knob(label = name with "_"->" " or given, lo, hi, log = "freq" in name and lo>0, bipolar = lo<0<hi, size, formatter = spin text + suffix, show_value False); column margins 0 spacing SPACE = 4, knob and spin AlignHCenter; knob value rounded to step, applied if |delta| >= step/2; knob edit_requested (double-click/Enter) -> focus spin + selectAll; tooltip "Drag up or down to set <name> (Shift: fine); double-click to type the value" | fm:286-324 |
| EnumEditor | QComboBox sorted enum, guard_wheel; unknown -> "<key> — undocumented value" | fm:327-349 |
| BitsEditor | QGridLayout margins 0, 2 per row: flag QCheckBox spans 2 cols; group: QLabel + QComboBox/QSpinBox(0..2^n-1) | fm:352-379 |
| TextEditor | QLineEdit maxLength item_size, placeholder "up to N bytes", commit on editingFinished | fm:422-436 |
| HexEditor | QLineEdit placeholder "N bytes, hexadecimal", hex with spaces | fm:439-452 |
| BoolEditor | QCheckBox (no text), integer 0..1 without enum | fm:572-588, fm:603-604 |
| make_editor priority | char[] Text, bytes[] Hex, enum, bits, bool, (slider) knob field -> Knob, (slider) SLIDER_FIELDS with min/max -> Slider, else Number | fm:591-609 |

### 6.5 RequestForm layout
| item | value | file:line |
|---|---|---|
| root VBox | margins 0, spacing SPACE*2 = 8; "Empty payload: no parameters." when no fields | fm:636-640 |
| card | card(QFrame); margins (SPACE*3, SPACE*2, SPACE*3, SPACE*3) = (12,8,12,12); spacing 8 | fm:681-685 |
| card heading | "Parameters" (first card only), ui_font("section") | fm:667, fm:686-689 |
| knob row | QHBoxLayout spacing SPACE*4 = 16, above the form | fm:695-697 |
| QFormLayout | FieldsStayAtSizeHint; labels Right|VCenter; hSpacing 12; vSpacing 8 | fm:690-694 |
| card width | row = card + addStretch(1) -> card at size hint, left aligned | fm:699-702 |
| labels | role muted unless rich header (starts "<"); tooltip = description + limits | fm:709-719 |
| table label | "<b>name</b> · N item(s)" / "<b>name</b> · N taps" | fm:651, fm:657-658 |
| tables | SingleSelection, SelectRows, NoEditTriggers, header ResizeToContents; min height = header.h + 4 + sum(first min(rows,6) row heights); table stretch 1 | fm:721-738, fm:660 |
| compact cell editors | combos AdjustToMinimumContentsLengthWithIcon, min contents 9, popup min width sizeHintForColumn(0)+24; number spin min width 0 | fm:740-752 |
| trailing stretch | if no tables | fm:675-676 |

### 6.6 TapsPanel
| item | value | file:line |
|---|---|---|
| chart | plots.ImpulseChart (not painted in forms.py) or none (compact/multiband) | fm:464, fm:470 |
| buttons | "Import .txt…"/"Export .txt…"/"Clear"; compact: "Import…"/"Export…"/"Clear" with property compact=True; info role muted + caption font | fm:474-481 |
| layout | VBox margins 0: chart, buttons row (+stretch), info (wrap) | fm:489-498 |
| info text | "N taps (limits lo…hi)." / "N values read from <path>." (+ padded zeros) / "N values saved to <path>." (compact: file name only) | fm:515, fm:528-536, fm:538-540 |
| dialogs | open "Text (*.txt);;All files (*)", save default "taps.txt" | fm:544, fm:550 |

---

## 7. Dynamics — dynamics.py

### 7.1 Constants
| property | value | file:line |
|---|---|---|
| CURVE_IN | (-80.0, 0.0) | dy:33 |
| INPUT_FLOOR_DB | -80.0 | dy:34 |
| CURVE_STEP_DB | 0.5 | dy:35 |
| COMPRESSOR_BLOCKS | {"out_lim","dyn_compr"} | dy:36 |
| soft knee | quadratic: knee>0 and 2|over|<=knee -> level + (1/ratio-1)*(over+knee/2)^2/(2*knee); over>0 -> T + over/ratio; + post_gain; ratio floored at 1 | dy:39-53 |

### 7.2 TransferCurve (PlotWidget)
| property | value | file:line |
|---|---|---|
| min height / policy | 200 / Expanding x Expanding | dy:63-64 |
| x range / ticks / minor | -80..0, labels every 20 (-80..0), minor -70,-50,-30,-10 | dy:66-68 |
| y range | top = max(0, ceil(gain/10)*10), bottom = -80 + min(0, floor(gain/10)*10); ticks every 20; gain = makeup if enabled | dy:94-99 |
| 1:1 diagonal | t["grid_major"], 1 px, DashLine | dy:132-133 |
| 1:1 + post gain | t["grid_minor"], 1 px, DashLine (only if gain != 0) | dy:134-136 |
| knee lines | alpha(accent,150), 1 px, DotLine, full height | dy:137-142 |
| veil (enabled) | path curve -> (hi,hi+gain) -> (lo,lo+gain), brush alpha(accent,45), no pen | dy:146-155 |
| curve halo | alpha(ink,60) width 5 | dy:161-162 |
| curve | ink width 2.0, RoundCap, RoundJoin; ink = t["accent"] (ACCENT="accent") if enabled else t["muted"] | dy:59, dy:159, dy:163-165 |
| knee dots | r 3.5, pen t["text"] 1.2, brush accent | dy:166-171 |
| signal colour | t["error"] if reducing (level+gain-out > 0.05) else t["ok"] | dy:185-186 |
| input vertical line | alpha(colour,150), 1.2 | dy:187-189 |
| reduction segment | colour 2.5 from (level, level+gain) to dot | dy:191-193 |
| static ring (measured) | r 4.5, pen t["text"] 1.2, no brush | dy:194-197 |
| peak mark | horizontal tick ±5 px, t["text"] 1.5 (if peak > level+0.3) | dy:198-202 |
| dot | r 6, pen t["text"] 1.5, brush colour | dy:203-205 |
| header text | numeric_font("caption"); rect.adjusted(6,3,-6,-3) Top|Left; t["text"] enabled / t["muted"] "off (1:1)" | dy:209-213 |
| footer text | rect.adjusted(6,3,-6,-4) Bottom|Right t["muted"]: "input x dBFS  ·  GR g dB[ (unit)]" or "input: no data from the unit" | dy:214-225 |
| SoftKnee header | "T +x.x dB · r:1[ · knee k][ · post +p dB]" | dy:251-257 |
| InputFollower | MeterAnim ballistics via MeterTimer (~30 fps per docstring); stops when settled/hidden | dy:260-285 |

### 7.3 CompressorForm layout
| item | value | file:line |
|---|---|---|
| row | HBox spacing 8: params card (stretch 2), graph card (stretch 3) | dy:299-300, dy:343-344 |
| params card | margins (12,8,12,12), spacing 8; "Parameters" section font; QFormLayout labels Right|VCenter, h 12 v 8; knob grid h SPACE*4 = 16, v SPACE*3 = 12, 2 columns, AlignHCenter; non-knob spins min width 96; stretch | dy:301-328 |
| graph card | margins (12,8,12,12), spacing SPACE = 4; "Compression curve" section; note caption muted wrap; curve stretch 1 | dy:329-342 |
| row in form | stretch 1 | dy:345 |

---

## 8. Drex (drex_lim) — drex.py
| property | value | file:line |
|---|---|---|
| stage prefixes | "side-chain_filter_", "drive_filter_", "compr_" | dx:43 |
| panel titles/notes | Side chain filter / Drive filter / Compressor (+ captions) | dx:44-50 |
| field order | sc/drive: type, freq, q, gain; compr: threshold_low, ratio_low, threshold_high, ratio_high, attack, release | dx:51-53 |
| DRIVE_TYPES | {0:2, 1:1, 2:0} | dx:59 |
| DRIVE_RANGE / POINTS / MIN_CHANGE | 20..500 Hz / 120 / 0.01 dB | dx:60-62 |
| envelope | one-pole: tau = (attack if rising else release)/1000; k = 1 - exp(-dt/tau) (1 if tau<=0) | dx:80-86 |
| TwoPointCurve header | "low +x dB · r:1   high +y dB · r:1" | dx:110-112 |

DriveFilterChart:
| property | value | file:line |
|---|---|---|
| min height / policy | 170 / Expanding x Expanding | dx:121-122 |
| x | log, 20..500; ticks 20,50,100,200,500; major 100; minor 30,40,60,70,80,90,300,400 | dx:123-129 |
| zero line / points | True / not drawn | dx:124-125 |
| y | top = max(6, ceil((gain+3)/6)*6); bottom = min(-24, floor((gain-24)/6)*6); step 6 if span<=36 else 12; labels "+d" / "0" | dx:143-149 |
| freq marker | alpha(accent,140) 1 px DotLine | dx:201-204 |
| scoop fill | alpha(accent,90) between live and nominal | dx:207-216 |
| nominal (with live) | alpha(t["text"],160) 1.3 DashLine | dx:217-219 |
| live | accent 2.2 RoundCap RoundJoin | dx:220-222 |
| nominal only | accent (or t["muted"] if off) 2.0 | dx:223-227 |
| header | numeric_font("caption"), adjusted(6,3,-6,-3) Top|Left: "<freq> · gain +g dB[ → now +n dB]" / "limiter off" / "cannot be computed: …" | dx:230-243 |
| footer | adjusted(6,3,-6,-4) Bottom|Right muted "GR x dB[ (estimated)]" | dx:244-248 |

StagePanel / DrexForm layout:
| item | value | file:line |
|---|---|---|
| StagePanel | card; Expanding x Preferred; margins (12,8,12,12), spacing 8: heading (section), caption (muted, caption, wrap), [chart inserted at index 2, stretch 1], form, knob grid | dx:254-278, dx:346-348 |
| form | labels Right|VCenter, h SPACE*2 = 8, v 8, AllNonFixedFieldsGrow | dx:263-267 |
| knob grid | h 8, v 8; columns 3 (side chain 2) | dx:268-271, dx:324 |
| enable | BoolEditor text "Limiter on", above panels | dx:313-319 |
| panels row | spacing 8; stretch side chain 2, drive 3, compressor 3 | dx:320-336 |
| knob size | KNOB_SMALL_PX = 40 | dx:331 |
| compact | spin min width 0, Expanding x Fixed; combo min contents 6, Expanding x Fixed | dx:295-302 |
| side-chain | addStretch at bottom | dx:344 |

---

## 9. Multiband (mb_compr) — multiband.py
| property | value | file:line |
|---|---|---|
| FIR_FS | 96 000 | mb:35 |
| SPECTRUM_POINTS / RANGE | 180 / 20..20 000 Hz | mb:36-37 |
| FLOOR_DB | -60 | mb:38 |
| EDGE_DROP_DB | 3.0 | mb:39 |
| CURVE_IN | (-80, 0) | mb:40 |
| ROW_ORDER | threshold, ratio, attack, release | mb:41 |
| edge text | "−3 dB: up to X" / "from X" / "X – Y" / "no FIR loaded" | mb:101-111 |

FirSpectrumChart:
| property | value | file:line |
|---|---|---|
| min height | 190 | mb:139 |
| x | log; ticks 20,50,100,200,500,1k,2k,5k,10k,20k; major 100,1k,10k; minor other 1-9 decades in range | mb:140-150 |
| y | right axis, zero line; initial (-60, 6), ticks -60..6 step 12; after data: top = max(6, ceil(peak/6)*6), range (top-66, top), ticks from top-66 step 12 | mb:141-142, mb:151-152, mb:172-176 |
| note | "FIR 96 kHz" | mb:158 |
| band area | fill to bottom, alpha(band_color, 22 dimmed / 40) | mb:199-205 |
| band line | alpha(band_color, 150 dimmed / 255) width 1.8 | mb:206-208 |
| sum | t["text"] 1.6 DashLine (toggle "Sum") | mb:209-212 |
| legend | numeric caption; origin x = left+8, y = top+4; dot centre (x+4, y+7) r 4 band colour; text t["text"] baseline (x+12, y+11); y += fontHeight+1; sum swatch dashed line (x,y+7)-(x+9,y+7) | mb:215-237 |
| empty | centered muted "No FIR taps loaded: import a .txt in each band below" | mb:220-224 |

CompressorCurve (per band):
| property | value | file:line |
|---|---|---|
| min height | 150, Expanding x Expanding | mb:247-248 |
| axes | x -80..0 ticks/20, minor -70..-10; y top = max(0, ceil(g/10)*10), bottom = min(-80, -80 + floor(g/10)*10) | mb:250-252, mb:265-269 |
| diagonal | t["grid_major"] 1 DashLine | mb:305-306 |
| threshold | alpha(band colour,170) 1 DotLine | mb:308-311 |
| veil | alpha(colour,50) | mb:315-322 |
| halo / curve | alpha(ink,60) 5 / ink 2.0 RoundCap RoundJoin; ink = band colour or t["muted"] | mb:326-332 |
| knee dot | r 3.5, pen t["text"] 1.2, brush colour | mb:333-336 |
| block input line | alpha(t["ok"],170) 1.3 DashLine; triangle marker apex (x, bottom-9), base x±5 at bottom, fill ok | mb:338-350 |
| input peak | vertical tick 10 px, t["text"] 1.5 | mb:351-354 |
| working point | vertical alpha(error,150) 1.2; segment error 2.5; dot r 5.5, pen t["text"] 1.5, brush t["error"] | mb:356-367 |
| header | "r:1 · T +x dB" / "compressor off (1:1)" + " · +g dB[ Ø]" | mb:373-381 |
| footer | Bottom|Right muted lines: "GR at 0 dBFS x dB", "GR x · band y", "in x dBFS" | mb:384-398 |

BandPanel / MultibandForm layout:
| item | value | file:line |
|---|---|---|
| BandPanel | card; margins SPACE*2 = 8, spacing 8: header, curve (stretch 1), knob grid, form, FIR box | mb:409-447 |
| header | spacing 8; names VBox spacing 0: "● Band n" (section, band colour span), range (muted caption); "On" checkbox AlignTop | mb:414-425, mb:528-535 |
| knob grid | 2 per row, h 8, v 8, AlignHCenter; KNOB_SMALL_PX 40 | mb:432-434, mb:449-451, mb:541 |
| form | labels Right|VCenter, h 8, v SPACE = 4, AllNonFixedFieldsGrow | mb:427-431 |
| FIR box | spacing 4; "FIR · 100 taps" muted caption + compact TapsPanel (no chart) | mb:435-439, mb:526-527 |
| compact | spin min 0 Expanding x Fixed; combos min contents 4, popup +24 | mb:466-478 |
| top card | margins (12,8,12,8), spacing 4; head: title "Band split · FIR magnitude response" (section), note caption muted Ignored stretch 1, "Sum" checkbox checked; spectrum stretch 1; card stretch 2 | mb:498-518 |
| bands row | spacing 8, 4 panels stretch 1 each; row stretch 3 | mb:520-548 |
| gain fields | mb_gain gain/polarity added to each panel, tooltip suffix "(Multiband gain block)" | mb:552-566 |

---

## 10. Presets window — preset_window.py
| property | value | file:line |
|---|---|---|
| default size | 1320 x 640 (geometry key "presetWindow/geometry", restored/saved) | pw:252, pw:44, pw:343-345, pw:642-645 |
| title | "SpeakerNet · Presets[ · alias]" | pw:251, pw:398-399 |
| MAX_SHOWN_ISSUES | 6 | pw:45 |
| PANEL_WIDTH (min) | N 230, C 310, user sections 400 | pw:47 |
| root layout | margins: not set (style default, not determinable); spacing SPACE*3 = 12 | pw:324-325 |
| order | section_title "Speaker presets"; top Panel; columns scroll (stretch 1); Package panel | pw:326-329 |
| top panel | hardware.Panel(notches=(LEFT,RIGHT)), HBox margins 0: speaker_label, spacing 12 (literal), assignment_label (wrap, stretch 1), "Load package…", "Destination folder" (eyebrow), folder_label (muted), "Change…" | pw:261-270 |
| columns scroll | resizable, NoFrame, vertical scrollbar always off; columns HBox margins 0 (spacing default) panels stretch 1 | pw:273-285 |
| visible user sections | min(4, used + 1) | pw:410-413 |
| Package panel | Panel("Package"), VBox margins 0 spacing 8: data row, issues_label (wrap, RichText) | pw:309-322 |
| data row | eyebrow labels Device ID / Device Name / Revision / Category / Compatibility + widgets; stretch; "Export package" (primary) | pw:313-320 |
| id_edit | placeholder "1020-65535", max width 90 | pw:288-290 |
| device_name_edit | maxLength DEVICE_NAME_LENGTH[1], max width 150 | pw:291-293 |
| revision / compat spin | 0..9999 | pw:294-302 |
| category combo | "value · text" | pw:296-298 |
| issues | ok: `<span color t['ok']>The package is complete…`; else `<span color t['warn']>To export:</span>` + bullets (6 max, "… and N more") | pw:438-447 |

SectionPanel:
| item | value | file:line |
|---|---|---|
| frame | card; min width PANEL_WIDTH[section] | pw:167-168 |
| layout | QVBoxLayout default margins/spacing (not set) | pw:194 |
| title | rich "<span color SECTION_COLORS[s]>●</span>&nbsp; <b>NAME</b>", ui_font("section") | pw:170-172 |
| blocks_label | role muted "N block(s) assigned[ · row number = speakers in parallel]" | pw:173-174, pw:220-223 |
| name/summary edits | placeholders "Name"/"Summary", generic only | pw:175-182 |
| Save | primary "Save preset"; disabled with tooltip reason | pw:183, pw:224-226 |
| rows | VBox spacing 0, AlignTop in scroll (NoFrame, H scrollbar off) | pw:184-193 |

PresetRow:
| item | value | file:line |
|---|---|---|
| margins / spacing | (2,1,2,1) / 4 (literals) | pw:121-122 |
| index | fixed width 18; C rows show index+1 | pw:124-129 |
| ▲ ▼ | fixed width 24, property compact="arrow", hidden for N | pw:131-138 |
| name | "name[ · summary]", policy Ignored, min width 40, stretch 1, tooltip "N blocks" | pw:139-144 |
| Load / Rename / Delete | property compact=True; Rename only generic | pw:145-152 |
| default radio | generic only | pw:153-157 |

NameDialog: QFormLayout "Name (a-b characters)", "Summary (up to n)", message role "warning", Ok disabled while invalid (pw:64-110).

ASCII:
```
+-- PresetWindow 1320 x 640, spacing 12 (margins: style default) ---------------------------------+
| SPEAKER PRESETS (sectionTitle)                                                                   |
| [Panel notches L/R] alias · Save and Load act on …[12] assignment text (stretch) [Load package…]  |
|                     DESTINATION FOLDER  <path muted>  [Change…]                                  |
| QScrollArea (H only) -------------------------------------------------- stretch 1               |
| [card N >=230][card C >=310][card 1 >=400][card 2 >=400]…  (each stretch 1)                       |
|  ● NAME / n blocks assigned / [Name][Summary] / [SAVE PRESET] / rows: idx18 ▲24 ▼24 name… [Load][Rename][Delete] (o) |
| [Panel "Package"] DEVICE ID[<=90] DEVICE NAME[<=150] REVISION[ ] CATEGORY[ v] COMPATIBILITY[ ] <s> [EXPORT PACKAGE] |
|  8 issues (rich text)                                                                            |
+--------------------------------------------------------------------------------------------------+
```

---

## 11. Interaction summary (cross-file)
| gesture | where | effect | file:line |
|---|---|---|---|
| vertical drag on unfocused number | DragSpinBox | linear 4 px/step or log 120 px/octave; Ctrl x0.1, Shift x10; threshold 3 px | fm:89-156 |
| click (no drag) on number | DragSpinBox | focus + select all | fm:150-155 |
| wheel | all guarded editors | only with focus | fm:62-78 |
| knob drag / double-click | Knob editors | Shift fine (per tooltip); double-click types value | fm:301-311, bw:382-384 |
| EQ graph drag | EqEditor (pl) | Shift freq only, Alt gain only, Ctrl fine (hint text) | bw:475-476 |
| band chip click / dbl-click | BandStrip | select / toggle enable | bw:258-266 |
| card buttons | system grid | mouse release left | sv:451-464 |
| card drag | system grid | reorder (Custom sort, no filter) | sv:519-529, sv:643-646 |
| Esc / Alt+Left / Ctrl+B / F2 / Ctrl+S / Ctrl+Shift+S / Ctrl+O | main | up / up / sidebar / rename / save / save as / load (StandardKey) | mw:341-346, sv:695-701, mw:362-369 |
| chain card click | unit page | open chain | uv:121-123 |
| tab close hover | block window | halo alpha 50 | bw:106-125 |

## 12. Not determinable from code
- Exact header/nav/status-bar heights (depend on stylesheet + font metrics; header >= 32 + 8 + 8 = 48 px when logo shown, mw:1332, mw:1335).
- option.rect size vs gridSize in the system grid (Qt-internal).
- Default margins/spacings of LayoutDialog, NameDialog, PresetWindow root, SectionPanel, columns HBox (not set in code).
- Visual of paint_panel / paint_display / paint_pill / StatusChip / Knob / MeterPanel / EqEditor / ImpulseChart (in hardware.py, meters.py, plots.py — out of scope).
- Viewport width at startup (sidebar 200 + splitter handle + scrollbar), hence initial card columns.

## 13. Hardcoded literals
Searched all ten files for `#RGB/#RRGGBB/#AARRGGBB`, `rgb(`/`rgba(`, `QColor(<number>`, `Qt.GlobalColor`: **no literal colours found**. All colours come from `tokens()` names (accent, error, ok, warn, busy, muted, text, border, surface, elevated, field, field_border, control, meter_yellow, meter_bg, grid_major, grid_minor) or from external maps: `LIMITER_COLORS` (meters.py; sv:332, uv:187), `CATEGORY_COLORS` (chain_view.py; mw:123-124), `SECTION_COLORS` (section_badge.py; bw:153, pw:170), `band_color()` (plots.py; bw:278, mb:196, mb:300, mb:414), `text_on()` (section_badge.py; bw:154, bw:295).
Literal numeric pixel values that do not use SPACE: SliderNumberEditor row spacing 8 (fm:253); PresetRow margins (2,1,2,1) spacing 4 (pw:121-122); preset top-panel addSpacing 12 (pw:265).
Alpha values used: 70 (sv:425), 50 (bw:122), 150 (dy:141, dy:188, mb:207, mb:360), 45 (dy:154), 60 (dy:161, mb:328), 140 (dx:203), 90 (dx:215), 160 (dx:218), 22/40 (mb:204), 170 (mb:310, mb:342), 50 (mb:321).
