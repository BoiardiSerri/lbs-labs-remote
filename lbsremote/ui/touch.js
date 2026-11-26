// Touch e tastiera a schermo (tablet e telefoni). Usa le funzioni e lo stato di app.js
// (S, sendInput, remotePos, canControl…), caricato dopo di lui.
//
// Gesti sullo schermo remoto (tocco diretto: il dito è il puntatore):
//   tocco                → clic sinistro       doppio tocco   → doppio clic
//   trascinare           → trascinamento col pulsante sinistro (faders, selezioni, finestre)
//   tocco lungo          → clic destro         due dita: tocco → clic destro, scorrere → rotella
'use strict'

const TOUCH = {
  pts: new Map(),     // pointerId -> { x, y, sx, sy }
  mode: null,         // null | 'drag' | 'long' | 'scroll' | 'ignore'
  longTimer: 0,
  lastTap: { t: 0, x: 0, y: 0, n: 0 },
  twoStart: 0,
  twoDist: 0,
  scrollLast: null,
}
const TAP_SLOP = 10             // px: oltre questa distanza il tocco diventa trascinamento
const LONG_PRESS_MS = 450
const DOUBLE_TAP_MS = 350
const SCROLL_PX_PER_STEP = 36   // px di scorrimento delle dita per uno "scatto" di rotella

function touchCenter() {
  let x = 0, y = 0
  for (const p of TOUCH.pts.values()) { x += p.x; y += p.y }
  const n = Math.max(1, TOUCH.pts.size)
  return { x: x / n, y: y / n }
}

function touchClick(button, pos, n) {
  sendInput({ t: 'btn', b: button, d: 1, x: pos.x, y: pos.y, n })
  sendInput({ t: 'btn', b: button, d: 0, x: pos.x, y: pos.y, n })
}

function setupTouch() {
  const area = $('remote-display')

  area.addEventListener('pointerdown', (ev) => {
    if (ev.pointerType !== 'touch') return
    ev.preventDefault()
    if (!canControl()) return
    try { area.setPointerCapture(ev.pointerId) } catch (e) { /* ignorato */ }
    TOUCH.pts.set(ev.pointerId, { x: ev.clientX, y: ev.clientY, sx: ev.clientX, sy: ev.clientY })
    if (TOUCH.pts.size === 1) {
      TOUCH.mode = null
      clearTimeout(TOUCH.longTimer)
      TOUCH.longTimer = setTimeout(() => {
        const pt = TOUCH.pts.values().next().value
        if (TOUCH.pts.size === 1 && TOUCH.mode === null && pt) {
          const p = remotePos({ clientX: pt.x, clientY: pt.y }, false)
          if (p) { TOUCH.mode = 'long'; touchClick('right', p, 1) }
        }
      }, LONG_PRESS_MS)
    } else if (TOUCH.pts.size === 2) {
      clearTimeout(TOUCH.longTimer)
      if (S.buttonsDown.has('left')) {                  // il trascinamento era già iniziato: lo si chiude
        S.buttonsDown.delete('left')
        sendInput({ t: 'btn', b: 'left', d: 0, n: 1 })
      }
      TOUCH.mode = 'scroll'
      TOUCH.twoStart = performance.now()
      TOUCH.twoDist = 0
      TOUCH.scrollLast = touchCenter()
      const c = TOUCH.scrollLast
      const p = remotePos({ clientX: c.x, clientY: c.y }, true)   // la rotella agisce sotto le dita
      if (p) sendInput({ t: 'move', x: p.x, y: p.y })
    }
  })

  area.addEventListener('pointermove', (ev) => {
    if (ev.pointerType !== 'touch') return
    const pt = TOUCH.pts.get(ev.pointerId)
    if (!pt) return
    ev.preventDefault()
    pt.x = ev.clientX; pt.y = ev.clientY
    if (!canControl()) return
    if (TOUCH.pts.size === 1) {
      if (TOUCH.mode === null && Math.hypot(pt.x - pt.sx, pt.y - pt.sy) > TAP_SLOP) {
        clearTimeout(TOUCH.longTimer)
        const p0 = remotePos({ clientX: pt.sx, clientY: pt.sy }, true)
        if (p0) {
          TOUCH.mode = 'drag'
          S.buttonsDown.set('left', 1)
          sendInput({ t: 'btn', b: 'left', d: 1, x: p0.x, y: p0.y, n: 1 })
        }
      }
      if (TOUCH.mode === 'drag') {
        const p = remotePos(ev, true)
        if (p) sendInput({ t: 'move', x: p.x, y: p.y })
      }
    } else if (TOUCH.mode === 'scroll' && TOUCH.pts.size === 2) {
      const c = touchCenter(), last = TOUCH.scrollLast
      const dx = c.x - last.x, dy = c.y - last.y
      TOUCH.twoDist += Math.abs(dx) + Math.abs(dy)
      TOUCH.scrollLast = c
      S.wheel.y += dy / SCROLL_PX_PER_STEP      // dita in basso = contenuto in basso = rotella "su"
      S.wheel.x += -dx / SCROLL_PX_PER_STEP
      const wx = Math.trunc(S.wheel.x), wy = Math.trunc(S.wheel.y)
      if (wx || wy) {
        S.wheel.x -= wx; S.wheel.y -= wy
        sendInput({ t: 'scroll', dx: wx, dy: wy })
      }
    }
  })

  const up = (ev) => {
    if (ev.pointerType !== 'touch') return
    const pt = TOUCH.pts.get(ev.pointerId)
    if (!pt) return
    ev.preventDefault()
    const count = TOUCH.pts.size
    TOUCH.pts.delete(ev.pointerId)
    clearTimeout(TOUCH.longTimer)
    if (canControl()) {
      if (count === 1) {
        if (TOUCH.mode === 'drag') {
          const p = remotePos(ev, true) || {}
          S.buttonsDown.delete('left')
          sendInput({ t: 'btn', b: 'left', d: 0, x: p.x, y: p.y, n: 1 })
        } else if (TOUCH.mode === null && ev.type === 'pointerup') {
          const p = remotePos({ clientX: pt.sx, clientY: pt.sy }, false)
          if (p) {
            const now = performance.now(), last = TOUCH.lastTap
            const near = Math.hypot(pt.sx - last.x, pt.sy - last.y) < 30
            const n = now - last.t < DOUBLE_TAP_MS && near ? Math.min(last.n + 1, 3) : 1
            TOUCH.lastTap = { t: now, x: pt.sx, y: pt.sy, n }
            touchClick('left', p, n)
          }
        }
      } else if (count === 2 && TOUCH.mode === 'scroll') {
        // due dita che toccano senza muoversi = clic destro
        if (TOUCH.twoDist < 12 && performance.now() - TOUCH.twoStart < 350 && ev.type === 'pointerup') {
          const c = TOUCH.scrollLast
          const p = c && remotePos({ clientX: c.x, clientY: c.y }, false)
          if (p) touchClick('right', p, 1)
        }
        TOUCH.mode = 'ignore'                       // finché tutte le dita non sono alzate
      }
    }
    if (TOUCH.pts.size === 0) TOUCH.mode = null
  }
  area.addEventListener('pointerup', up)
  area.addEventListener('pointercancel', up)
}

// ============================================================================
// tastiera a schermo + barra dei tasti speciali
// ============================================================================
const KBD = { open: false, mods: { ctrl: false, alt: false, shift: false, cmd: false } }
const KBD_MOD_NAME = { ctrl: 'ctrl_l', alt: 'alt_l', shift: 'shift_l', cmd: 'cmd_l' }

function kbdActiveMods() {
  return Object.keys(KBD.mods).filter((m) => KBD.mods[m]).map((m) => KBD_MOD_NAME[m])
}

function kbdClearMods() {
  for (const m of Object.keys(KBD.mods)) KBD.mods[m] = false
  document.querySelectorAll('#kbd-bar [data-mod]').forEach((b) => b.classList.remove('is-checked'))
}

// premi e rilascia un tasto con i modificatori "appiccicati" della barra (valgono per un solo tasto)
function kbdTap(wire) {
  const mods = kbdActiveMods()
  const shortcut = mods.some((m) => m !== 'shift_l')
  if (wire.c && shortcut && /^[A-Za-z]$/.test(wire.c)) wire = { c: wire.c.toLowerCase() }
  for (const m of mods) sendInput({ t: 'key', d: 1, s: m })
  sendInput({ t: 'key', d: 1, ...wire })
  sendInput({ t: 'key', d: 0, ...wire })
  for (const m of mods.reverse()) sendInput({ t: 'key', d: 0, s: m })
  if (mods.length) kbdClearMods()
}

function kbdPosition() {
  // iPad: la tastiera copre la pagina senza ridimensionarla; Android: la pagina si restringe da sola
  const vv = window.visualViewport
  const covered = vv ? Math.max(0, window.innerHeight - vv.height - vv.offsetTop) : 0
  $('kbd-bar').style.bottom = `${covered}px`
}

function kbdSetOpen(on) {
  if (on === KBD.open) return
  KBD.open = on
  const bar = $('kbd-bar'), inp = $('kbd-input')
  bar.classList.toggle('hidden', !on)
  $('btn-keyboard').classList.toggle('is-checked', on)
  if (on) { inp.value = ''; inp.focus(); kbdPosition() } else { inp.blur(); kbdClearMods() }
}

// le etichette dei modificatori seguono il sistema del computer remoto
function kbdSetPlatform(platform) {
  const bar = $('kbd-bar')
  bar.querySelector('[data-mod="cmd"] span').textContent = platform === 'darwin' ? 'CMD' : platform === 'win32' ? 'WIN' : 'SUPER'
  bar.querySelector('[data-mod="alt"] span').textContent = platform === 'darwin' ? 'OPT' : 'ALT'
}

function setupKeyboardBar() {
  const bar = $('kbd-bar'), inp = $('kbd-input')

  // i pulsanti non devono togliere il focus al campo nascosto (altrimenti la tastiera si chiude)
  bar.addEventListener('pointerdown', (ev) => ev.preventDefault())
  bar.querySelectorAll('[data-mod]').forEach((b) => b.addEventListener('click', () => {
    KBD.mods[b.dataset.mod] = !KBD.mods[b.dataset.mod]
    b.classList.toggle('is-checked', KBD.mods[b.dataset.mod])
  }))
  bar.querySelectorAll('[data-key]').forEach((b) => b.addEventListener('click', () => kbdTap({ s: b.dataset.key })))
  $('kbd-done').addEventListener('click', () => kbdSetOpen(false))
  $('btn-keyboard').addEventListener('click', () => kbdSetOpen(!KBD.open))
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', kbdPosition)
    window.visualViewport.addEventListener('scroll', kbdPosition)
  }

  // testo digitato sulla tastiera a schermo (se la tastiera non produce tasti "veri")
  let composing = false
  inp.addEventListener('compositionstart', () => { composing = true })
  inp.addEventListener('compositionend', (ev) => {
    composing = false
    if (ev.data) for (const ch of ev.data) kbdTap({ c: ch })
    inp.value = ''
  })
  inp.addEventListener('beforeinput', (ev) => {
    if (composing || ev.isComposing) return
    const t = ev.inputType
    if (t === 'insertText' && ev.data) { ev.preventDefault(); for (const ch of ev.data) kbdTap({ c: ch }) }
    else if (t === 'insertLineBreak' || t === 'insertParagraph') { ev.preventDefault(); kbdTap({ s: 'enter' }) }
    else if (t === 'deleteContentBackward') { ev.preventDefault(); kbdTap({ s: 'backspace' }) }
    else if (t === 'deleteContentForward') { ev.preventDefault(); kbdTap({ s: 'delete' }) }
  })
  inp.addEventListener('input', () => { if (!composing) inp.value = '' })
  inp.addEventListener('blur', () => { if (KBD.open) setTimeout(() => { if (KBD.open && document.activeElement !== inp) inp.focus() }, 0) })
}
