#!/bin/bash
# Builds Resources/AppCleaner.icns from the 1024x1024 master Resources/AppIcon.png.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/Resources/AppIcon.png"
SET="$(mktemp -d)/AppCleaner.iconset"
mkdir -p "$SET"

# name          size
render() { sips -z "$2" "$2" "$SRC" --out "$SET/icon_$1.png" >/dev/null; }
render 16x16        16
render 16x16@2x     32
render 32x32        32
render 32x32@2x     64
render 128x128      128
render 128x128@2x   256
render 256x256      256
render 256x256@2x   512
render 512x512      512
render 512x512@2x   1024

iconutil -c icns "$SET" -o "$ROOT/Resources/AppCleaner.icns"
rm -rf "$(dirname "$SET")"
echo "✓ Built Resources/AppCleaner.icns"
