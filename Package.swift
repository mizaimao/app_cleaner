// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "AppCleaner",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "AppCleaner",
            path: "Sources/AppCleaner"
        )
    ]
)
