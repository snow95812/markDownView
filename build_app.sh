#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_SVG="$ROOT_DIR/assets/app-icon.svg"
ICON_PNG="$ROOT_DIR/assets/app-icon-rendered.png"
ICONSET_DIR="$ROOT_DIR/assets/app-icon.iconset"
ICON_ICNS="$ROOT_DIR/assets/app-icon.icns"

echo "Installing packaging dependency..."
python3 -m pip install -r "$ROOT_DIR/requirements.txt"

if [ -f "$ICON_PNG" ] || [ -f "$ICON_SVG" ]; then
  echo "Generating macOS icon..."
  rm -rf "$ICONSET_DIR" /tmp/markdown_icon_build
  mkdir -p "$ICONSET_DIR" /tmp/markdown_icon_build
  if [ -f "$ICON_PNG" ]; then
    cp "$ICON_PNG" "$ICONSET_DIR/icon_512x512@2x.png"
  else
    qlmanage -t -s 1024 -o /tmp/markdown_icon_build "$ICON_SVG" >/dev/null
    cp "/tmp/markdown_icon_build/app-icon.svg.png" "$ICONSET_DIR/icon_512x512@2x.png"
  fi
  sips -z 16 16 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
  sips -z 32 32 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
  sips -z 64 64 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
  sips -z 256 256 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
  sips -z 512 512 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$ICONSET_DIR/icon_512x512@2x.png" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
  iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"
fi

echo "Cleaning previous build output..."
rm -rf "$ROOT_DIR/build" "$ROOT_DIR/dist" "$ROOT_DIR/__pycache__" "$ROOT_DIR/.pyinstaller" "$ROOT_DIR/Markdown Parser.spec"

echo "Building macOS app..."
export PYINSTALLER_CONFIG_DIR="$ROOT_DIR/.pyinstaller"
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "Markdown Parser" \
  --icon "$ICON_ICNS" \
  --hidden-import "WebKit" \
  --add-data "$ROOT_DIR/assets:assets" \
  "$ROOT_DIR/app.py"

echo "Done."
echo "App path: $ROOT_DIR/dist/Markdown Parser.app"
