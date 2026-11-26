import Foundation

/// Protocollo di rete di LBS Labs Remote (specifica: lbsremote/protocol.py).
/// Ogni messaggio: 4 byte big-endian con la lunghezza del payload + 1 byte di tipo + payload.
enum Proto {
    static let appId = "lbslabs-remote"
    static let defaultPort = 5970
    static let maxMessage: UInt32 = 64 * 1024 * 1024

    // server -> client
    static let hello: UInt8 = 1
    static let frame: UInt8 = 2
    static let pong: UInt8 = 3
    static let notice: UInt8 = 4
    static let bye: UInt8 = 5
    // client -> server
    static let input: UInt8 = 10
    static let ping: UInt8 = 11
    static let config: UInt8 = 12

    static func pack(_ type: UInt8, _ payload: Data) -> Data {
        var d = Data(capacity: 5 + payload.count)
        let n = UInt32(payload.count)
        d.append(UInt8((n >> 24) & 0xFF))
        d.append(UInt8((n >> 16) & 0xFF))
        d.append(UInt8((n >> 8) & 0xFF))
        d.append(UInt8(n & 0xFF))
        d.append(type)
        d.append(payload)
        return d
    }

    static func pack(_ type: UInt8, json: Any) -> Data {
        return pack(type, Data(jsonString(json).utf8))
    }

    static func looksForeign(_ head: [UInt8]) -> Bool {
        let s = String(decoding: head.prefix(4), as: UTF8.self)
        return s.hasPrefix("RFB") || s.hasPrefix("HTTP") || s.hasPrefix("SSH-")
    }

    static func describeForeign(_ head: [UInt8], port: Int) -> String {
        if String(decoding: head.prefix(3), as: UTF8.self) == "RFB" {
            return "another remote control program (VNC, e.g. macOS Screen Sharing) is answering on port \(port), "
                + "not LBS Labs Remote. Update LBS Labs Remote to the latest version on both computers, "
                + "or turn off Screen Sharing on the remote computer."
        }
        return "another program is answering on port \(port), not LBS Labs Remote."
    }

    /// Larghezza e altezza di un JPEG leggendo l'intestazione (senza decodificarlo).
    static func jpegSize(_ d: Data) -> (Int, Int)? {
        let b = [UInt8](d.prefix(65536))
        var i = 2
        while i + 9 < b.count {
            if b[i] != 0xFF { i += 1; continue }
            let marker = b[i + 1]
            if marker == 0xC0 || marker == 0xC1 || marker == 0xC2 {
                let h = (Int(b[i + 5]) << 8) | Int(b[i + 6])
                let w = (Int(b[i + 7]) << 8) | Int(b[i + 8])
                return (w, h)
            }
            if marker == 0xD8 || marker == 0x01 || (marker >= 0xD0 && marker <= 0xD7) { i += 2; continue }
            i += 2 + ((Int(b[i + 2]) << 8) | Int(b[i + 3]))
        }
        return nil
    }

    /// "192.168.1.5" → (host, default); "192.168.1.5:6000" → (host, 6000); "[::1]:5970".
    static func parseHostPort(_ raw: String, defaultPort: Int) -> (String, Int)? {
        let text = raw.trimmingCharacters(in: .whitespaces)
        if text.isEmpty { return nil }
        func port(_ s: String) -> Int? {
            guard let p = Int(s.trimmingCharacters(in: .whitespaces)), p >= 1, p <= 65535 else { return nil }
            return p
        }
        if text.hasPrefix("[") {
            guard let close = text.firstIndex(of: "]") else { return nil }
            let host = String(text[text.index(after: text.startIndex)..<close])
            let rest = String(text[text.index(after: close)...])
            if rest.hasPrefix(":") {
                guard let p = port(String(rest.dropFirst())) else { return nil }
                return (host, p)
            }
            return (host, defaultPort)
        }
        let colons = text.filter { $0 == ":" }.count
        if colons == 1 {
            let parts = text.split(separator: ":", maxSplits: 1, omittingEmptySubsequences: false)
            guard parts.count == 2, let p = port(String(parts[1])) else { return nil }
            return (String(parts[0]).trimmingCharacters(in: .whitespaces), p)
        }
        return (text, defaultPort)
    }
}

func jsonString(_ obj: Any) -> String {
    guard JSONSerialization.isValidJSONObject(obj),
          let d = try? JSONSerialization.data(withJSONObject: obj, options: []),
          let s = String(data: d, encoding: .utf8) else { return "null" }
    return s
}

func parseJSON(_ data: Data) -> [String: Any]? {
    return (try? JSONSerialization.jsonObject(with: data, options: [])) as? [String: Any]
}
