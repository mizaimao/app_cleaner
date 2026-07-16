import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var model = CleanerModel()
    @State private var isTargeted = false

    var body: some View {
        VStack(spacing: 0) {
            dropZone

            if !model.items.isEmpty {
                Divider()
                itemList
                Divider()
                footer
            } else if let status = model.statusMessage {
                Text(status)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .padding()
            }
        }
        .frame(minWidth: 560, minHeight: 480)
    }

    // MARK: - Drop zone

    private var dropZone: some View {
        VStack(spacing: 8) {
            if model.isScanning {
                ProgressView()
                Text("Scanning…")
            } else if let name = model.appName {
                Image(systemName: "app.dashed")
                    .font(.system(size: 34))
                    .foregroundStyle(.secondary)
                Text(name).font(.headline)
                if let bid = model.bundleID, !bid.isEmpty {
                    Text(bid).font(.caption).foregroundStyle(.secondary)
                }
                Text("Drop another app to rescan").font(.caption2).foregroundStyle(.tertiary)
            } else {
                Image(systemName: "arrow.down.app")
                    .font(.system(size: 40))
                    .foregroundStyle(.secondary)
                Text("Drag an app here").font(.headline)
                Text("Finds its leftover files and lets you trash them")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: model.items.isEmpty ? 460 : 130)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(isTargeted ? Color.accentColor.opacity(0.12) : Color.clear)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(isTargeted ? Color.accentColor : Color.secondary.opacity(0.3),
                              style: StrokeStyle(lineWidth: 2, dash: [7]))
                .padding(8)
        )
        .onDrop(of: [UTType.fileURL], isTargeted: $isTargeted) { providers in
            handleProviders(providers)
        }
    }

    private func handleProviders(_ providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first else { return false }
        provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
            var url: URL?
            if let data = item as? Data {
                url = URL(dataRepresentation: data, relativeTo: nil)
            } else if let u = item as? URL {
                url = u
            }
            if let url {
                Task { @MainActor in model.handleDrop(url) }
            }
        }
        return true
    }

    // MARK: - Item list

    private var itemList: some View {
        List {
            ForEach($model.items) { $item in
                HStack(spacing: 10) {
                    Toggle("", isOn: $item.selected).labelsHidden()
                    VStack(alignment: .leading, spacing: 1) {
                        Text(item.displayName).lineLimit(1)
                        Text(item.path)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                    }
                    Spacer()
                    Text(item.category)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(ByteCountFormatter.string(fromByteCount: item.size, countStyle: .file))
                        .monospacedDigit()
                        .frame(width: 78, alignment: .trailing)
                }
            }
        }
        .listStyle(.inset)
    }

    // MARK: - Footer

    private var footer: some View {
        HStack {
            Button("All") { model.setAll(true) }
            Button("None") { model.setAll(false) }
            Spacer()
            if let status = model.statusMessage {
                Text(status).font(.caption).foregroundStyle(.secondary)
                Spacer()
            }
            Text("\(model.selectedCount) selected · \(ByteCountFormatter.string(fromByteCount: model.totalSelectedSize, countStyle: .file))")
                .font(.callout)
                .foregroundStyle(.secondary)
            Button {
                model.deleteSelected()
            } label: {
                Label("Move to Trash", systemImage: "trash")
            }
            .buttonStyle(.borderedProminent)
            .disabled(model.selectedCount == 0)
        }
        .padding(12)
    }
}
