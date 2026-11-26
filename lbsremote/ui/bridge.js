// Ponte verso le app per tablet (Android e iPad).
// Sul desktop l'interfaccia parla con Python tramite window.pywebview.api (viewer.py);
// sui tablet le stesse chiamate arrivano all'app nativa:
//   Android → window.LBSAndroid (JavascriptInterface, risposta con LBSNative.resolve)
//   iPad    → window.webkit.messageHandlers.lbsNative (risposta come Promise)
// Le risposte sono sempre stringhe JSON. I frame arrivano come sul desktop: fetch('frame?after=N').
'use strict'

;(function () {
  if (window.pywebview) return
  const android = window.LBSAndroid
  const ios = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.lbsNative
  if (!android && !ios) return

  const pending = new Map()
  let seq = 0
  window.LBSNative = {
    resolve(id, json) {
      const done = pending.get(id)
      if (done) { pending.delete(id); done(json) }
    },
  }

  function call(method, args) {
    const parse = (json) => (json === null || json === undefined || json === '' ? null : JSON.parse(json))
    if (ios) return ios.postMessage({ method, args: args || [] }).then(parse)
    return new Promise((resolve) => {
      const id = ++seq
      pending.set(id, (json) => resolve(parse(json)))
      android.call(id, method, JSON.stringify(args || []))
    })
  }

  window.LBS_MOBILE = android ? 'android' : 'ios'
  window.pywebview = {
    api: {
      get_state: () => call('get_state'),
      connect: (text, settings) => call('connect', [text, settings]),
      disconnect: () => call('disconnect'),
      send_input: (events) => call('send_input', [events]),
      get_servers: () => call('get_servers'),
      set_fullscreen: (on) => call('set_fullscreen', [on]),
      set_capture: (active) => call('set_capture', [active]),
    },
  }
})()
