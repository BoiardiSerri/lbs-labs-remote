// LBS Labs Remote – interfaccia del viewer (schermata di connessione + schermo remoto).
// Comunica con Python tramite window.pywebview.api (viewer.py) e riceve gli eventi da LBS.onEvent().
// Sui tablet lo stesso api è fornito dall'app nativa (bridge.js); gesti touch e tastiera a schermo: touch.js.
'use strict'

const $ = (id) => document.getElementById(id)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const CLICK_SWALLOW_MS = 300   // il clic che riattiva la finestra non viene inoltrato

const S = {
  api: null,
  platform: '',
  mode: 'connect',          // 'connect' | 'remote'
  connState: 'idle',        // 'idle' | 'connecting' | 'connected' | 'reconnecting'
  host: '',
  remoteName: '',
  mobile: !!window.LBS_MOBILE,   // app per tablet/telefono (Android, iPad): tocco, niente "focus" da perdere
  focused: !!window.LBS_MOBILE || document.hasFocus(),
  swallowUntil: 0,
  fullscreen: false,
  macCmdMonitor: false,
  settings: { port: 5970, quality: 'Automatic', fps: 'Default', max_width: 'Default' },
  keysDown: new Map(),      // code -> evento "key" inviato alla pressione
  buttonsDown: new Map(),   // pointerId/pulsante -> nome pulsante
  wheel: { x: 0, y: 0 },
  frameSeq: 0,
  frameLoopId: 0,
  frameUrl: null,
  serversSig: '',
}

// ============================================================================
// coda di input verso Python: una chiamata alla volta (l'ordine conta),
// i movimenti del mouse consecutivi si fondono in uno solo
// ============================================================================
const inputQ = []
let inputBusy = false

let rafMove = null
function sendInput(ev) {
  if (S.mode !== 'remote' || S.connState !== 'connected') return
  if (S.mobile && ev.t === 'move') {          // un solo movimento per fotogramma
    const first = rafMove === null
    rafMove = ev
    if (first) requestAnimationFrame(() => { const m = rafMove; rafMove = null; if (m) queueInput(m) })
    return
  }
  if (rafMove) { queueInput(rafMove); rafMove = null }   // i clic partono dalla posizione aggiornata
  queueInput(ev)
}

function queueInput(ev) {
  const last = inputQ[inputQ.length - 1]
  if (ev.t === 'move' && last && last.t === 'move') inputQ[inputQ.length - 1] = ev
  else inputQ.push(ev)
  pumpInput()
}

async function pumpInput() {
  if (inputBusy || !inputQ.length || !S.api) return
  inputBusy = true
  const batch = inputQ.splice(0, inputQ.length)
  try { await S.api.send_input(batch) } catch (e) { /* sessione chiusa */ }
  inputBusy = false
  if (inputQ.length) pumpInput()
}

// ============================================================================
// barra di stato con le due fasce ambra (porting del componente IoBar)
// ============================================================================
function paintIoBar() {
  const cv = $('iobar')
  const css = getComputedStyle(document.documentElement)
  const v = (n) => css.getPropertyValue(`--color-${n}`).trim()
  const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight
  if (!W || !H) return
  cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr)
  const x = cv.getContext('2d'); x.setTransform(dpr, 0, 0, dpr, 0, 0)
  x.fillStyle = v('bg-io-bar'); x.fillRect(0, 0, W, H)
  x.lineWidth = 1
  x.strokeStyle = v('edge-lo'); x.beginPath(); x.moveTo(0, 0.5); x.lineTo(W, 0.5); x.stroke()
  x.strokeStyle = v('edge-hi'); x.beginPath(); x.moveTo(0, 1.5); x.lineTo(W, 1.5); x.stroke()
  for (const at of [0.3, 0.7]) {
    const sx = W * at, t = 2, b = H, sw = 70
    x.save(); x.beginPath(); x.moveTo(sx + sw * 0.3, t); x.lineTo(sx + sw, t); x.lineTo(sx + sw * 0.7, b); x.lineTo(sx, b); x.closePath(); x.clip()
    x.strokeStyle = v('accent'); x.globalAlpha = 115 / 255; x.lineWidth = 2
    const shift = (b - t) / Math.tan(60 * Math.PI / 180)
    for (let p = sx - shift; p < sx + sw + shift; p += 9) { x.beginPath(); x.moveTo(p, b); x.lineTo(p + shift, t); x.stroke() }
    x.restore()
  }
}

function setIoMessage(msg, data) {
  $('iomsg').textContent = msg
  if (data !== undefined) $('iodata').textContent = data
}

// ============================================================================
// chip, banner
// ============================================================================
function setChip(el, kind, text, tooltip) {
  el.className = `ds-chip ds-chip--${kind}`
  el.querySelector('.ds-chip__text').textContent = text
  el.title = tooltip || text
}

function addBanner(container, kind, text, { closable = true, id = null } = {}) {
  if (id) { const old = document.getElementById(id); if (old) old.remove() }
  const b = document.createElement('div')
  b.className = `ds-banner ds-banner--${kind}`
  if (id) b.id = id
  b.innerHTML = `<span class="ic" data-icon="${kind === 'warn' ? 'warning' : 'check'}"></span><span class="ds-banner__text t-body"></span>`
  b.querySelector('.ds-banner__text').textContent = text
  if (closable) {
    const actions = document.createElement('div')
    actions.className = 'ds-banner__actions'
    actions.innerHTML = '<button class="ds-btn ds-btn--ghost ds-btn--icon ds-btn--small" title="Dismiss"><span class="ic" data-icon="close"></span></button>'
    actions.querySelector('button').addEventListener('click', () => b.remove())
    b.appendChild(actions)
  }
  container.appendChild(b)
  lbsFillIcons(b)
  return b
}

function clearBanners(container) { container.innerHTML = '' }

// ============================================================================
// schermate
// ============================================================================
function showConnectScreen() {
  S.mode = 'connect'
  S.connState = 'idle'
  S.frameLoopId++
  releaseAll(false)
  document.body.className = document.body.className.replace(/\bmode-\w+/g, '').trim() + ' mode-connect'
  document.body.classList.remove('is-fullscreen')
  S.fullscreen = false
  $('screen-connect').classList.remove('hidden')
  $('screen-remote').classList.add('hidden')
  for (const id of ['docname', 'chip-conn', 'chip-control', 'btn-fullscreen', 'btn-disconnect', 'btn-keyboard']) $(id).classList.add('hidden')
  if (typeof kbdSetOpen === 'function') kbdSetOpen(false)
  if (!S.mobile) $('chip-agent').classList.remove('hidden')
  $('btn-connect').disabled = false
  $('host').disabled = false
  if (S.frameUrl) { URL.revokeObjectURL(S.frameUrl); S.frameUrl = null }
  $('remote-img').removeAttribute('src')
  $('remote-empty').classList.remove('hidden')
  clearBanners($('remote-banners'))
  setIoMessage('Ready', S.version ? `v${S.version}` : '')
  setTimeout(() => { $('host').focus(); $('host').select() }, 0)
}

function showRemoteScreen(hello) {
  S.mode = 'remote'
  S.connState = 'connected'
  S.remoteName = (hello && hello.name) || S.host
  document.body.className = document.body.className.replace(/\bmode-\w+/g, '').trim() + ' mode-remote'
  $('screen-connect').classList.add('hidden')
  $('screen-remote').classList.remove('hidden')
  $('chip-agent').classList.add('hidden')
  for (const id of ['docname', 'chip-conn', 'chip-control', 'btn-fullscreen', 'btn-disconnect']) $(id).classList.remove('hidden')
  if (S.mobile) {
    $('btn-keyboard').classList.remove('hidden')
    $('chip-control').classList.add('hidden')
    kbdSetPlatform((hello && hello.platform) || '')
  }
  $('docname-text').textContent = S.remoteName === S.host ? S.host : `${S.remoteName}  ·  ${S.host}`
  $('remote-status').classList.add('hidden')
  setChip($('chip-conn'), 'ok', 'CONNECTED')
  S.swallowUntil = performance.now() + CLICK_SWALLOW_MS
  updateControlState()
  S.frameSeq = 0
  startFrameLoop()
  paintIoBar()
}

function updateControlState() {
  if (S.mode !== 'remote') return
  const active = S.focused && S.connState === 'connected'
  if (S.mobile) {
    setIoMessage(S.connState === 'connected'
      ? 'Tap to click · drag to move · two fingers to scroll · hold for right-click'
      : 'Reconnecting…')
    return
  }
  setChip($('chip-control'), active ? 'ok' : 'idle',
    active ? 'IN CONTROL' : 'CLICK TO CONTROL',
    active ? 'Mouse and keyboard go to the remote computer. Click outside this window to use your own computer.'
           : 'Click the remote screen to send mouse and keyboard to it.')
  setIoMessage(active
    ? (S.fullscreen ? 'You are in control · press ESC to exit full screen'
                    : 'You are in control · click outside this window to use your own computer')
    : 'Click the remote screen to take control')
  if (S.api) S.api.set_capture(active).catch(() => {})
}

// ============================================================================
// frame: richiesta continua dell'ultimo frame al server locale (mai in coda)
// ============================================================================
function startFrameLoop() {
  const id = ++S.frameLoopId
  const img = $('remote-img')
  ;(async () => {
    while (id === S.frameLoopId) {
      try {
        const r = await fetch(`frame?after=${S.frameSeq}`, { cache: 'no-store' })
        if (id !== S.frameLoopId) break
        if (r.status === 200) {
          S.frameSeq = Number(r.headers.get('X-Seq')) || S.frameSeq + 1
          const url = URL.createObjectURL(await r.blob())
          const pre = new Image()
          pre.src = url
          try { await pre.decode() } catch (e) { URL.revokeObjectURL(url); continue }
          if (id !== S.frameLoopId) { URL.revokeObjectURL(url); break }
          img.src = url
          $('remote-empty').classList.add('hidden')
          if (S.frameUrl) URL.revokeObjectURL(S.frameUrl)
          S.frameUrl = url
        } else if (r.status !== 204) {
          await sleep(300)
        }
      } catch (e) {
        await sleep(300)
      }
    }
  })()
}

// coordinate del puntatore in frazione dell'immagine remota (object-fit: contain)
function remotePos(ev, clamp) {
  const img = $('remote-img')
  const iw = img.naturalWidth, ih = img.naturalHeight
  if (!iw || !ih) return null
  const r = img.getBoundingClientRect()
  const s = Math.min(r.width / iw, r.height / ih)
  const w = iw * s, h = ih * s
  const left = r.left + (r.width - w) / 2, top = r.top + (r.height - h) / 2
  let fx = (ev.clientX - left) / w, fy = (ev.clientY - top) / h
  if (!clamp && (fx < 0 || fx > 1 || fy < 0 || fy > 1)) return null
  fx = Math.min(Math.max(fx, 0), 1); fy = Math.min(Math.max(fy, 0), 1)
  return { x: Math.round(fx * 1e5) / 1e5, y: Math.round(fy * 1e5) / 1e5 }
}

function canControl() {
  return S.mode === 'remote' && S.connState === 'connected' && (S.mobile || S.focused)
}

// ============================================================================
// mouse
// ============================================================================
const BUTTONS = { 0: 'left', 1: 'middle', 2: 'right' }

function setupPointer() {
  const area = $('remote-display')

  area.addEventListener('pointerdown', (ev) => {
    ev.preventDefault()
    if (ev.pointerType === 'touch') return                            // touch.js
    if (!canControl() || performance.now() < S.swallowUntil) return   // clic di attivazione
    const name = BUTTONS[ev.button]
    if (!name) return
    const p = remotePos(ev, false)
    if (!p) return                                                    // bande ai lati dell'immagine
    try { area.setPointerCapture(ev.pointerId) } catch (e) { /* ignorato */ }
    S.buttonsDown.set(name, ev.detail || 1)
    sendInput({ t: 'btn', b: name, d: 1, x: p.x, y: p.y, n: ev.detail || 1 })
  })

  area.addEventListener('pointermove', (ev) => {
    if (ev.pointerType === 'touch' || !canControl()) return
    const p = remotePos(ev, true)
    if (p) sendInput({ t: 'move', x: p.x, y: p.y })
  })

  area.addEventListener('pointerup', (ev) => {
    if (ev.pointerType === 'touch') return
    const name = BUTTONS[ev.button]
    if (!name || !S.buttonsDown.has(name)) return
    const n = S.buttonsDown.get(name)
    S.buttonsDown.delete(name)
    const p = remotePos(ev, true) || {}
    sendInput({ t: 'btn', b: name, d: 0, x: p.x, y: p.y, n })
  })

  area.addEventListener('contextmenu', (ev) => ev.preventDefault())
  area.addEventListener('dblclick', (ev) => ev.preventDefault())

  area.addEventListener('wheel', (ev) => {
    ev.preventDefault()
    if (!canControl()) return
    // rotella classica: wheelDelta a multipli di 120 = uno scatto ciascuno;
    // trackpad e rotelle "fini": si accumulano i pixel (circa 50 per scatto)
    const wy = ev.wheelDeltaY || 0, wx = ev.wheelDeltaX || 0
    if (ev.deltaMode === 1) { S.wheel.x += ev.deltaX / 3; S.wheel.y += -ev.deltaY / 3 }
    else if (ev.deltaMode === 2) { S.wheel.x += ev.deltaX; S.wheel.y += -ev.deltaY }
    else if ((wy && wy % 120 === 0) || (wx && wx % 120 === 0)) { S.wheel.x += -wx / 120; S.wheel.y += wy / 120 }
    else { S.wheel.x += ev.deltaX / 50; S.wheel.y += -ev.deltaY / 50 }
    const dx = Math.trunc(S.wheel.x), dy = Math.trunc(S.wheel.y)
    if (dx || dy) {
      S.wheel.x -= dx; S.wheel.y -= dy
      sendInput({ t: 'scroll', dx, dy })
    }
  }, { passive: false })
}

// ============================================================================
// tastiera
// ============================================================================
const SPECIAL_BY_CODE = {
  ShiftLeft: 'shift_l', ShiftRight: 'shift_r', ControlLeft: 'ctrl_l', ControlRight: 'ctrl_r',
  AltLeft: 'alt_l', AltRight: 'alt_r', MetaLeft: 'cmd_l', MetaRight: 'cmd_r', OSLeft: 'cmd_l', OSRight: 'cmd_r',
  CapsLock: 'caps_lock', NumpadEnter: 'enter', ContextMenu: 'menu',
}
const SPECIAL_BY_KEY = {
  Enter: 'enter', Tab: 'tab', Backspace: 'backspace', Delete: 'delete', Insert: 'insert',
  Home: 'home', End: 'end', PageUp: 'page_up', PageDown: 'page_down',
  ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right',
  ' ': 'space', CapsLock: 'caps_lock', ContextMenu: 'menu', NumLock: 'num_lock',
  ScrollLock: 'scroll_lock', Pause: 'pause', PrintScreen: 'print_screen', AltGraph: 'alt_gr',
  AudioVolumeMute: 'media_volume_mute', AudioVolumeDown: 'media_volume_down',
  AudioVolumeUp: 'media_volume_up', MediaPlayPause: 'media_play_pause',
}
for (let i = 1; i <= 20; i++) SPECIAL_BY_KEY[`F${i}`] = `f${i}`

function keyToWire(ev) {
  if (ev.key === 'AltGraph') return { s: 'alt_gr' }
  if (SPECIAL_BY_CODE[ev.code]) return { s: SPECIAL_BY_CODE[ev.code] }
  if (SPECIAL_BY_KEY[ev.key]) return { s: SPECIAL_BY_KEY[ev.key] }
  const altGr = ev.getModifierState && ev.getModifierState('AltGraph')
  const shortcut = (ev.ctrlKey || ev.metaKey || ev.altKey) && !altGr
  if ([...ev.key].length === 1) {
    // con Ctrl/Alt/Cmd si inoltra la lettera minuscola: lo Shift è già inoltrato a parte
    if (shortcut && /^[A-Za-z]$/.test(ev.key)) return { c: ev.key.toLowerCase() }
    return { c: ev.key }
  }
  // tasti "morti" o non identificati: si usa la posizione fisica
  let m = /^Key([A-Z])$/.exec(ev.code)
  if (m) return { c: m[1].toLowerCase() }
  m = /^(?:Digit|Numpad)(\d)$/.exec(ev.code)
  if (m) return { c: m[1] }
  return null
}

function setupKeyboard() {
  window.addEventListener('keydown', (ev) => {
    if (S.mode !== 'remote') return
    // tastiera a schermo che non produce tasti "veri" (composizione): il testo lo gestisce touch.js
    if (S.mobile && (ev.key === 'Unidentified' || ev.keyCode === 229 || ev.isComposing)) return
    ev.preventDefault()
    ev.stopPropagation()
    if (ev.key === 'Escape') {
      if (S.fullscreen) { setFullscreen(false); return }
      if (!S.mobile) return                             // sul desktop ESC è riservato: mai inoltrato
    }
    if (!canControl() || ev.isComposing) return
    // Mac: le scorciatoie Cmd+lettera le intercetta Python prima dei menu (viewer.py)
    if (S.macCmdMonitor && ev.metaKey && [...ev.key].length === 1) return
    let wire = S.keysDown.get(ev.code)
    if (!wire) {
      wire = keyToWire(ev)
      if (!wire) return
      if (S.mobile && typeof kbdActiveMods === 'function' && kbdActiveMods().length) {
        kbdTap(wire)                                    // modificatori "appiccicati" della barra dei tasti
        return
      }
      S.keysDown.set(ev.code, wire)
    }
    sendInput({ t: 'key', d: 1, ...wire })              // anche le ripetizioni automatiche
  }, true)

  window.addEventListener('keyup', (ev) => {
    if (S.mode !== 'remote') return
    ev.preventDefault()
    ev.stopPropagation()
    if (ev.key === 'Escape' && !S.mobile) return
    const wire = S.keysDown.get(ev.code)
    if (!wire) return
    S.keysDown.delete(ev.code)
    sendInput({ t: 'key', d: 0, ...wire })
  }, true)
}

// rilascia sul computer remoto tutto ciò che risulta premuto (niente tasti "incollati")
function releaseAll(send = true) {
  if (send && S.mode === 'remote' && S.connState === 'connected') {
    for (const wire of S.keysDown.values()) sendInput({ t: 'key', d: 0, ...wire })
    for (const [name, n] of S.buttonsDown) sendInput({ t: 'btn', b: name, d: 0, n })
  }
  S.keysDown.clear()
  S.buttonsDown.clear()
  S.wheel = { x: 0, y: 0 }
}

// ============================================================================
// focus: la cattura è attiva solo quando la finestra ha il focus
// ============================================================================
function setupFocus() {
  if (S.mobile) {            // su tablet non c'è un "focus" da perdere: si rilascia tutto in background
    document.addEventListener('visibilitychange', () => { if (document.hidden) releaseAll(true) })
    return
  }
  window.addEventListener('focus', () => {
    if (!S.focused) {
      S.focused = true
      S.swallowUntil = performance.now() + CLICK_SWALLOW_MS
      updateControlState()
    }
  })
  window.addEventListener('blur', () => {
    if (S.focused) {
      S.focused = false
      releaseAll(true)
      updateControlState()
    }
  })
}

// ============================================================================
// schermo intero
// ============================================================================
let hintTimer = null
async function setFullscreen(on) {
  if (on === S.fullscreen) return
  S.fullscreen = on
  document.body.classList.toggle('is-fullscreen', on)
  clearTimeout(hintTimer)
  $('fs-hint').textContent = S.mobile ? 'Tap EXIT FULL SCREEN to return' : 'Press ESC to exit full screen'
  $('fs-hint').classList.toggle('hidden', !on)
  if (on) hintTimer = setTimeout(() => $('fs-hint').classList.add('hidden'), 2500)
  updateControlState()
  try { await S.api.set_fullscreen(on) } catch (e) { /* ignorato */ }
}

// ============================================================================
// connessione
// ============================================================================
function readSettings() {
  const q = document.querySelector('#set-quality .is-checked')
  return {
    port: Number($('set-port').value) || 5970,
    quality: q ? q.dataset.v : 'Automatic',
    fps: $('set-fps').value,
    max_width: $('set-width').value,
  }
}

function applySettings(s) {
  S.settings = Object.assign(S.settings, s || {})
  $('set-port').value = S.settings.port
  for (const b of document.querySelectorAll('#set-quality .ds-seg__item')) {
    b.classList.toggle('is-checked', b.dataset.v === S.settings.quality)
  }
  if (!document.querySelector('#set-quality .is-checked')) document.querySelector('#set-quality .ds-seg__item').classList.add('is-checked')
  $('set-fps').value = S.settings.fps
  $('set-width').value = S.settings.max_width
}

async function connect(target) {
  if (S.connState !== 'idle' && S.connState !== 'failed') return
  const text = (target || $('host').value).trim()
  if (target) $('host').value = target
  clearBanners($('connect-banners'))
  if (!text) {
    addBanner($('connect-banners'), 'warn', 'Type the IP address of the computer you want to control.')
    $('host').focus()
    return
  }
  S.connState = 'connecting'
  $('btn-connect').disabled = true
  $('host').disabled = true
  setIoMessage(`Connecting to ${text}…`)
  let res
  try { res = await S.api.connect(text, readSettings()) } catch (e) { res = { error: String(e) } }
  if (res && res.error) {
    S.connState = 'idle'
    $('btn-connect').disabled = false
    $('host').disabled = false
    addBanner($('connect-banners'), 'warn', res.error)
    setIoMessage('Ready')
    $('host').focus()
    return
  }
  S.host = res.host
}

async function disconnect() {
  try { await S.api.disconnect() } catch (e) { /* ignorato */ }
  showConnectScreen()
}

// ============================================================================
// eventi da Python
// ============================================================================
window.LBS = {
  onEvent(ev) {
    switch (ev.type) {
      case 'connected':
        S.host = ev.host || S.host
        showRemoteScreen(ev.hello)
        break
      case 'failed':
        showConnectScreen()
        addBanner($('connect-banners'), 'warn', `Unable to connect to ${ev.host}: ${ev.message}`)
        break
      case 'closed':
        showConnectScreen()
        if (ev.message) addBanner($('connect-banners'), 'warn', ev.message)
        break
      case 'reconnecting':
        S.connState = 'reconnecting'
        releaseAll(false)
        setChip($('chip-conn'), 'warn', 'RECONNECTING…')
        $('remote-status').classList.remove('hidden')
        updateControlState()
        setIoMessage('Connection lost – reconnecting…')
        break
      case 'reconnected':
        S.connState = 'connected'
        setChip($('chip-conn'), 'ok', 'CONNECTED')
        $('remote-status').classList.add('hidden')
        updateControlState()
        break
      case 'notice':
        addBanner($('remote-banners'), ev.level === 'info' ? 'info' : 'warn', ev.text)
        break
      case 'stats':
        if (S.mode === 'remote' && S.connState === 'connected') {
          setChip($('chip-conn'), 'ok', ev.rtt != null ? `CONNECTED · ${Math.round(ev.rtt)} ms` : 'CONNECTED',
            'Connection quality: round-trip time to the remote computer')
        }
        if (S.mode === 'remote') {
          $('iodata').textContent = ev.width ? `${ev.width} × ${ev.height} · ${Math.round(ev.fps)} fps` : ''
        }
        break
      case 'agent':
        updateAgentChip(ev)
        break
      case 'fullscreen':
        if (!ev.on && S.fullscreen) { S.fullscreen = false; document.body.classList.remove('is-fullscreen'); updateControlState() }
        break
    }
  },
}

function updateAgentChip(a) {
  const chip = $('chip-agent')
  if (a.state === 'ready') setChip(chip, 'ok', 'THIS COMPUTER: READY', 'Other computers can control this one.')
  else if (a.state === 'unavailable') setChip(chip, 'warn', 'THIS COMPUTER: NOT CONTROLLABLE', a.message || 'LBS Labs Remote is not running in the background.')
  else setChip(chip, 'idle', 'THIS COMPUTER: CHECKING…')
}

// ============================================================================
// elenco dei computer trovati in rete
// ============================================================================
async function refreshServers() {
  if (S.mode === 'connect' && S.api) {
    let list = []
    try { list = await S.api.get_servers() } catch (e) { /* ignorato */ }
    const sig = JSON.stringify(list)
    if (sig !== S.serversSig) {
      S.serversSig = sig
      const rows = $('server-rows')
      rows.innerHTML = ''
      list.forEach((s, i) => {
        const row = document.createElement('div')
        row.className = 'ds-row' + (i % 2 ? ' is-alt' : '')
        row.innerHTML = '<span class="ds-row__name t-value"></span><span class="t-caption c-muted num addr"></span>' +
          '<span class="ds-row__spacer"></span>' +
          (s.busy ? '<span class="ds-chip ds-chip--mini ds-chip--warn" title="Someone is already connected"><span class="ds-chip__text">IN USE</span></span>' : '') +
          '<button class="ds-btn ds-btn--small">Connect</button>'
        row.querySelector('.ds-row__name').textContent = s.name
        row.querySelector('.addr').textContent = s.target
        row.title = `Connect to ${s.name} (${s.target})`
        row.addEventListener('click', () => connect(s.target))
        rows.appendChild(row)
      })
      $('server-empty').classList.toggle('hidden', list.length > 0)
    }
  }
  setTimeout(refreshServers, 1000)
}

// ============================================================================
// avvio
// ============================================================================
async function init() {
  S.api = window.pywebview.api
  let st = {}
  try { st = await S.api.get_state() } catch (e) { /* ignorato */ }
  S.platform = st.platform || ''
  S.version = st.version || ''
  S.macCmdMonitor = !!st.mac_cmd_monitor
  if (S.platform === 'darwin') document.body.classList.add('scale-125')
  if (S.mobile) {
    document.body.classList.add('is-mobile', 'is-touch', `is-${window.LBS_MOBILE}`)
    $('chip-agent').classList.add('hidden')
    $('chip-control').classList.add('hidden')
    setupKeyboardBar()
    if (st.discovery === false) {
      $('server-empty').querySelector('.ds-empty__title').textContent = 'Type the IP address'
      $('server-empty').querySelector('.ds-empty__caption').innerHTML =
        'Automatic search is not available on this device.<br>Enter the IP address of the computer above and tap CONNECT.'
    }
  }
  $('host').value = st.last_host || ''
  applySettings(st.settings)
  setIoMessage('Ready', st.version ? `v${st.version}` : '')
  if (st.agent) updateAgentChip(st.agent)
  if (st.notice) addBanner($('connect-banners'), 'warn', st.notice)
  paintIoBar()
  if (st.session && st.session.state === 'connected') {   // pagina ricaricata durante una sessione
    S.host = st.session.host
    showRemoteScreen(st.session.hello)
  } else {
    showConnectScreen()
    if (st.connect_now) connect(st.connect_now)
  }
  refreshServers()
}

function setupStatic() {
  $('btn-connect').addEventListener('click', () => connect())
  $('host').addEventListener('keydown', (ev) => { if (ev.key === 'Enter') { ev.preventDefault(); connect() } })
  $('btn-disconnect').addEventListener('click', disconnect)
  $('btn-fullscreen').addEventListener('click', () => setFullscreen(true))
  $('btn-exit-fs').addEventListener('click', () => setFullscreen(false))
  $('btn-advanced').addEventListener('click', () => {
    const open = $('advanced').classList.toggle('hidden') === false
    $('btn-advanced').classList.toggle('is-open', open)
  })
  for (const b of document.querySelectorAll('#set-quality .ds-seg__item')) {
    b.addEventListener('click', () => {
      for (const o of document.querySelectorAll('#set-quality .ds-seg__item')) o.classList.toggle('is-checked', o === b)
    })
  }
  // trascinare immagini o testo nella pagina non deve fare nulla
  window.addEventListener('dragover', (e) => e.preventDefault())
  window.addEventListener('drop', (e) => e.preventDefault())
  new ResizeObserver(paintIoBar).observe($('iobar'))
}

setupStatic()
setupPointer()
setupTouch()
setupKeyboard()
setupFocus()
lbsFillIcons()
paintIoBar()
if (window.pywebview && window.pywebview.api) init()
else window.addEventListener('pywebviewready', init)
