#!/usr/bin/env bash
set -e

# fetch_vendor.sh
# Dynamically fetches the required third-party static assets (MathJax & Emojis)
# using npm in a temporary directory and copies them to static/vendor/

# Go to project root
cd "$(dirname "$0")/.."

echo "📦 Fetching dynamic vendor assets..."

# Create a temporary directory for npm
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Prepare vendor destination
VENDOR_DIR="static/vendor"
rm -rf "$VENDOR_DIR"
mkdir -p "$VENDOR_DIR/emoji/data"
mkdir -p "$VENDOR_DIR/mathjax"

cd "$TMP_DIR"
npm init -y > /dev/null
echo "   Installing mathjax@3 and @james_zhan/markdown-emoji..."
npm install --no-save --loglevel=warn mathjax@3 @james_zhan/markdown-emoji > /dev/null

cd - > /dev/null

# -- MathJax: selective copy from es5/ (only the tex-mml-chtml combo and its deps) --
echo "   Copying MathJax assets (selective)..."
MJ="$TMP_DIR/node_modules/mathjax/es5"
cp "$MJ/tex-mml-chtml.js" "$VENDOR_DIR/mathjax/"
cp "$MJ/core.js"          "$VENDOR_DIR/mathjax/"
cp "$MJ/startup.js"       "$VENDOR_DIR/mathjax/"
cp "$MJ/loader.js"        "$VENDOR_DIR/mathjax/"
cp -r "$MJ/input"         "$VENDOR_DIR/mathjax/"
cp -r "$MJ/output"        "$VENDOR_DIR/mathjax/"
cp -r "$MJ/ui"            "$VENDOR_DIR/mathjax/"
cp -r "$MJ/a11y"          "$VENDOR_DIR/mathjax/"

# -- Emoji: preserve data/ subdirectory structure for import.meta.url --
echo "   Copying Emoji mapping assets..."
cp "$TMP_DIR/node_modules/@james_zhan/markdown-emoji/src/index.js" "$VENDOR_DIR/emoji/"
cp "$TMP_DIR/node_modules/@james_zhan/markdown-emoji/src/data/"*   "$VENDOR_DIR/emoji/data/"

echo "✅ Vendor assets successfully populated in $VENDOR_DIR/"
