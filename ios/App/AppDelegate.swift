import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let w = UIWindow(frame: UIScreen.main.bounds)
        w.rootViewController = ViewController()
        w.backgroundColor = UIColor(lbs: LBSTokens.bgWindow)
        w.makeKeyAndVisible()
        window = w
        return true
    }
}

extension UIColor {
    /// Colore da un token dello stile LBS (0xRRGGBB, generato in Generated/Tokens.swift).
    convenience init(lbs rgb: UInt32) {
        self.init(red: CGFloat((rgb >> 16) & 0xFF) / 255,
                  green: CGFloat((rgb >> 8) & 0xFF) / 255,
                  blue: CGFloat(rgb & 0xFF) / 255,
                  alpha: 1)
    }
}
