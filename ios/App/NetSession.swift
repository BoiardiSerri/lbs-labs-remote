import Darwin
import Foundation

enum NetError: Error {
    case closed
    case timeout
    case refused
    case unknownHost
    case foreign(String)
    case io(String)
}

/// Socket TCP bloccante con timeout in lettura (POSIX: niente dipendenze, stesso comportamento di Android).
final class TCPSocket {
    private let fd: Int32
    private let lock = NSLock()
    private var aborted = false

    private init(fd: Int32) { self.fd = fd }

    var isAborted: Bool {
        lock.lock(); defer { lock.unlock() }
        return aborted
    }

    static func open(host: String, port: Int, connectTimeout: TimeInterval, recvTimeout: Int) throws -> TCPSocket {
        var hints = addrinfo()
        hints.ai_family = AF_UNSPEC
        hints.ai_socktype = SOCK_STREAM
        var res: UnsafeMutablePointer<addrinfo>?
        if getaddrinfo(host, String(port), &hints, &res) != 0 || res == nil {
            throw NetError.unknownHost
        }
        defer { freeaddrinfo(res) }

        var refused = false
        var timedOut = false
        var lastError = "connection failed"
        var ptr = res
        while let ai = ptr {
            ptr = ai.pointee.ai_next
            let fd = socket(ai.pointee.ai_family, ai.pointee.ai_socktype, ai.pointee.ai_protocol)
            if fd < 0 { continue }
            var one: Int32 = 1
            setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, socklen_t(MemoryLayout<Int32>.size))
            let flags = fcntl(fd, F_GETFL, 0)
            _ = fcntl(fd, F_SETFL, flags | O_NONBLOCK)
            var connected = false
            if Darwin.connect(fd, ai.pointee.ai_addr, ai.pointee.ai_addrlen) == 0 {
                connected = true
            } else if errno == EINPROGRESS {
                var pfd = pollfd(fd: fd, events: Int16(POLLOUT), revents: 0)
                let pr = poll(&pfd, 1, Int32(connectTimeout * 1000))
                if pr == 0 {
                    timedOut = true
                } else if pr > 0 {
                    var err: Int32 = 0
                    var len = socklen_t(MemoryLayout<Int32>.size)
                    getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &len)
                    if err == 0 {
                        connected = true
                    } else {
                        if err == ECONNREFUSED { refused = true }
                        lastError = String(cString: strerror(err))
                    }
                }
            } else {
                if errno == ECONNREFUSED { refused = true }
                lastError = String(cString: strerror(errno))
            }
            if !connected {
                Darwin.close(fd)
                continue
            }
            _ = fcntl(fd, F_SETFL, flags)                       // di nuovo bloccante
            setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, socklen_t(MemoryLayout<Int32>.size))
            setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &one, socklen_t(MemoryLayout<Int32>.size))
            var tv = timeval(tv_sec: recvTimeout, tv_usec: 0)
            setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, socklen_t(MemoryLayout<timeval>.size))
            return TCPSocket(fd: fd)
        }
        if refused { throw NetError.refused }
        if timedOut { throw NetError.timeout }
        throw NetError.io(lastError)
    }

    func readExact(_ n: Int) throws -> [UInt8] {
        if n <= 0 { return [] }
        var buf = [UInt8](repeating: 0, count: n)
        var got = 0
        while got < n {
            let r = buf.withUnsafeMutableBytes { (raw: UnsafeMutableRawBufferPointer) -> Int in
                return Darwin.recv(fd, raw.baseAddress! + got, n - got, 0)
            }
            if r > 0 {
                got += r
            } else if r == 0 {
                throw NetError.closed
            } else {
                if errno == EINTR { continue }
                if errno == EAGAIN || errno == EWOULDBLOCK { throw NetError.timeout }
                throw NetError.io(String(cString: strerror(errno)))
            }
        }
        return buf
    }

    func writeAll(_ data: Data) throws {
        try data.withUnsafeBytes { (raw: UnsafeRawBufferPointer) in
            var off = 0
            while off < raw.count {
                let w = Darwin.send(fd, raw.baseAddress! + off, raw.count - off, 0)
                if w > 0 {
                    off += w
                } else if w < 0 && errno == EINTR {
                    continue
                } else {
                    throw NetError.io(String(cString: strerror(errno)))
                }
            }
        }
    }

    /// Sblocca chi è in attesa di dati (lettura o scrittura) e impedisce nuovi usi.
    func abort() {
        lock.lock()
        let first = !aborted
        aborted = true
        lock.unlock()
        if first { shutdown(fd, SHUT_RDWR) }
    }

    func closeDescriptor() {
        abort()
        Darwin.close(fd)
    }
}

/// Connessione all'agente remoto con riconnessione automatica (porting di lbsremote/client.py).
/// Eventi (kind → data): connected → hello · failed → String · reconnecting → String ·
/// reconnected → hello · notice → [String: Any] · closed → String.
final class NetSession {
    typealias Handler = (NetSession, String, Any?) -> Void

    private static let connectTimeout: TimeInterval = 6
    private static let recvTimeout = 6                    // nessun dato per 6 s => connessione persa
    private static let reconnectWindow: TimeInterval = 15
    private static let reconnectDelay: TimeInterval = 2.5
    private static let pingInterval: TimeInterval = 1
    private static let minSession: TimeInterval = 5       // una sessione più breve è "caduta subito"
    private static let maxQuickDrops = 3                  // dopo tante cadute immediate di fila si smette

    let host: String
    let port: Int
    private let remoteConfig: [String: Any]
    private let handler: Handler

    private let stateLock = NSLock()
    private var _hello: [String: Any] = [:]
    private var _rtt: Double = -1
    private var _fps: Double = 0
    private var _size: (Int, Int) = (0, 0)
    private var _stopped = false
    private var lastNotice = ""
    private var sock: TCPSocket?

    private let frameCond = NSCondition()
    private var frame: Data?
    private var frameSeq = 0
    private var fpsCount = 0
    private var fpsT0 = ProcessInfo.processInfo.systemUptime

    private let sendCond = NSCondition()
    private var sendQueue: [Data] = []

    init(host: String, port: Int, remoteConfig: [String: Any], handler: @escaping Handler) {
        self.host = host
        self.port = port
        self.remoteConfig = remoteConfig
        self.handler = handler
    }

    // --- stato letto dall'esterno ---
    var hello: [String: Any] { stateLock.lock(); defer { stateLock.unlock() }; return _hello }
    var rttMs: Double { stateLock.lock(); defer { stateLock.unlock() }; return _rtt }
    var fps: Double { stateLock.lock(); defer { stateLock.unlock() }; return _fps }
    var frameSize: (Int, Int) { stateLock.lock(); defer { stateLock.unlock() }; return _size }
    var stopped: Bool { stateLock.lock(); defer { stateLock.unlock() }; return _stopped }

    func start() {
        let t = Thread { [weak self] in self?.run() }
        t.name = "net-session"
        t.start()
    }

    func stop() {
        stateLock.lock(); _stopped = true; let s = sock; stateLock.unlock()
        s?.abort()
        frameCond.lock(); frameCond.broadcast(); frameCond.unlock()
        sendCond.lock(); sendCond.broadcast(); sendCond.unlock()
    }

    func sendInput(_ event: [String: Any]) {
        let msg = Proto.pack(Proto.input, json: event)
        sendCond.lock(); sendQueue.append(msg); sendCond.signal(); sendCond.unlock()
    }

    func currentSeq() -> Int {
        frameCond.lock(); defer { frameCond.unlock() }
        return frameSeq
    }

    /// Attende un frame più recente di `after` (fino a `timeout` s). Restituisce (seq, jpeg o nil).
    func waitFrame(after: Int, timeout: TimeInterval) -> (Int, Data?) {
        frameCond.lock(); defer { frameCond.unlock() }
        if frameSeq <= after && !stopped {
            _ = frameCond.wait(until: Date(timeIntervalSinceNow: timeout))
        }
        return (frameSeq, frame)
    }

    // --- interno ---
    private func post(_ kind: String, _ data: Any?) { handler(self, kind, data) }

    private func readMessage(_ s: TCPSocket) throws -> (UInt8, Data) {
        let head = try s.readExact(5)
        if Proto.looksForeign(head) { throw NetError.foreign(Proto.describeForeign(head, port: port)) }
        let len = (UInt32(head[0]) << 24) | (UInt32(head[1]) << 16) | (UInt32(head[2]) << 8) | UInt32(head[3])
        if len > Proto.maxMessage { throw NetError.foreign(Proto.describeForeign(head, port: port)) }
        let payload = try s.readExact(Int(len))
        return (head[4], Data(payload))
    }

    /// Una connessione + handshake. nil se ok, altrimenti il motivo.
    private func connectOnce() -> String? {
        var s: TCPSocket?
        do {
            s = try TCPSocket.open(host: host, port: port, connectTimeout: NetSession.connectTimeout,
                                   recvTimeout: NetSession.recvTimeout)
            let (type, payload) = try readMessage(s!)
            let h = (type == Proto.hello ? parseJSON(payload) : nil) ?? [:]
            if (h["app"] as? String) != Proto.appId {
                throw NetError.foreign(Proto.describeForeign([], port: port))
            }
            if !remoteConfig.isEmpty {
                try s!.writeAll(Proto.pack(Proto.config, json: remoteConfig))
            }
            stateLock.lock(); sock = s; _hello = h; stateLock.unlock()
            return nil
        } catch NetError.unknownHost {
            s?.closeDescriptor()
            return "invalid address or unknown computer name."
        } catch NetError.refused {
            s?.closeDescriptor()
            return "connection refused: LBS Labs Remote is not running on that computer (port \(port))."
        } catch NetError.timeout {
            s?.closeDescriptor()
            return "no response. Is the computer on and connected to the network? Is LBS Labs Remote "
                + "installed on it? Is a firewall blocking the connection? On iPad, also check that "
                + "Local Network access is allowed for this app in Settings."
        } catch NetError.foreign(let message) {
            s?.closeDescriptor()
            return message
        } catch NetError.closed {
            s?.closeDescriptor()
            return "the remote computer closed the connection immediately"
        } catch NetError.io(let message) {
            s?.closeDescriptor()
            return message
        } catch {
            s?.closeDescriptor()
            return "\(error)"
        }
    }

    private func run() {
        var err = connectOnce()
        if err != nil && !stopped && (err ?? "").hasPrefix("no response") {
            // iPad: alla prima connessione compare la richiesta "Rete locale"; si riprova una volta
            Thread.sleep(forTimeInterval: 1.5)
            err = connectOnce()
        }
        if let e = err {
            post("failed", e)
            return
        }
        post("connected", hello)
        var quickDrops = 0
        while !stopped {
            let started = Date()
            let (kind, reason) = serve()
            if stopped { return }
            if kind == "bye" {
                post("closed", reason)
                return
            }
            quickDrops = Date().timeIntervalSince(started) < NetSession.minSession ? quickDrops + 1 : 0
            if quickDrops >= NetSession.maxQuickDrops {
                // Il computer remoto chiude la connessione appena creata: riprovare di continuo è inutile.
                let detail = lastNotice.isEmpty ? "" : " (\(lastNotice))"
                post("closed", "The remote computer keeps closing the connection right after it is established\(detail). "
                    + "Check LBS Labs Remote on that computer, then connect again.")
                return
            }
            post("reconnecting", reason)
            let deadline = Date().addingTimeInterval(NetSession.reconnectWindow)
            var again: String? = reason
            while !stopped && Date() < deadline {
                Thread.sleep(forTimeInterval: NetSession.reconnectDelay)   // pausa prima di ogni tentativo
                if stopped { return }
                again = connectOnce()
                if again == nil { break }
            }
            if stopped { return }
            if let e = again {
                post("closed", "Connection to \(host) lost: \(e)")
                return
            }
            post("reconnected", hello)
        }
    }

    private func onFrame(_ jpeg: Data) {
        if let size = Proto.jpegSize(jpeg) {
            stateLock.lock(); _size = size; stateLock.unlock()
        }
        frameCond.lock()
        frame = jpeg
        frameSeq += 1
        frameCond.broadcast()
        frameCond.unlock()
        fpsCount += 1
        let now = ProcessInfo.processInfo.systemUptime
        if now - fpsT0 >= 1 {
            stateLock.lock(); _fps = Double(fpsCount) / (now - fpsT0); stateLock.unlock()
            fpsCount = 0
            fpsT0 = now
        }
    }

    /// Serve la connessione finché cade. Restituisce ("bye"|"lost"|"stopped", motivo).
    private func serve() -> (String, String) {
        stateLock.lock(); let s = sock; stateLock.unlock()
        guard let s = s else { return ("lost", "no connection") }
        sendCond.lock(); sendQueue.removeAll(); sendCond.unlock()   // gli input in coda durante la disconnessione sono obsoleti
        let sender = Thread { [weak self] in self?.senderLoop(s) }
        sender.name = "net-sender"
        sender.start()
        defer {
            s.closeDescriptor()
            sendCond.lock(); sendCond.broadcast(); sendCond.unlock()
        }
        do {
            while !stopped {
                let (type, payload) = try readMessage(s)
                switch type {
                case Proto.frame:
                    onFrame(payload)
                case Proto.pong:
                    if let ts = parseJSON(payload)?["ts"] as? Double {
                        let rtt = (ProcessInfo.processInfo.systemUptime - ts) * 1000
                        stateLock.lock()
                        _rtt = _rtt < 0 ? rtt : _rtt * 0.7 + rtt * 0.3
                        stateLock.unlock()
                    }
                case Proto.notice:
                    let notice = parseJSON(payload) ?? [:]
                    stateLock.lock(); lastNotice = String(((notice["text"] as? String) ?? "").prefix(200)); stateLock.unlock()
                    post("notice", notice)
                case Proto.bye:
                    let reason = (parseJSON(payload)?["reason"] as? String) ?? ""
                    return ("bye", reason.isEmpty ? "Session closed by the remote computer." : reason)
                default:
                    break
                }
            }
            return ("stopped", "")
        } catch NetError.timeout {
            return ("lost", "no data from the remote computer for several seconds")
        } catch NetError.closed {
            return ("lost", "connection closed by the other side")
        } catch NetError.foreign(let message) {
            return ("lost", message)
        } catch NetError.io(let message) {
            return ("lost", message)
        } catch {
            return ("lost", "\(error)")
        }
    }

    private func senderLoop(_ s: TCPSocket) {
        var nextPing: TimeInterval = 0
        while !stopped && !s.isAborted {
            let now = ProcessInfo.processInfo.systemUptime
            var batch: [Data] = []
            if now >= nextPing {
                batch.append(Proto.pack(Proto.ping, json: ["ts": now]))
                nextPing = now + NetSession.pingInterval
            }
            sendCond.lock()
            if sendQueue.isEmpty {
                _ = sendCond.wait(until: Date(timeIntervalSinceNow: max(0.01, nextPing - now)))
            }
            batch.append(contentsOf: sendQueue)
            sendQueue.removeAll()
            sendCond.unlock()
            do {
                for m in batch { try s.writeAll(m) }
            } catch {
                s.abort()                                   // sblocca il thread di ricezione
                return
            }
        }
    }
}
