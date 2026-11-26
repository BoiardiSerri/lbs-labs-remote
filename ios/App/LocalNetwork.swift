import Foundation
import Network

/// Fa comparire subito, all'apertura dell'app, la richiesta "Rete locale" di iPadOS (invece che alla
/// prima connessione) e riconosce quando l'utente l'ha rifiutata.
/// Funziona con una ricerca Bonjour del servizio dichiarato in Info.plist (NSBonjourServices).
final class LocalNetworkPermission {
    /// Chiamata (sul thread principale) quando l'utente ha negato l'accesso alla rete locale.
    var onDenied: (() -> Void)?
    private var browser: NWBrowser?

    func request() {
        let b = NWBrowser(for: .bonjour(type: "_lbsremote._tcp", domain: nil), using: .tcp)
        b.stateUpdateHandler = { [weak self] state in
            NSLog("LBS local network: %@", String(describing: state))
            if case .waiting(let error) = state, "\(error)".contains("PolicyDenied") || "\(error)".contains("-65570") {
                DispatchQueue.main.async { self?.onDenied?() }
            }
        }
        b.browseResultsChangedHandler = { _, _ in }
        b.start(queue: .main)
        browser = b
        // la richiesta compare subito: dopo qualche secondo la ricerca non serve più
        DispatchQueue.main.asyncAfter(deadline: .now() + 30) { [weak self] in
            self?.browser?.cancel()
            self?.browser = nil
        }
    }
}
