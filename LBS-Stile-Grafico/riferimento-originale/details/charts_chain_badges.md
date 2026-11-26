# Design-system extract: plots.py, chain_view.py, section_badge.py

Paths are relative to `C:\Users\andrea.capra\Documents\CLAUDE\SpeakerNet-main\`. `P` = speakernet/ui/plots.py, `C` = speakernet/ui/chain_view.py, `S` = speakernet/ui/section_badge.py. Tokens appear as `t["name"]` and are not resolved here. `alpha(c, N)` takes N from 0 to 255. External helpers are cited where they are used: `RADIUS_S = 6` (speakernet/ui/theme.py:43); the meters helpers are in speakernet/ui/meters.py; `paint_display` is in speakernet/ui/hardware.py:173.

---

## 1. PlotWidget (base chart)  P:39-207

**Purpose:** the base chart widget. It draws the axes, the grid, one polyline, a note and the frame. Subclasses set the scales and the labels.

**Anatomy (paint order, P:95-110):** widget bg fill → plot-area gradient bg → grid (clipped) → axis labels → `_paint_under` hook → series (if `_draw_points` and ≥2 points) → note → `_paint_over` hook → frame.

| property | value | file:line |
|---|---|---|
| Margins L,R,T,B | 40, 12, 10, 22 (`MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM`) | P:31 |
| Right margin when `_y_right` | = MARGIN_LEFT (40) | P:76 |
| Plot rect | `QRectF(left, top, max(10, w-left-right), max(10, h-top-bottom))` | P:79-82 |
| Min height | 110 | P:44 |
| Size policy | Expanding × Preferred | P:45 |
| Render hints | Antialiasing, TextAntialiasing | P:98-99 |
| Crisp-line helper | `_crisp(v) = floor(v) + 0.5` | P:34-36 |
| X mapping (log) | `fx = (log10(max(x,1e-9)) - log10(x0)) / (log10(x1) - log10(x0))` | P:87-88 |
| X mapping (lin) | `fx = (x-x0)/(x1-x0)` (0 if x1==x0) | P:90 |
| Y mapping | `fy = (y-y0)/(y1-y0)`; point = `(rect.left + fx*w, rect.bottom - fy*h)` | P:91-92 |
| Widget background | `t["surface"]` fillRect | P:101 |
| Plot bg gradient | linear, rect.topLeft→bottomLeft (vertical); stop 0.0 `t["plot_top"]`, 1.0 `t["plot_bottom"]`; NoPen; roundedRect radius RADIUS_S | P:114-119 |
| Grid clip | `setClipRect(rect)` | P:126 |
| Minor grid pen | `t["grid_minor"]`, width 1 | P:123 |
| Major grid pen | `t["grid_major"]`, width 1 | P:124 |
| X tick line pen rule | major if `_x_major` empty or value ∈ `_x_major`, else minor | P:132 |
| Y tick lines | always the minor pen | P:135-138 |
| Zero line | only if `_zero_line` and y0<0<y1; `t["zero_line"]`, width 1.2 | P:139-142 |
| Axis label font | `numeric_font("caption", self.font())` | P:145 |
| Axis label color | `t["muted"]` | P:146 |
| Y label box (left) | `QRectF(0, y-8, left-6, 16)`, AlignRight\|AlignVCenter | P:150-151 |
| Y label box (right) | `QRectF(rect.right+6, y-8, right-6, 16)`, AlignLeft\|AlignVCenter | P:152-155 |
| X label box | `QRectF(x-24, rect.bottom+4, 48, 14)`, AlignCenter; clamped to `[0, width-48]` | P:158-161 |
| Series y clamp | `min(max(y, y0), y1)` | P:167 |
| Series fill (if `_fill_to_zero` and y0≤0≤y1) | `alpha(t["accent"], 46)`, NoPen, area closed to the zero line | P:172-180 |
| Series pen | `t["accent"]`, width 1.5 | P:182 |
| Note font | `ui_font("caption", self.font())` | P:189 |
| Note color | `t["muted"]` | P:190 |
| Note box | `rect.adjusted(8,4,-8,-4)`, AlignTop\|AlignRight\|TextWordWrap | P:191-193 |
| Frame pen | `_frame_color()` = `t["plot_frame"]`, width 1, NoBrush | P:195-201 |
| Frame rect | `rect.adjusted(0.5,0.5,-0.5,-0.5)`, radius RADIUS_S | P:201 |
| Defaults | x_range (0,1), y_range (-1,1), no log, no zero line, `_draw_points=True` | P:47-59 |

**States:** none; the base widget is static.

---

## 2. ImpulseChart (FIR taps chart)  P:210-229

**Purpose:** plots the FIR taps against the tap index.

| property | value | file:line |
|---|---|---|
| Min height | 140 | P:215 |
| Fill to zero | True (`alpha(t["accent"],46)`) | P:216, P:179 |
| Zero line | True | P:217 |
| Y top | `1.0 if peak>0.5 else max(peak*1.1, 0.05)`; range (-top, top) | P:222-224 |
| X range | (0, max(n-1,1)) | P:223 |
| X ticks | `_nice_ticks(n-1)`, labels = str(i) | P:225 |
| `_nice_ticks` | step=10^max(0,floor(log10(last))); factor ∈ (1,2,5), first with last/(step·f) ≤ 6, else ×10; range(0,last+1,step); last≤0 → [0] | P:1288-1298 |
| Y ticks | (-top,"{:.2g}"), (-top/2,""), (0,"0"), (top/2,""), (top,"{:.2g}") | P:226-227 |
| Note text | `f"{n} taps · peak {peak:.4g}"` | P:228 |

---

## 3. EqChart (EQ response, read-only)  P:232-310

| property | value | file:line |
|---|---|---|
| `EQ_NOTE` | "RCF coefficients, 96 kHz" | P:232 |
| `EQ_TOP_DB` | 18.0 | P:233 |
| `EQ_TOP_MAX_DB` | 36.0 | P:234 |
| `EQ_SCALES` | (6.0, 12.0, 18.0, 24.0) (fixed-scale buttons besides Auto) | P:235 |
| `EQ_LABELED` | 20,50,100,200,500,1k,2k,5k,10k,20k | P:236-237 |
| X axis | log, 20–20 000 Hz | P:245, P:248 |
| Zero line / right Y labels | True / True | P:246-247 |
| Major x lines | {100, 1000, 10000} | P:250 |
| Minor x lines | m·10^d for d∈{1..4}, m∈1..9, 20≤f≤20000, excluding labelled values | P:252-253 |
| Y tick step | 3 if top≤12; 6 if top≤24; else 12 | P:262 |
| Y ticks | k·step for k∈[-n..n], n=round(top/step); label `f"{v:+g}"`, "0" at k=0 | P:263-264 |
| Auto scale | `top = min(36, max(18, ceil((peak+1)/6)*6))` | P:285 |
| Scale freeze | skipped while `_frozen` (drag) or a fixed scale is set | P:282 |
| Error note | "cannot be computed: " + message; points cleared | P:289-290 |
| `curve_db_at` | log-frequency linear interpolation; clamps to the first/last point | P:297-310 |

---

## 4. EqEditor (interactive EQ curve editor)  P:436-1285

**Purpose:** the interactive EQ curve. Each band has a coloured curve and a draggable node. The selected band gets Q diamonds; disabled bands appear as ghost points. Also: value label with inline edit, crosshair, dynamic-EQ overlay, legend and empty-state text.

**Anatomy (z-order: draw order inside paint):**
1. PlotWidget bg + grid (§1)
2. `_paint_under`: dotted vertical guide of the focus band, then `_paint_curve` (per-band areas/lines → dynamic "dig" areas → total curve) P:1054-1060
3. (series skipped: `_draw_points=False` P:457)
4. note
5. `_paint_over`: Q handles → ghosts (if editable) → nodes → value label → crosshair → dynamic legend (if `dynamic_source`) → empty-state text P:1269-1285
6. frame (focus-aware)

### Constants
| property | value | file:line |
|---|---|---|
| Min height | 260 | P:456 |
| Mouse tracking / focus policy | True / ClickFocus | P:458-459 |
| `BAND_COLORS` | #3987e5, #d95926, #199e70, #c98500, #d55181, #2aa52a, #9085e9, #e66767 | P:347-348 |
| `band_color(i)` | `BAND_COLORS[i % 8]` | P:361-362 |
| `band_dashed(i)` | `i >= 8` → DashLine | P:365-366 |
| `HANDLE_R` | 9.0 | P:349 |
| `OFF_R` | 6.5 | P:350 |
| `Q_HANDLE_R` | 5.0 | P:351 |
| `PICK_PX` | 14.0 | P:352 |
| `Q_WHEEL_FACTOR` | 1.12 | P:353 |
| `FINE_FACTOR` | 10.0 | P:354 |
| `GHOST_CLUSTER_PX` | 12.0 | P:355 |
| `GAIN_STEP_DB, GAIN_FINE_DB` | 0.5, 0.1 | P:356 |
| `FREQ_STEP_OCT, FREQ_FINE_OCT` | 1/12, 1/48 | P:357 |
| `DYNAMIC_MIN_DB` | 0.05 | P:358 |
| `Q_TYPES` | {0, 9} (peak, all-pass) | P:342 |
| BandPoint defaults | freq_range (20,20000), gain_range (-30,15), q_range (0.1,20) | P:322-324 |
| slope dB/oct | `(order+1)*6` when not uses_q | P:339 |

### Formatting / maths
| property | value | file:line |
|---|---|---|
| `format_freq` | ≥10k `{f/1000:.1f} kHz`; ≥1k `{:.2f} kHz`; ≥100 `{:.0f} Hz`; else `{:.1f} Hz` | P:369-374 |
| `short_freq` | ≥10k `{:.0f}k` if f%1000==0 else `{:.1f}k`; ≥1k `{:.2g}k` if f%100==0 else `{:.2f}k`; else `{:.0f}` if f≥100 or integer, else `{:.1f}` | P:377-383 |
| `round_freq` | step 0.1 (<100), 1 (<1000), 10; `round(round(f/step)*step, 1)` | P:386-389 |
| `q_edge_ratio(q)` | a=1/(2q); `sqrt(1+a²)+a` | P:392-395 |
| `q_from_ratio(r)` | r=max(r,1.0001); `1/(r - 1/r)` | P:398-401 |
| `parse_value` | lowercase; "," → "."; "−" → "-"; units khz(×1000)/hz/db; trailing "k" for freq (×1000); leading "q" for q; non-finite → None | P:404-421 |
| Gain clamp/round | clamp to gain_range, round to 1 decimal | P:647 |
| Q clamp/round | clamp to q_range, round to 3 decimals | P:651 |
| Handle pos | `_map(plot_rect, clamp(freq), clamp(gain))` | P:573-576 |
| Q handle pos | x at `freq·ratio` (side +1) or `freq/ratio` (side −1), clamped to x_range; y = node y | P:578-582 |
| Inverse mapping | `freq = 10^(lo + fx(hi-lo))`, `gain = y0 + fy(y1-y0)` | P:584-591 |

### Per-band curves  P:976-1000
| property | value | file:line |
|---|---|---|
| Clip | plot rect | P:981 |
| Draw order | non-focus bands first, focus band last (`sorted(key=i==focus)`) | P:985 |
| "lit" | focus is None or index == focus | P:990 |
| Area fill (to 0 dB) | `alpha(color, 64)` focus / `30` lit / `14` dimmed; NoPen | P:992-994 |
| Line pen colour | `alpha(color, 255)` lit / `110` dimmed | P:995 |
| Line pen width | 2.0 focus / 1.2 others | P:995 |
| Line style | DashLine if index ≥ 8 | P:996-997 |

### Dynamic-EQ overlay  P:1001-1029
| property | value | file:line |
|---|---|---|
| Active band | abs(gain) ≥ 0.05 and enabled | P:507-510 |
| Area between static and live curves | `alpha(color, 120)`, NoPen | P:1015-1017 |
| Live band line | `color`, width 2.2, SolidLine, RoundCap, RoundJoin | P:1019-1021 |
| Nominal total (when live) | `alpha(t["text"],150)`, width 1.2, DashLine | P:1027 |
| Live total | drawn with the `_paint_total` style using `dynamic_total` | P:1029 |

### Total curve  P:1032-1052
| property | value | file:line |
|---|---|---|
| Area gradient | vertical rect.topLeft→bottomLeft; 0.0 `alpha(t["text"],40)`; at `clamp((zero-top)/h,0,1)` `alpha(t["text"],4)`; 1.0 `alpha(t["text"],40)` | P:1037-1041 |
| Halo pass 1 | `alpha(t["text"],22)`, width 7.0, RoundCap, RoundJoin | P:1046-1049 |
| Halo pass 2 | `alpha(t["text"],46)`, width 4.0, RoundCap, RoundJoin | P:1046-1049 |
| Main line | `t["text"]`, width 2.2, SolidLine, RoundCap, RoundJoin | P:1050-1052 |

### Focus guide line  P:1054-1059
| property | value | file:line |
|---|---|---|
| Focus band | first enabled of: dragged → hovered → selected | P:954-959 |
| Guide | vertical full-height at the node x; `alpha(band_color,170)`, width 1, DotLine | P:1058-1059 |

### Q handles (diamonds)  P:1062-1082
| property | value | file:line |
|---|---|---|
| Shown when | selected band is enabled and `uses_q` | P:1065 |
| Connector | left↔right line `alpha(color,200)`, width 1.2, DashLine | P:1069-1070 |
| Diamond r | `Q_HANDLE_R + 1.5` if hot else `Q_HANDLE_R` (5.0) | P:1073 |
| Diamond shape | (0,-r-1), (r,0), (0,r+1), (-r,0) | P:1077-1081 |
| Outline | `t["text"]`, width 1.6 hot / 1 normal | P:1074 |
| Fill | band colour | P:1075 |
| Hot | hovered side, or the side being dragged | P:1072 |

### Ghosts (disabled bands)  P:605-628, P:1084-1102
| property | value | file:line |
|---|---|---|
| Y position | 0 dB line (or rect centre if 0 is not in range) | P:609-610 |
| Clustering | x-distance < 12 px merges; group index = lowest band index | P:615-620 |
| Pick radius | `OFF_R + 4` (10.5) | P:626 |
| Font | `numeric_font("caption")` | P:1087 |
| Circle | radius OFF_R 6.5; fill `t["plot_bottom"]`; pen width 1.4, `t["text"]` hot / `t["control"]` normal | P:1092-1094 |
| Number | `t["text"]` hot / `t["muted"]` normal; centred | P:1095-1097 |
| "+n" text | `t["muted"]`, box `(x+OFF_R+2, y-8, 28, 16)`, AlignLeft\|VCenter | P:1098-1102 |
| Hot | hovered ghost, or the selected band is in the group | P:1091 |
| Drawn only if | `editable` | P:1272-1273 |

### Nodes (enabled bands)  P:1104-1146
| property | value | file:line |
|---|---|---|
| Font | `numeric_font("caption")`, setBold(True) | P:1106-1107 |
| Z-order | sort key (is_hover, is_selected): selected on top, then hovered | P:1109-1110 |
| Dynamic marker line | node → live-gain point; `alpha(color,220)`, width 1.4, DashLine | P:1121-1122 |
| Dynamic marker dot | radius 5.0; pen `color` width 2.0; fill `t["plot_bottom"]` | P:1123-1125 |
| Node fill | band colour, radius HANDLE_R 9.0 | P:1142-1143 |
| Node outline | `t["plot_bottom"]`, width 1.5 | P:1141 |
| Node number | `text_on(color.name())` (#000000 or #ffffff), centred in 2·HANDLE_R box | P:1144-1146 |

### Value label (readout)  P:1148-1213
| property | value | file:line |
|---|---|---|
| Fields | freq (`format_freq`); gain `{:+.1f} dB` (not if fixed_gain); live `live {:+.1f} dB` / `live —`; `Q {:.2f}` or `{n} dB/oct` | P:1148-1159 |
| Font | `numeric_font("body")`, setBold(True) | P:1171-1172 |
| Separator | "  ·  " | P:1175 |
| Swatch | diameter 10, filled with band colour, NoPen, at `left+pad_x+5` | P:1176, P:1189-1192 |
| Padding | pad_x 8, pad_y 4 | P:1177 |
| Width | `2·8 + 10 + 6 + Σtext + sep·(n-1)` | P:1178-1179 |
| Height | `metrics.height() + 8` | P:1180 |
| Position | centred above the node: `y = p.y - HANDLE_R - 10 - h`; flips below (`p.y + HANDLE_R + 10`) if top < rect.top+2; x clamped to [rect.left+2, rect.right-w-2] | P:1182-1185 |
| Border | `alpha(color,220)`, width 1 | P:1186 |
| Fill | `alpha(t["elevated"],238)`, radius RADIUS_S | P:1187-1188 |
| Text colour | freq/gain/q: `t["text"]`; slope/live: `t["muted"]`; live when the band is active: band colour; separators: `t["muted"]` | P:1198-1211 |
| Hit areas | freq/gain/q, each `part.adjusted(-3,0,3,0)` | P:1205-1206 |

### Inline value editor  P:424-433, P:906-946
| property | value | file:line |
|---|---|---|
| Widget | QLineEdit, AlignCenter | P:479-481 |
| Font | `numeric_font("body")` | P:914 |
| Geometry | width `max(part.w+24, 72)`, height 24, centred on the part, x clamped to the widget | P:915-918 |
| Initial text | freq `{:g}`, gain `{:+.1f}`, q `{:.3g}`; selectAll | P:912, P:919-920 |
| Keys | Enter/editingFinished → commit; Esc → cancel | P:428-433, P:482-483 |

### Crosshair  P:1237-1267
| property | value | file:line |
|---|---|---|
| Shown when | `crosshair` on, mouse inside the plot rect, not dragging, not hovering a node | P:1240-1241 |
| Lines | `alpha(t["text"],90)`, width 1, DashLine; crisp x/y | P:1244-1248 |
| Text | `"{format_freq}  {gain:+.1f} dB"` + `"  ·  curve {:+.1f} dB"` | P:1250-1253 |
| Font | `numeric_font("caption")` | P:1254 |
| Box | `(pos+12, pos+12, textW+12, fontH+6)`; flips left/up by 12 if it overflows | P:1257-1262 |
| Box pen / fill | `t["field_border"]` w1 / `alpha(t["elevated"],235)`, radius RADIUS_S | P:1263-1265 |
| Text colour | `t["text"]`, AlignCenter | P:1266-1267 |

### Dynamic legend  P:1215-1235
| property | value | file:line |
|---|---|---|
| Position | x = rect.left+10, y = rect.bottom-10 | P:1222-1223 |
| Font | `numeric_font("caption")` | P:1218 |
| Items | DashLine "nominal", SolidLine "live (unit gain reduction)" | P:1224-1225 |
| Swatch line | length 16; `alpha(t["text"], 80)` if dashed and inactive, else 200; width 1.6 | P:1227-1229 |
| Text | `t["muted"]` at x+20; advance `20 + textW + 14` | P:1230-1232 |
| Inactive suffix | "· no dynamic action", `t["muted"]` | P:1233-1235 |

### Empty state / frame / tooltip
| property | value | file:line |
|---|---|---|
| Empty text | "All bands are off: double-click the graph, click a grey point or press “Add band”"; `ui_font("body")`, `t["muted"]`, `rect.adjusted(8,6,-8,-6)` top-left | P:1279-1285 |
| Frame when focused | `alpha(t["accent"],170)` (else `t["plot_frame"]`) | P:949-952 |
| Widget tooltip | multi-line help text | P:563-570 |

### States
| state | visual | file:line |
|---|---|---|
| node normal | fill colour, outline `t["plot_bottom"]` 1.5 | P:1141-1143 |
| node hover | + ring r=HANDLE_R+3, `alpha(t["text"],150)` w1.4 | P:1137-1140 |
| node selected | + halo r=HANDLE_R+7 `alpha(color,70)` + ring r=HANDLE_R+3 `t["text"]` w2.0 | P:1130-1136 |
| curve focus / lit / dim | see per-band curves table | P:993-995 |
| Q handle hot | r+1.5, outline w1.6 | P:1073-1074 |
| ghost hot | outline/number `t["text"]` | P:1092-1095 |
| widget focused | frame `alpha(accent,170)` | P:951 |
| not editable | arrow cursor; no ghosts; no edits | P:783-784, P:1272 |
| disabled band | ghost on 0 dB | §ghosts |

### Interaction
| input | effect | file:line |
|---|---|---|
| LMB press on Q handle (≤ PICK_PX-3 = 11 px) | start Q drag, SizeHorCursor | P:637, P:735-740 |
| LMB press on node (< PICK_PX = 14; ties ±0.5 go to the selected node) | select + drag | P:593-603, P:741-748 |
| LMB press on ghost | `switch_on` (re-enable + select) | P:752-754 |
| Drag | virtual pos = anchor + delta; Ctrl → delta/10 (re-anchors on toggle) | P:707-720 |
| Drag + Shift | frequency only (SizeHorCursor) | P:770-771, P:723-724 |
| Drag + Alt | gain only (SizeVerCursor) | P:772-773, P:725-726 |
| Drag (no modifier) | ClosedHandCursor | P:727 |
| Q drag | `q = q_from_ratio(f/f0 or f0/f)` | P:766-769 |
| Release | unfreeze, OpenHandCursor, refit the auto scale | P:797-803 |
| Hover cursors | Q handle SizeHor; node OpenHand; ghost/label PointingHand; else Cross | P:783-794 |
| Double-click node | switch band off | P:809-812 |
| Double-click label value | inline edit | P:813-816 |
| Double-click empty | `add_band(freq, gain)` at the cursor (first disabled band) | P:819-834 |
| Wheel | Q ×= 1.12^(angleDelta.y/120) on the hovered (else selected) band | P:836-845 |
| Tab / Shift+Tab | next/prev enabled band by frequency (wraps) | P:686-696, P:855-859 |
| ←/→ | ±1/12 oct (Ctrl ±1/48); if rounding absorbs the change, step 0.1/1/10 Hz | P:865-873 |
| ↑/↓ | ±0.5 dB (Ctrl ±0.1) | P:879-881 |
| Shift+↑/↓ | Q ×/÷ 1.12 (uses_q only) | P:876-878 |
| Del / Backspace | switch off | P:882-883 |
| Leave | clear hover and mouse | P:889-891 |
| Signals | `band_edited(int, dict)`, `band_selected(int)` | P:451-452 |
| Animations | none | n/a |

---

## 5. Chain graph: layout constants  C:56-81

| property | value | file:line |
|---|---|---|
| `BLOCK_W, BLOCK_H` | 120, 80 | C:56 |
| `GAP_X, ROW_GAP` | 24, 26 | C:57 |
| `COMBO_H` | 20 | C:58 |
| `SUM_W` | 28 | C:59 |
| `MARGIN` | 14 | C:60 |
| `HEAD_W` | 150 | C:61 |
| `LANE_PAD` | 10 | C:62 |
| `LANE_H` | `LANE_PAD + BLOCK_H + ROW_GAP + 6` = 122 | C:63 |
| `LANE_SPACING` | 6 | C:64 |
| `SPLIT_GAP` | 30 | C:65 |
| `HEADER_H` | 22 | C:66 |
| `MAX_SCALE` | 1.6 | C:67 |
| `LOD_DETAIL` | 0.5 | C:68 |
| `LOD_BARS` | 0.3 | C:69 |
| `SCREEN_FONT_PT` | 7.5 | C:70 |
| `LABEL_H` | 30 | C:71 |
| `LABEL_LEFT` | 25 | C:72 |
| `ICON_PX` | 13 | C:73 |
| `METER_ROW_H` | 11 | C:74 |
| `CARD_R` | 8 | C:75 |
| `CABLE_R` | 6 | C:76 |
| `PREVIEW_POINTS` | 48 | C:77 |
| `CATEGORY_COLORS` | USER #5cc76e, USER_PRESET #9fc3e6, PRESET_DEFINED #e8a655, HARDCODED #8a8c92 | C:78-79 |
| `LEGEND` | User / "User, set by preset" / Preset / Fixed | C:80-81 |
| `COLUMN_NAMES` | resource → short header (MUTE, GAIN, U-EQ, A-FIR, SENS, DELAY, CW-EQ, AIR, ML-FIR, BASS, DYN-EQ, DREX, PH-DLY, F-EQ, MB-C, MB-G, OUT-G, LIM, COMP, LPF, HPF, HF-C, PROT, Σ, IN, OUT); fallback `k[:5].upper()` | C:239-246, C:400 |

### Layout formulas (`layout_chain`)  C:295-407
| property | value | file:line |
|---|---|---|
| scale floor | max(scale, 0.05) | C:303 |
| head_w | `max(150, (max bold screen-font label width + 24)/scale)` | C:308-309 |
| lane_pad | `max(10, 16/scale)` | C:310 |
| header_h | `max(22, 18/scale)` | C:311 |
| lane_h | `lane_pad + 80 + 26 + 6` | C:312 |
| column step | `BLOCK_W + GAP_X` = 144 | C:313 |
| left | `MARGIN + head_w` | C:314 |
| node x | `left + col*step + (BLOCK_W-SUM_W)/2` (the last term only for SUM) | C:324 |
| node y | `lane_y + lane_pad` | C:339, C:365 |
| split bus y | `y + lane_h + SPLIT_GAP/2 - 4` | C:350 |
| empty slot | `QRectF(left+col*step+10, lane_y+lane_pad+BLOCK_H/2-12, BLOCK_W-20, 24)` | C:376-377 |
| branch sub-lane y | `lane_y + lane_h*(b+1)` | C:380 |
| order numbers | common 1..n; way continues n+1..; branches base + "a".."h" | C:345, C:369, C:386 |
| lane rect width | `content_w + LANE_PAD`, content_w = `head_w + cols*step - GAP_X` | C:397-399 |
| column header x | `left + c*step + BLOCK_W/2` | C:400 |
| scene size | `(MARGIN + content_w + LANE_PAD + MARGIN, y - LANE_SPACING + MARGIN)` | C:402 |
| lane titles | "WAY n · name"; "INPUT · COMMON"/"{k} blocks, {which}"; copy: "INPUT · COMMON · WAY n"/"copy of WAY 0, {which}"; sub "OUT {x}" | C:285-292, C:389-392 |

---

## 6. EdgeItem (cables)  C:410-452, C:1220-1257

**Anatomy:** a QGraphicsPathItem (orthogonal polyline with rounded corners) plus a child arrow-head path item.

| property | value | file:line |
|---|---|---|
| Start / end | `pa + (node_width(a), BLOCK_H/2)` / `pb + (0, BLOCK_H/2)` | C:419-420 |
| Straight | if |Δy|<1 and end.x ≥ start.x | C:421-422 |
| Gap column x | `start.x + GAP_X/2` | C:423 |
| Split route | via gap_x → split_y → bus_x=`MARGIN+head_w-GAP_X/2-2` → end.y | C:424-427 |
| Branch return into SUM | ends at `pb + (SUM_W/2, BLOCK_H/2+14)`; rise y = `pb.y + lane_h - lane_pad - 4` | C:428-432 |
| Corner rounding | quadTo; r = `min(CABLE_R=6, d1/2, d2/2)`; r < 0.5 → sharp | C:436-452 |
| Arrow head | triangle end, end+(-7,-4), end+(-7,4); NoPen; brush = cable colour | C:1232-1238, C:1251 |
| Colour normal (multi-way) | `alpha(BAND_COLORS[way%8], 200)` | C:1245-1246, C:1520 |
| Colour normal (single/common) | `t["cable"]` | C:1248 |
| Colour hot | `t["cable_hot"]` | C:1243-1244 |
| Width | 1.6 normal / 2.2 hot | C:1249 |
| Cap / join | RoundCap / RoundJoin, SolidLine | C:1249-1250 |
| Z | -1 normal / -0.5 hot | C:1252 |

| state | visual | file:line |
|---|---|---|
| normal | way colour α200 or `t["cable"]`, w1.6, z -1 | C:1245-1252 |
| hot (path of the hovered node's way) | `t["cable_hot"]`, w2.2, z -0.5 | C:1243-1252 |

Hot rule: both endpoints in the union of the ancestor sets of every output whose path contains the hovered node (C:1643-1652). Cleared on view leave (C:1758-1760).

---

## 7. Card base `_paint_card` (shared by Block, Protection, IO)  C:743-766

| property | value | file:line |
|---|---|---|
| Shadow (lod ≥ 0.5) | 2 passes, NoPen: dy 3.0 `alpha(t["shadow"],60)`; dy 1.5 `alpha(t["shadow"],80)`; same radius | C:748-752 |
| Selected halo | NoBrush: width 8.0 `alpha(t["accent"],45)`; width 4.5 `alpha(t["accent"],90)` | C:753-757 |
| Relief fill (relief and lod ≥ 0.5) | vertical gradient topLeft→bottomLeft: 0.0 `fill.lighter(116)`, 1.0 `fill.darker(108)` | C:759-763 |
| Flat fill | `fill` (relief off or lod < 0.5) | C:765 |
| Radius default | CARD_R 8 | C:744 |

---

## 8. BlockItem (block tile)  C:885-1092

**Anatomy:** shadow → (halo) → card → icon → label (2 lines) → section badge → LED → pending corner → meters → preview; child SectionSelector below the card.

| property | value | file:line |
|---|---|---|
| Size | 120×80; boundingRect (-6,-6,132,92) | C:935-936, C:996 |
| Flags | selectable, hover events, PointingHandCursor | C:891-893 |
| Border colour | `CATEGORY_COLORS[category]` | C:910 |
| Fill | `SECTION_COLORS[section]` if assignable+section; else `t["surface"]` (has_data) / `t["alt"]` (no data) | C:938-944 |
| Ink on section fill | `text_on(fill.name())` (#000000/#ffffff) | C:1008 |
| Text colour | ink, else `t["text"]` (has_data) / `t["muted"]` | C:1009 |
| Relief | off when assignable+section (flat fill) | C:1007 |
| Pen | normal: category colour w1.6; selected: `t["accent"]` w2.4; DUP → DashLine | C:1003-1005 |

**Detail LOD (lod ≥ 0.5):**
| part | value | file:line |
|---|---|---|
| Icon | rect (8,6,13,13); colour ink or `t["muted"]` | C:1026 |
| Label rect | (25, 5, BLOCK_W-25-18=77, 30); right edge −16 if badge | C:1027-1029 |
| Label font | painter font, setPointSizeF 8.0 (lod≥0.5) / 11.0, setBold(True), italic if DUP | C:727-732 |
| Label wrap | WordWrap, AlignLeft\|Top; if overflow → elide right to `width*2-8` | C:735-740 |
| Badge | rect (right-26=82, 5, 15, 14) | C:1030 |
| LED | centre (108, 12) scale 1 | C:1078 |
| Meters | left 8, top `max(BLOCK_H-6-11·n, LABEL_H+4)`, width BLOCK_W-14 | C:1036-1039 |
| Preview | rect (9, LABEL_H+7=37, BLOCK_W-20, bottom-top); bottom = meters_top-2 or BLOCK_H-7 | C:1040-1044 |

**Compact LOD (lod < 0.5):**
| part | value | file:line |
|---|---|---|
| Icon | rect (BLOCK_W/2-18, 14, 36, 34); colour ink or text colour | C:1014-1015 |
| Badge | (8,6,22,20), scale 1.6 | C:1016-1017 |
| LED | scale 1.6 → centre (120-19.2, 19.2) | C:1018, C:1078 |
| Meters (lod ≥ 0.3) | last 2 meters, bars only: left 10, top `BLOCK_H-8-11·k`, width BLOCK_W-20 | C:1021-1024 |
| Label / preview | not drawn | C:1011-1025 |

**Pending corner** C:1046-1056: path (W-16,H) → (W-CARD_R,H) quad via (W,H) → (W,H-CARD_R) → (W,H-16) close; size 16; fill ink or `t["accent"]`; NoPen.

**Badge** C:1058-1072: roundedRect radius 3, fill = ink; letter in `SECTION_COLORS[section]`, font `numeric_font("caption")` bold, pointSize × scale, centred.

**LED** C:1074-1092:
| condition | visual | file:line |
|---|---|---|
| led None and not muted | not drawn | C:1076-1077 |
| on section fill, not muted | ring pen ink w`1.6·scale`, r `4.2·scale`; filled with ink if led else NoBrush | C:1079-1085 |
| muted | `paint_led(t["error"], r 4.5·scale)` | C:1086-1087, C:1092 |
| led on | `paint_led(t["ok"])` | C:1088-1089 |
| led off | `paint_led(t["button_disabled"])` | C:1090-1091 |
| paint_led | halo `alpha(color,60)` r+2; disc pen `t["border"]` w1 | speakernet/ui/meters.py:266-276 |

**States**
| state | visual | file:line |
|---|---|---|
| normal | fill as above, border category w1.6 | C:1003 |
| hover | fill.lighter(112) if section else lighter(125); emits path highlight | C:1001-1002, C:981-989 |
| selected | border `t["accent"]` w2.4 + yellow halo | C:1003, C:753-757 |
| muted | fill `t["mute_fill"]` (overrides hover); LED `t["error"]` | C:999-1000 |
| no data | fill `t["alt"]`, text `t["muted"]` | C:944, C:1009 |
| DUP (duplicate) | DashLine border, italic label | C:1004-1005, C:1032 |
| pending (offline edits) | corner triangle accent/ink | C:1019-1020, C:1034-1035 |
| assigned section | flat fill = section colour, ink text/icons, badge | C:941-942, C:1007-1008 |
| warning | stored (C:899, C:961) but not painted in this file | n/a |

**Tooltip** C:922-933: `<b>{label}</b><br>way {w} · {CATEGORY_TEXT}` + DUP copy/dsp lines + "Preset section: X (right-click to change)" + "Click to open its parameters".

---

## 9. Tile meters `_paint_meters`  C:690-724

| property | value | file:line |
|---|---|---|
| Font | `numeric_font("caption")`, setPointSizeF 7.5, bold False | C:699-702 |
| Value column width | 30 (numbers) / -3 (bars only) | C:703 |
| Bar rect | `(left, y+2.5, width-value_w-3, 6 or 8 if bars-only)` | C:708 |
| Row pitch | METER_ROW_H 11 | C:711, C:724 |
| Value text box | `(left+width-value_w, y-1, value_w, 11)`, AlignRight\|VCenter | C:721-723 |
| Value colour (no ink) | `t["error"]` if GR > 0.05 else `t["muted"]` | C:713, C:720 |
| Value colour (ink) | ink; bold when GR is active | C:714-718 |
| Value text | "—" None; GR `{:.1f}`; level "-inf" ≤ -60 else `{:.1f}` | speakernet/ui/meters.py:64-69 |
| Bar track | `t["deep"]`, radius min(h,w)/2 | speakernet/ui/meters.py:206-210 |
| Level fill | horizontal gradient: `t["ok"]` → `t["meter_yellow"]` at -12 dB → `t["error"]` at -3 dB, blend 0.025; range -60..0 | speakernet/ui/meters.py:101-113 |
| GR fill | `t["error"]`, right→left, full at 24 dB | speakernet/ui/meters.py:29, 222-224, 230 |
| Peak tick | 2 px wide, level colour / `t["error"]` | speakernet/ui/meters.py:244-252 |
| Level ticks | -12 and -3 dB, `t["meter_tick"]` w1 | speakernet/ui/meters.py:253-262 |
| Animation | timer 33 ms; release 30 dB/s; peak hold 1.2 s, then 18 dB/s; dt capped at 0.2 s | speakernet/ui/meters.py:36-39, 304 |

---

## 10. Block icons `icon_path` / `paint_icon`  C:459-583

| property | value | file:line |
|---|---|---|
| Pen | colour, width 1.4, SolidLine, RoundCap, RoundJoin | C:579-580 |
| Fill | `alpha(color,70)` only for "gain"; others NoBrush | C:573, C:581 |
| Kind mapping | xover_hpf→hpf, xover_lpf→lpf, *_eq/fact_dynpeq/bass_shaper→eq, *_fir→fir, *_delay→delay, *_mute→mute, *_lim→limiter, *compr*→compressor, *_gain→gain, else generic | C:459-480 |
| eq | bell: (0,.75) cubic (.3,.75)(.35,.1)(.5,.1); cubic (.65,.1)(.7,.75)(1,.75) | C:491-494 |
| hpf | (0,1) cubic (.25,.6)(.35,.25)(.55,.25), line (1,.25) | C:495-498 |
| lpf | (0,.25)→(.45,.25) cubic (.65,.25)(.75,.6)(1,1) | C:499-502 |
| gain | triangle (.1,.05)(.95,.5)(.1,.95) closed | C:503-507 |
| delay | ellipse rect.adjusted(.5,.5,-.5,-.5) + hands (.5,.2)→(.5,.5)→(.75,.62) | C:508-512 |
| limiter | ceiling (0,.15)-(1,.15) + wave (0,.9)(.2,.3)(.4,.3)(.55,.9)(.7,.3)(.9,.3)(1,.6) | C:513-522 |
| compressor | (0,1)→(.5,.45) quad (.6,.35)→(1,.2); axes (0,0)→(0,1)→(1,1) | C:523-529 |
| fir | stems at x .1/.35/.6/.85 to y .55/.1/.4/.65, dots r 1.3; baseline (0,1)-(1,1) | C:530-536 |
| mute | speaker (0,.35)(.2,.35)(.45,.1)(.45,.9)(.2,.65)(0,.65) closed + X (.65–.95, .35–.65) | C:537-548 |
| shield | (.5,0)(.95,.18) cubic (.95,.6)(.75,.85)(.5,1) cubic (.25,.85)(.05,.6)(.05,.18) closed | C:549-554 |
| in / out | bar x .15/.85; arrow base .4/.05 → tip .95/.7 at y .5; head (tip-.28, .22/.78) | C:555-565 |
| generic | square wave (0,.75)(.25,.75)(.25,.25)(.6,.25)(.6,.75)(1,.75) | C:566-572 |

---

## 11. Block preview `_paint_preview`  C:590-679

| property | value | file:line |
|---|---|---|
| Skip if | rect h < 10 or w < 20 | C:642-643 |
| Curve dB top | `ceil(max(6, max|d|)/6)*6` | C:646-647 |
| X map | log10, 20–20 000 | C:648-652 |
| Y map | `fy = 0.5 - clamp(d,-top,top)/(2·top)` | C:652 |
| Zero line | rect centre y; `alpha(ink,60)`, w1, DotLine | C:655-657 |
| Area | `alpha(ink,40)`, NoPen, to the zero line | C:662-668 |
| Line | ink, width 1.4 | C:669 |
| Text preview font | `numeric_font("display")`, pointSizeF `min(current, max(7.0, rect.h·0.62))` | C:673-674 |
| Text align | AlignLeft\|VCenter, ink | C:676-678 |
| Text formats | gain `{:+.1f} dB` (+ " Ø" if polarity); delay `{:.2f} ms`; error "n/a" | C:627, C:634, C:637 |
| Points | 48 (log frequencies) | C:77, C:623 |

---

## 12. SectionSelector (preset-section dropdown under a tile)  C:769-873

| property | value | file:line |
|---|---|---|
| Position | (8, BLOCK_H+3) relative to the block | C:776 |
| Size | (BLOCK_W-16=104) × COMBO_H 20 | C:799-800 |
| Cursor | PointingHandCursor | C:778 |
| Visible | only when session and block are set | C:785, C:790 |
| Box | rect.adjusted(.5,.5,-.5,-.5), radius 4 | C:857 |
| Box pen | `t["field_hover"]` hover / `t["field_border"]`, w1 | C:855 |
| Box fill | `t["elevated"]` hover / `t["field"]` | C:856 |
| Colour strip | (0.5,0.5,5,h-1), radius 2, `SECTION_COLORS[section]` or `t["warn"]` if unassigned | C:796-797, C:858-860 |
| Text | font = painter font, pointSizeF 8, bold; `t["text"]`; rect (10,0,w-28,h); section letter or "–" | C:861-868 |
| Chevron | polyline c+(-3.5,-1.5), c+(0,2), c+(3.5,-1.5), c=(w-11, h/2); `t["muted"]` w1.4 RoundCap RoundJoin | C:870-873 |
| Tooltip | `Preset section: {name}<br>Click to change` (unassigned → "not assigned") | C:791-792 |

| state | visual | file:line |
|---|---|---|
| normal | field fill, field_border | C:855-856 |
| hover | elevated fill, field_hover border | C:855-856 |
| pressed | `_pressed` flag only; no visual | C:841 |
| unassigned | strip `t["warn"]`, text "–" | C:797, C:868 |

Interaction: the menu opens on LMB release inside the bounds (button semantics), after ungrabMouse (C:835-848). The QMenu is anchored at the bottom-left corner (C:820-821). An outside click is swallowed by OutsideClickGuard (§17).

---

## 13. SumItem  C:1095-1112

| property | value | file:line |
|---|---|---|
| Bounds | (0, BLOCK_H/2-14, 28, 28) | C:1101-1102 |
| Circle | centre (14, 40), r 12 | C:1109-1110 |
| Pen | `t["control"]`, w1.6 | C:1107 |
| Fill | `t["field"]` | C:1108 |
| Plus sign | ±6 px horizontal and vertical | C:1111-1112 |
| Tooltip | "Sum of the two branches" | C:1099 |
| States | none | n/a |

---

## 14. ProtectionItem  C:1115-1139

| property | value | file:line |
|---|---|---|
| Card | 120×80, fill `t["alt"]`, border `CATEGORY_COLORS[HARDCODED]` (#8a8c92) w1.4, never selected, radius 8 | C:1132-1133 |
| Compact icon | shield (BLOCK_W/2-15, 18, 30, 34), `t["muted"]` | C:1134-1136 |
| Detail icon | shield (8,6,12,13), `t["muted"]` | C:1137 |
| Label | "Amplifier protections", rect (25,5,87,30), `t["muted"]`, `_paint_label` font | C:1138-1139 |
| Tooltip | "Amplifier protections, fixed in the firmware: …" | C:1121-1122 |

---

## 15. IoItem (input / output tile)  C:1142-1217

| property | value | file:line |
|---|---|---|
| Card | 120×80, fill `t["field"]`, radius 14 | C:1194-1195 |
| Pen | `t["accent"]` w2.4 selected / `t["control"]` w1.4 | C:1193 |
| Selectable | OUTPUT only (PointingHandCursor) | C:1149-1151 |
| Text | "Input" or node label | C:1196 |
| Meters | level (+ GR for output); top `BLOCK_H-8-11·n` | C:1198-1201 |
| Detail icon | "in"/"out" at (12,7,13,12), `t["muted"]` | C:1211 |
| Detail label | rect (29, 6, 71, 30), `t["text"]` | C:1212-1213 |
| Detail limiter LED | (106, 13), r 4.5, `LIMITER_COLORS[status]` (fallback [0]) | C:1214-1216 |
| Detail meters | left 12, width BLOCK_W-22, with numbers | C:1217 |
| Compact icon | (BLOCK_W/2-16, 10, 32, 28), `t["text"]` | C:1203 |
| Compact LED | (100, 20), r 7 | C:1204-1206 |
| Compact meters (lod ≥ 0.3) | left 12, width BLOCK_W-24, no numbers | C:1207-1209 |
| LIMITER_COLORS | 0 #8a8c92, 1 #5cc76e, 2 #f5d000, 3 #ff5c5c | speakernet/ui/meters.py:32 |
| Tooltips | output: `<b>{label}</b><br>Output meters and limiting status<br>Click to open the meter thresholds (gui_lim_st)`; input: "Input of the chain" / copy text | C:1152-1156 |

| state | visual | file:line |
|---|---|---|
| normal | control border w1.4 | C:1193 |
| hover | no visual change; highlights the way path | C:1181-1185 |
| selected (output) | accent w2.4 + halo | C:1193-1195 |

---

## 16. ScreenText / LinkToggle / lanes background / column headers / legend

### ScreenText  C:1260-1294
| property | value | file:line |
|---|---|---|
| Flags | ItemIgnoresTransformations, no mouse buttons, Z 2 | C:1270-1272 |
| Font | `numeric_font("caption")`, pointSizeF 7.5, bold optional | C:1274-1276 |
| Rect | width = textW+4; "center" centred; "number" above the anchor; "left" below; `line` offsets by one line height | C:1278-1285 |
| Draw | AlignLeft\|VCenter, colour as given | C:1293-1294 |
| `screen_font()` | same font (caption, 7.5 pt, bold flag) | C:278-282 |

### Lane / header / number labels (`_add_labels`)  C:1534-1567
| element | value | file:line |
|---|---|---|
| Lane name | bold, colour `BAND_COLORS[way%8]` if multi-way else `t["text"]`; pos (lane.left+12, lane.top+8) | C:1544-1548 |
| Lane subtitle | `t["muted"]`, line 1, same pos | C:1549-1552 |
| Column header | bold, `t["muted"]`, centred at (x, header_y + header_h/2) | C:1559-1562 |
| Order number | `t["muted"]`, align "number", pos node + (2,-2); tooltip "Processing order" | C:1563-1567 |

### LinkToggle (checkbox)  C:1297-1355
| property | value | file:line |
|---|---|---|
| Flags | IgnoresTransformations, hover, PointingHandCursor, Z 3 | C:1303-1306 |
| Font | `screen_font(bold=on)` | C:1310 |
| Text | "Linked with WAY n" (on) / "Link with WAY n" | C:1312 |
| Rect | (0, line·fontH+2, 18+textW+4, fontH+4); line default 2 | C:1313-1315 |
| Box | 12×12 at (left+1, centreY-6), radius 2.5 | C:1341, C:1344 |
| Box pen | `t["accent"]` if on or hover else `t["control"]`, w1.2 | C:1342 |
| Box fill | `t["accent"]` on / `t["surface"]` off | C:1343 |
| Check mark | (2.5,6)(5,8.8)(9.5,3.2); `t["accent_text"]` w1.8 RoundCap RoundJoin | C:1345-1349 |
| Text colour | `t["accent"]` on / `t["text"]` hover / `t["muted"]` | C:1351-1352 |
| Text rect | (box.right+5, top, w-18, h), AlignLeft\|VCenter | C:1353-1355 |
| Click | on release inside → `on_click(not on)` | C:1333-1336 |
| Tooltip | "Link WAY n: every change to a block of one of the two ways is also made to the same block of the other" | C:1316-1317 |

### Lanes background (`ChainView.drawBackground`)  C:1606-1640
| property | value | file:line |
|---|---|---|
| View bg | `t["window"]` | C:1396, C:1608 |
| Lane body | `paint_display(painter, lane.rect, 10)`: gradient `display` 0→0.45, `display_bottom` 1.0; pen `panel_edge_hi` w1; inner top shade 8 px `alpha(ink,110)`→`alpha(ink,0)` | C:1615; speakernet/ui/hardware.py:173-193 |
| Lane stripe | (left, top, 4, h), radius 2; `BAND_COLORS[way%8]` multi-way else `t["control"]` | C:1616-1621 |
| Empty slots | DashLine `t["field_border"]` w1.2, radius 6, NoBrush | C:1623-1626 |
| Link bracket | `t["accent"]` w2.2 RoundCap; x = MARGIN/2 = 7; y = lane.top+18; dots r 2.6 at (MARGIN, y) | C:1628-1639 |

### Legend (category colours; drawn in main_window.py)
| property | value | file:line |
|---|---|---|
| Items | 4 LEGEND entries + "Duplicated by DSP" (CATEGORY_COLORS["preset"], dashed) | speakernet/ui/main_window.py:123-124 |
| Swatch | roundedRect (x, y-6, 18, 12) r3; pen category colour w1.6; fill `t["surface"]` | speakernet/ui/main_window.py:137-142 |
| Text | `t["muted"]` at x+24; advance 24+textW+18 | speakernet/ui/main_window.py:143-145 |
| LEDs | "Active" `t["ok"]`, "Muted" `t["error"]`, r 4.5 | speakernet/ui/main_window.py:146-150 |
| sizeHint | 640×22 | speakernet/ui/main_window.py:126-127 |

### ChainView (container)
| property | value | file:line |
|---|---|---|
| Scroll bars | always off; NoFrame; AlignHCenter\|Top; NoDrag | C:1391-1395 |
| Min height | 160 | C:1397 |
| Fit | scale = min(vw/sw, vh/sh, 1.6); centreOn | C:1582-1591 |
| Relayout threshold | zoom change > 3%, up to 3 iterations | C:1499-1506 |
| Wheel | ignored (no zoom/scroll) | C:1766-1767 |
| Right-click | section menu of the BlockItem under the cursor | C:1470-1478 |
| LMB release | `node_activated` on a selectable Block/IO (not on a SectionSelector) | C:1745-1756 |
| Meter animation | MeterTimer (33 ms) runs while anything moves; stops on hide | C:1412, C:1714-1715, C:1762-1764 |
| Multi-way colouring | active when > 1 lane has a way | C:1530-1532 |

---

## 17. section_badge.py: SECTION_COLORS, text_on, SectionCombo, menu

| property | value | file:line |
|---|---|---|
| `SECTION_COLORS` | N #129cff, C #ff36ff, 1 #1affd5, 2 #ffd21f, 3 #ff681c, 4 #7dff4d | S:28-29 |
| `INK_DARK, INK_LIGHT` | #000000, #ffffff | S:30 |
| relative_luminance | WCAG: c/12.92 if c≤0.03928 else ((c+0.055)/1.055)^2.4; 0.2126R+0.7152G+0.0722B | S:33-37 |
| contrast_ratio | (Lhi+0.05)/(Llo+0.05) | S:40-43 |
| `text_on(c)` | INK_DARK if contrast(dark) ≥ contrast(light) else INK_LIGHT | S:46-49 |
| `SECTION_NAMES` | N "N · neutral", C "C · compressor", 1-4 plain digits | S:50 |
| `UNASSIGNED_TEXT` | "Not assigned" | S:51 |
| `RELEASE_TIMEOUT_MS` | 2000 | S:97 |
| Menu title | "Preset section of {block}" (disabled) + separator | S:80-82 |
| Menu items | checkable; current checked; disallowed → disabled with the reason as tooltip; tooltips visible | S:76, S:84-91 |
| Menu attr | WA_NoMouseReplay | S:79 |
| OutsideClickGuard | app event filter swallows outside press/release/dblclick; closes the menu; removed on release or after 2000 ms; removed immediately if the menu was closed without an outside click | S:101-167 |
| SectionCombo | QComboBox; disallowed items disabled with a tooltip; resyncs to the model after `activated` (emits `chosen`) | S:180-210 |
| SectionCombo styling | none custom (no paint code, no colours in this file) | S:180-210 |

Badge drawing itself is in BlockItem._paint_badge (§8, C:1058-1072).

---

## Not determinable from these files
- Token values (`surface`, `plot_top`, `grid_major`, etc.) are resolved in theme.py and are not resolved here.
- Point sizes of the `ui_font`/`numeric_font` roles ("caption", "body", "display") are defined in theme.py; only the explicit overrides are listed above.
- The painter's base font in `_paint_label` / SectionSelector (only the pointSizeF override is known).
- `BlockItem.warning` has no visual in this file.
- Hover/press transitions are not animated; the only animation is the meters (§9).

---

## Hardcoded literals (hex colours)

| literal | use | file:line |
|---|---|---|
| #3987e5 | BAND_COLORS[0] | P:347 |
| #d95926 | BAND_COLORS[1] | P:347 |
| #199e70 | BAND_COLORS[2] | P:347 |
| #c98500 | BAND_COLORS[3] | P:347 |
| #d55181 | BAND_COLORS[4] | P:347 |
| #2aa52a | BAND_COLORS[5] | P:347 |
| #9085e9 | BAND_COLORS[6] | P:347 |
| #e66767 | BAND_COLORS[7] | P:348 |
| #5cc76e | CATEGORY_COLORS[USER] | C:78 |
| #9fc3e6 | CATEGORY_COLORS[USER_PRESET] | C:78 |
| #e8a655 | CATEGORY_COLORS[PRESET_DEFINED] | C:78 |
| #8a8c92 | CATEGORY_COLORS[HARDCODED] | C:79 |
| #129cff | SECTION_COLORS["N"] | S:28 |
| #ff36ff | SECTION_COLORS["C"] | S:28 |
| #1affd5 | SECTION_COLORS["1"] | S:28 |
| #ffd21f | SECTION_COLORS["2"] | S:28 |
| #ff681c | SECTION_COLORS["3"] | S:29 |
| #7dff4d | SECTION_COLORS["4"] | S:29 |
| #000000 | INK_DARK | S:30 |
| #ffffff | INK_LIGHT | S:30 |
| (imported) #8a8c92 / #5cc76e / #f5d000 / #ff5c5c | LIMITER_COLORS used by IoItem | speakernet/ui/meters.py:32 |

No rgb()/QColor(r,g,b) literals in the three files. Colours derived at runtime: `fill.lighter(116)` and `fill.darker(108)` (C:761-762); hover `lighter(112/125)` (C:1002).
