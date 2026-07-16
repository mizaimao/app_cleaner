#!/bin/bash
# Builds AppCleaner and assembles a runnable .app bundle (no Xcode required).
set -euo pipefail

CONFIG="${1:-release}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "▸ swift build -c $CONFIG"
swift build -c "$CONFIG"

BIN_PATH="$(swift build -c "$CONFIG" --show-bin-path)"
APP="$ROOT/build/AppCleaner.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
mkdir -p "$APP/Contents/Resources"

cp "$BIN_PATH/AppCleaner" "$APP/Contents/MacOS/AppCleaner"
cp "$ROOT/Resources/Info.plist" "$APP/Contents/Info.plist"

# Ad-hoc sign so macOS will run it locally without Gatekeeper complaints.
codesign --force --deep --sign - "$APP" 2>/dev/null || true

echo "✓ Built $APP"
echo "  Run it with:  open \"$APP\""
