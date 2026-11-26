// Icone 16×16 in currentColor. Le icone LBS si caricano da lbs/icone/*.svg (unica fonte);
// qui solo le icone nuove di questo programma, disegnate con le stesse regole
// (griglia 16, tratto 1,4 px, terminali e giunzioni tondi).
'use strict'

const LBS_CUSTOM_ICONS = {
  // schermo intero: quattro angoli
  // tastiera: contorno con tasti puntiformi
  keyboard: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="1.5" y="3.5" width="13" height="9" rx="2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M4.2 6.5h.01M6.7 6.5h.01M9.3 6.5h.01M11.8 6.5h.01M4.2 9.5h.01M11.8 9.5h.01M6.2 9.6h3.6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  fullscreen: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M2.5 6V2.5H6M10 2.5h3.5V6M13.5 10v3.5H10M6 13.5H2.5V10" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

const lbsIconCache = {}

async function lbsIcon(name) {
  if (LBS_CUSTOM_ICONS[name]) return LBS_CUSTOM_ICONS[name]
  if (!lbsIconCache[name]) {
    lbsIconCache[name] = fetch(`lbs/icone/${name}.svg`)
      .then((r) => (r.ok ? r.text() : ''))
      .then((t) => t.replace(/\scolor="[^"]*"/, ''))   // il colore viene dal testo (currentColor)
      .catch(() => '')
  }
  return lbsIconCache[name]
}

// riempie tutti gli elementi <span class="ic" data-icon="nome"> presenti in `root`
async function lbsFillIcons(root = document) {
  const els = [...root.querySelectorAll('.ic[data-icon]:not([data-filled])')]
  await Promise.all(els.map(async (el) => {
    el.innerHTML = await lbsIcon(el.dataset.icon)
    el.dataset.filled = '1'
  }))
}
