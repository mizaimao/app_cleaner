import SwiftUI

@MainActor
final class CleanerModel: ObservableObject {
    @Published var appName: String?
    @Published var bundleID: String?
    @Published var items: [LeftoverItem] = []
    @Published var isScanning = false
    @Published var statusMessage: String?

    func handleDrop(_ url: URL) {
        guard url.pathExtension.lowercased() == "app" else {
            statusMessage = "That's not an application — drop a .app bundle."
            return
        }

        isScanning = true
        statusMessage = nil
        items = []
        appName = nil
        bundleID = nil

        Task.detached(priority: .userInitiated) {
            let result = LeftoverScanner.scan(appURL: url)
            await MainActor.run {
                self.appName = result.appName
                self.bundleID = result.bundleID
                self.items = result.items.sorted { $0.size > $1.size }
                self.isScanning = false
                self.statusMessage = result.items.count == 1
                    ? "Only the app bundle found — no leftover files matched."
                    : nil
            }
        }
    }

    var totalSelectedSize: Int64 {
        items.filter(\.selected).reduce(0) { $0 + $1.size }
    }

    var selectedCount: Int {
        items.filter(\.selected).count
    }

    func setAll(_ selected: Bool) {
        for i in items.indices { items[i].selected = selected }
    }

    func deleteSelected() {
        let toDelete = items.filter(\.selected)
        guard !toDelete.isEmpty else { return }

        let errors = LeftoverScanner.moveToTrash(toDelete.map(\.url))
        let failedPaths = Set(errors.keys.map(\.path))
        items.removeAll { $0.selected && !failedPaths.contains($0.url.path) }

        let moved = toDelete.count - errors.count
        if errors.isEmpty {
            statusMessage = "Moved \(moved) item(s) to Trash."
        } else {
            statusMessage = "Moved \(moved) to Trash. \(errors.count) failed — grant Full Disk Access in System Settings › Privacy."
        }
    }
}
