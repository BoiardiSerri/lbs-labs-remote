import Foundation

protocol CoreHost: AnyObject {
    /// Invia all'interfaccia un evento (JSON), da chiamare come LBS.onEvent(evento).
    func emit(_ json: String)
    func setFullscreen(_ on: Bool)
}

/// Logica dell'app per iPad/iPhone: stesso "api" che sul desktop offre viewer.py
/// (get_state, connect, disconnect, send_input, get_servers, set_fullscreen, set_capture).
/// Le risposte sono stringhe JSON.
final class AppCore {
    private unowned let host: CoreHost
    private let version: String
    private let connectNow: String
    private let selfTest: Bool
    private let lock = NSLock()
    private var cfg: [String: Any]
    private var _session: NetSession?
    private var connectText = ""
    private var firstFrameLogged = false
    private var alive = true

    init(host: CoreHost, version: String, connectNow: String, selfTest: Bool) {
        self.host = host
        self.version = version
        self.connectNow = connectNow
        self.selfTest = selfTest
        var c: [String: Any] = [:]
        if let stored = UserDefaults.standard.string(forKey: "config"),
           let parsed = parseJSON(Data(stored.utf8)) {
            c = parsed
        }
        if c["port"] == nil { c["port"] = Proto.defaultPort }
        if c["quality"] == nil { c["quality"] = "Automatic" }
        if c["fps"] == nil { c["fps"] = "Default" }
        if c["max_width"] == nil { c["max_width"] = "Default" }
        if c["last_host"] == nil { c["last_host"] = "" }
        self.cfg = c
        let t = Thread { [weak self] in
            while let core = self, core.alive {
                Thread.sleep(forTimeInterval: 0.5)
                core.pushStats()
            }
        }
        t.name = "stats"
        t.start()
    }

    deinit { alive = false }

    func shutdown() {
        alive = false
        lock.lock(); let s = _session; _session = nil; lock.unlock()
        s?.stop()
    }

    var session: NetSession? {
        lock.lock(); defer { lock.unlock() }
        return _session
    }

    private func saveConfig() {
        UserDefaults.standard.set(jsonString(cfg), forKey: "config")
    }

    // --- chiamate dall'interfaccia ---
    func call(_ method: String, _ args: [Any]) -> String {
        switch method {
        case "get_state":
            return jsonString(state())
        case "connect":
            let settings = (args.count > 1 ? args[1] as? [String: Any] : nil) ?? [:]
            return jsonString(connect(args.first as? String ?? "", settings))
        case "disconnect":
            disconnect()
            return "null"
        case "send_input":
            sendInput(args.first as? [Any] ?? [])
            return "null"
        case "get_servers":
            return "[]"                                   // niente ricerca automatica su iOS (serve un permesso speciale di Apple)
        case "set_fullscreen":
            host.setFullscreen((args.first as? Bool) ?? false)
            return "null"
        default:
            return "null"
        }
    }

    private func state() -> [String: Any] {
        var st: [String: Any] = [
            "version": version,
            "platform": "ios",
            "mobile": true,
            "discovery": false,
            "last_host": cfg["last_host"] ?? "",
            "connect_now": connectNow,
        ]
        var settings: [String: Any] = [:]
        for k in ["port", "quality", "fps", "max_width"] { settings[k] = cfg[k] }
        st["settings"] = settings
        if let s = session, !s.hello.isEmpty {
            st["session"] = ["host": s.host, "state": "connected", "hello": s.hello]
        }
        return st
    }

    private static func remoteConfig(_ settings: [String: Any]) -> [String: Any] {
        var out: [String: Any] = [:]
        switch settings["quality"] as? String ?? "Automatic" {
        case "Low": out["quality"] = 35; out["adaptive"] = false
        case "Medium": out["quality"] = 55; out["adaptive"] = false
        case "High": out["quality"] = 75; out["adaptive"] = false
        case "Maximum": out["quality"] = 90; out["adaptive"] = false
        default: break                                   // "Automatic": predefiniti dell'agente
        }
        if let fps = settings["fps"] as? String, let n = Int(fps) { out["fps"] = n }
        if let width = settings["max_width"] as? String {
            if width == "Original" { out["max_width"] = 0 } else if let n = Int(width) { out["max_width"] = n }
        }
        return out
    }

    private func connect(_ text: String, _ settings: [String: Any]) -> [String: Any] {
        if session != nil { return ["error": "Already connected."] }
        var port = Proto.defaultPort
        if let n = settings["port"] as? NSNumber { port = n.intValue }
        else if let s = settings["port"] as? String, let n = Int(s) { port = n }
        if port < 1 || port > 65535 { return ["error": "The port must be a number between 1 and 65535."] }
        guard let (hostName, p) = Proto.parseHostPort(text, defaultPort: port) else {
            return ["error": "Invalid address: check the IP address and port."]
        }
        for k in ["quality", "fps", "max_width"] { if let v = settings[k] { cfg[k] = v } }
        cfg["port"] = port
        saveConfig()
        connectText = text
        firstFrameLogged = false
        let s = NetSession(host: hostName, port: p, remoteConfig: AppCore.remoteConfig(settings)) { [weak self] sess, kind, data in
            self?.onEvent(sess, kind, data)
        }
        lock.lock(); _session = s; lock.unlock()
        s.start()
        return ["host": hostName]
    }

    private func disconnect() {
        lock.lock(); let s = _session; _session = nil; lock.unlock()
        s?.stop()
    }

    private func sendInput(_ events: [Any]) {
        guard let s = session else { return }
        for e in events { if let ev = e as? [String: Any] { s.sendInput(ev) } }
    }

    // --- eventi dalla rete ---
    private func onEvent(_ s: NetSession, _ kind: String, _ data: Any?) {
        guard s === session else { return }
        var ev: [String: Any] = [:]
        switch kind {
        case "connected":
            cfg["last_host"] = connectText.isEmpty ? s.host : connectText
            saveConfig()
            NSLog("LBS connected host=%@ name=%@", s.host, (data as? [String: Any])?["name"] as? String ?? "")
            ev = ["type": "connected", "host": s.host, "hello": data ?? [:]]
        case "failed":
            lock.lock(); _session = nil; lock.unlock()
            NSLog("LBS failed %@", String(describing: data))
            ev = ["type": "failed", "host": s.host, "message": String(describing: data ?? "")]
        case "closed":
            lock.lock(); _session = nil; lock.unlock()
            NSLog("LBS closed %@", String(describing: data))
            ev = ["type": "closed", "message": String(describing: data ?? "")]
        case "reconnecting", "reconnected":
            NSLog("LBS %@", kind)
            ev = ["type": kind]
        case "notice":
            let n = data as? [String: Any] ?? [:]
            ev = ["type": "notice", "level": n["level"] as? String ?? "warning", "text": n["text"] as? String ?? ""]
        default:
            return
        }
        host.emit(jsonString(ev))
    }

    private func pushStats() {
        guard let s = session, !s.hello.isEmpty else { return }
        if !firstFrameLogged && s.currentSeq() > 0 {
            firstFrameLogged = true
            NSLog("LBS first frame %dx%d", s.frameSize.0, s.frameSize.1)
            if selfTest { runSelfTest(s) }
        }
        var ev: [String: Any] = ["type": "stats", "fps": s.fps, "width": s.frameSize.0, "height": s.frameSize.1]
        if s.rttMs >= 0 { ev["rtt"] = s.rttMs }
        host.emit(jsonString(ev))
    }

    /// Prova automatica (avvio con -LBSSelfTest 1): invia un clic e un tasto, che l'agente di prova registra.
    private func runSelfTest(_ s: NetSession) {
        s.sendInput(["t": "move", "x": 0.5, "y": 0.5])
        s.sendInput(["t": "btn", "b": "left", "d": 1, "x": 0.5, "y": 0.5, "n": 1])
        s.sendInput(["t": "btn", "b": "left", "d": 0, "x": 0.5, "y": 0.5, "n": 1])
        s.sendInput(["t": "key", "d": 1, "c": "x"])
        s.sendInput(["t": "key", "d": 0, "c": "x"])
        NSLog("LBS selftest input sent")
    }
}
