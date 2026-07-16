import Foundation

/// One leftover file or folder that appears to belong to the dropped app.
struct LeftoverItem: Identifiable {
    let id = UUID()
    let url: URL
    let category: String
    var size: Int64
    var selected: Bool = true

    var displayName: String { url.lastPathComponent }
    var path: String { url.path }
}

struct ScanResult {
    var appName: String
    var bundleID: String
    var items: [LeftoverItem]
}

/// Finds files/folders that *most likely* belong to an app, by matching the
/// bundle identifier and app name against the standard macOS Library locations.
///
/// Note: macOS keeps no retroactive "app X created file Y" log, so this is
/// heuristic matching — the same approach AppCleaner / PearCleaner use.
enum LeftoverScanner {

    static func scan(appURL: URL) -> ScanResult {
        let fm = FileManager.default
        let plistURL = appURL.appendingPathComponent("Contents/Info.plist")

        var bundleID = ""
        var appName = appURL.deletingPathExtension().lastPathComponent

        if let data = try? Data(contentsOf: plistURL),
           let plist = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any] {
            bundleID = (plist["CFBundleIdentifier"] as? String) ?? ""
            if let name = plist["CFBundleName"] as? String, !name.isEmpty {
                appName = name
            }
        }

        var items: [LeftoverItem] = []

        // The application bundle itself is always the first candidate.
        items.append(makeItem(url: appURL, category: "Application"))

        let home = fm.homeDirectoryForCurrentUser
        let userLib = home.appendingPathComponent("Library")
        let sysLib = URL(fileURLWithPath: "/Library")

        let searchDirs: [(URL, String)] = [
            (userLib.appendingPathComponent("Application Support"), "Application Support"),
            (userLib.appendingPathComponent("Caches"), "Cache"),
            (userLib.appendingPathComponent("Preferences"), "Preferences"),
            (userLib.appendingPathComponent("Containers"), "Container"),
            (userLib.appendingPathComponent("Group Containers"), "Group Container"),
            (userLib.appendingPathComponent("Saved Application State"), "Saved State"),
            (userLib.appendingPathComponent("Logs"), "Logs"),
            (userLib.appendingPathComponent("HTTPStorages"), "HTTP Storage"),
            (userLib.appendingPathComponent("WebKit"), "WebKit"),
            (userLib.appendingPathComponent("Cookies"), "Cookies"),
            (userLib.appendingPathComponent("LaunchAgents"), "Launch Agent"),
            (userLib.appendingPathComponent("Application Scripts"), "Application Scripts"),
            (sysLib.appendingPathComponent("Application Support"), "Application Support (System)"),
            (sysLib.appendingPathComponent("Caches"), "Cache (System)"),
            (sysLib.appendingPathComponent("Preferences"), "Preferences (System)"),
            (sysLib.appendingPathComponent("LaunchAgents"), "Launch Agent (System)"),
            (sysLib.appendingPathComponent("LaunchDaemons"), "Launch Daemon (System)"),
            (sysLib.appendingPathComponent("PrivilegedHelperTools"), "Helper Tool (System)"),
        ]

        let bid = bundleID.lowercased()
        let aname = appName.lowercased()

        // A name matches if it is the bundle id (or a dotted/dashed extension of
        // it, e.g. "com.foo.Bar.plist"), or a folder named exactly after the app.
        func matches(_ name: String) -> Bool {
            let n = name.lowercased()
            if !bid.isEmpty && (n == bid || n.hasPrefix(bid + ".") || n.hasPrefix(bid + "-")) {
                return true
            }
            // Name-based match for folders named after the app. Skip very short
            // names ("Notes", "Mail") to avoid clobbering unrelated data.
            if aname.count >= 4 {
                let base = (n as NSString).deletingPathExtension
                if base == aname { return true }
            }
            return false
        }

        for (dir, category) in searchDirs {
            guard let children = try? fm.contentsOfDirectory(
                at: dir,
                includingPropertiesForKeys: nil,
                options: [.skipsHiddenFiles]
            ) else { continue }

            for child in children where matches(child.lastPathComponent) {
                items.append(makeItem(url: child, category: category))
            }
        }

        // De-dupe by resolved path.
        var seen = Set<String>()
        let unique = items.filter { seen.insert($0.url.path).inserted }

        return ScanResult(appName: appName, bundleID: bundleID, items: unique)
    }

    private static func makeItem(url: URL, category: String) -> LeftoverItem {
        LeftoverItem(url: url, category: category, size: size(of: url))
    }

    /// Recursive allocated size, in bytes. Cheap for files, walks folders.
    static func size(of url: URL) -> Int64 {
        let fm = FileManager.default
        var isDir: ObjCBool = false
        guard fm.fileExists(atPath: url.path, isDirectory: &isDir) else { return 0 }

        if !isDir.boolValue {
            let v = try? url.resourceValues(forKeys: [.totalFileAllocatedSizeKey])
            return Int64(v?.totalFileAllocatedSize ?? 0)
        }

        var total: Int64 = 0
        if let e = fm.enumerator(
            at: url,
            includingPropertiesForKeys: [.totalFileAllocatedSizeKey, .isRegularFileKey],
            options: []
        ) {
            for case let f as URL in e {
                let v = try? f.resourceValues(forKeys: [.totalFileAllocatedSizeKey, .isRegularFileKey])
                if v?.isRegularFile == true {
                    total += Int64(v?.totalFileAllocatedSize ?? 0)
                }
            }
        }
        return total
    }

    /// Moves items to the Trash (recoverable). Returns any per-URL failures.
    static func moveToTrash(_ urls: [URL]) -> [URL: Error] {
        var errors: [URL: Error] = [:]
        for url in urls {
            do {
                try FileManager.default.trashItem(at: url, resultingItemURL: nil)
            } catch {
                errors[url] = error
            }
        }
        return errors
    }
}
