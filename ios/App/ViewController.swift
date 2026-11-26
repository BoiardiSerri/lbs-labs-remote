import UIKit
import WebKit

/// Finestra dell'app: mostra l'interfaccia web (www/, la stessa del desktop) in una WKWebView
/// e collega la pagina al codice di rete (AppCore). I frame arrivano con la stessa richiesta
/// "frame?after=N" del desktop, servita da un URL scheme proprio (lbs://app/...), senza server.
final class ViewController: UIViewController, WKScriptMessageHandlerWithReply, WKURLSchemeHandler, WKNavigationDelegate, CoreHost {
    private var webView: WKWebView!
    private var core: AppCore!
    private let localNetwork = LocalNetworkPermission()
    private var fullscreen = false
    // una sola coda: l'ordine degli input (pressione/rilascio) deve essere rispettato
    private let calls = DispatchQueue(label: "lbs.calls")
    private let liveLock = NSLock()
    private var live = Set<ObjectIdentifier>()
    private lazy var wwwDir: URL = Bundle.main.resourceURL!.appendingPathComponent("www").standardizedFileURL

    // --- vista ---
    override func loadView() {
        let config = WKWebViewConfiguration()
        config.setURLSchemeHandler(self, forURLScheme: "lbs")
        config.userContentController.addScriptMessageHandler(self, contentWorld: .page, name: "lbsNative")
        config.allowsInlineMediaPlayback = true
        config.dataDetectorTypes = []
        let wv = WKWebView(frame: .zero, configuration: config)
        let bg = UIColor(lbs: LBSTokens.bgWindow)
        wv.isOpaque = false
        wv.backgroundColor = bg
        wv.scrollView.backgroundColor = bg
        wv.scrollView.isScrollEnabled = false
        wv.scrollView.bounces = false
        wv.scrollView.contentInsetAdjustmentBehavior = .never
        wv.allowsLinkPreview = false
        wv.navigationDelegate = self
        webView = wv
        view = wv
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
        // argomenti di avvio per le prove automatiche: -LBSConnect <indirizzo> -LBSSelfTest 1
        let defaults = UserDefaults.standard
        core = AppCore(host: self, version: version,
                       connectNow: defaults.string(forKey: "LBSConnect") ?? "",
                       selfTest: defaults.bool(forKey: "LBSSelfTest"))
        localNetwork.onDenied = { [weak self] in self?.core.localNetworkDenied = true }
        localNetwork.request()
        webView.load(URLRequest(url: URL(string: "lbs://app/index.html")!))
    }

    override var preferredStatusBarStyle: UIStatusBarStyle { return .lightContent }
    override var prefersStatusBarHidden: Bool { return fullscreen }
    override var prefersHomeIndicatorAutoHidden: Bool { return fullscreen }

    // --- CoreHost ---
    func emit(_ json: String) {
        DispatchQueue.main.async {
            self.webView.evaluateJavaScript("window.LBS&&window.LBS.onEvent(\(json))", completionHandler: nil)
        }
    }

    func setFullscreen(_ on: Bool) {
        DispatchQueue.main.async {
            self.fullscreen = on
            self.setNeedsStatusBarAppearanceUpdate()
            self.setNeedsUpdateOfHomeIndicatorAutoHidden()
        }
    }

    // --- la pagina non esce mai dall'app ---
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(navigationAction.request.url?.scheme == "lbs" ? .allow : .cancel)
    }

    // --- chiamate JavaScript → Swift (risposta come Promise) ---
    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage,
                               replyHandler: @escaping (Any?, String?) -> Void) {
        guard let body = message.body as? [String: Any], let method = body["method"] as? String else {
            replyHandler(nil, "bad message")
            return
        }
        let args = body["args"] as? [Any] ?? []
        calls.async {
            let result = self.core.call(method, args)
            DispatchQueue.main.async { replyHandler(result, nil) }
        }
    }

    // --- URL scheme lbs://app/... : pagina, stile e frame ---
    private func isLive(_ task: WKURLSchemeTask) -> Bool {
        liveLock.lock(); defer { liveLock.unlock() }
        return live.contains(ObjectIdentifier(task as AnyObject))
    }

    private func setLive(_ task: WKURLSchemeTask, _ on: Bool) {
        liveLock.lock(); defer { liveLock.unlock() }
        if on { live.insert(ObjectIdentifier(task as AnyObject)) } else { live.remove(ObjectIdentifier(task as AnyObject)) }
    }

    func webView(_ webView: WKWebView, start urlSchemeTask: WKURLSchemeTask) {
        guard let url = urlSchemeTask.request.url else {
            urlSchemeTask.didFailWithError(URLError(.badURL))
            return
        }
        setLive(urlSchemeTask, true)
        if url.path == "/frame" {
            DispatchQueue.global(qos: .userInitiated).async { self.serveFrame(urlSchemeTask, url) }
        } else {
            serveFile(urlSchemeTask, url)
        }
    }

    func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask) {
        setLive(urlSchemeTask, false)
    }

    private func respond(_ task: WKURLSchemeTask, _ url: URL, status: Int, type: String, body: Data,
                         extra: [String: String] = [:]) {
        DispatchQueue.main.async {
            guard self.isLive(task) else { return }
            var headers = ["Content-Type": type, "Content-Length": String(body.count), "Cache-Control": "no-store"]
            for (k, v) in extra { headers[k] = v }
            if let resp = HTTPURLResponse(url: url, statusCode: status, httpVersion: "HTTP/1.1", headerFields: headers) {
                task.didReceive(resp)
                if !body.isEmpty { task.didReceive(body) }
                task.didFinish()
            } else {
                task.didFailWithError(URLError(.cannotParseResponse))
            }
            self.setLive(task, false)
        }
    }

    private static let mimeTypes = [
        "html": "text/html; charset=utf-8", "js": "text/javascript", "css": "text/css",
        "svg": "image/svg+xml", "ttf": "font/ttf", "png": "image/png", "json": "application/json",
    ]

    private func serveFile(_ task: WKURLSchemeTask, _ url: URL) {
        var path = url.path
        if path.isEmpty || path == "/" { path = "/index.html" }
        let file = wwwDir.appendingPathComponent(String(path.dropFirst())).standardizedFileURL
        guard file.path.hasPrefix(wwwDir.path + "/"), let data = try? Data(contentsOf: file) else {
            respond(task, url, status: 404, type: "text/plain", body: Data())
            return
        }
        let mime = ViewController.mimeTypes[file.pathExtension.lowercased()] ?? "application/octet-stream"
        respond(task, url, status: 200, type: mime, body: data)
    }

    /// Risposta alla richiesta "frame?after=N": attende un frame più recente (fino a 1 s).
    private func serveFrame(_ task: WKURLSchemeTask, _ url: URL) {
        guard let s = core.session else {
            respond(task, url, status: 404, type: "text/plain", body: Data())
            return
        }
        var after = 0
        if let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems,
           let v = items.first(where: { $0.name == "after" })?.value, let n = Int(v) {
            after = n
        }
        if after > s.currentSeq() { after = 0 }            // sessione nuova
        let (seq, jpeg) = s.waitFrame(after: after, timeout: 1.0)
        if let jpeg = jpeg, seq > after {
            respond(task, url, status: 200, type: "image/jpeg", body: jpeg, extra: ["X-Seq": String(seq)])
        } else {
            respond(task, url, status: 204, type: "image/jpeg", body: Data())
        }
    }
}
