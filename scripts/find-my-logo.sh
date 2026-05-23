#!/usr/bin/env bash
#
# Ready-to-use one-shot: find → enhance → animate.
#
#   scripts/find-my-logo.sh <logo.png> <mosaic.png> [out-prefix]
#
# Produces <out-prefix>.png (upscaled crop), <out-prefix>.mp4 and <out-prefix>.gif (zoom).
set -euo pipefail

usage() { echo "usage: $(basename "$0") <logo.png> <mosaic.png> [out-prefix]" >&2; exit 1; }

LOGO="${1:-}"; MOSAIC="${2:-}"; OUT="${3:-found}"
[ -n "$LOGO" ] && [ -n "$MOSAIC" ] || usage
[ -f "$LOGO" ]   || { echo "✗ logo not found: $LOGO" >&2; exit 1; }
[ -f "$MOSAIC" ] || { echo "✗ mosaic not found: $MOSAIC" >&2; exit 1; }

# Use the installed CLI, or fall back to `uv run` inside a checkout.
if command -v logo-finder >/dev/null 2>&1; then
  CLI=(logo-finder)
elif command -v uv >/dev/null 2>&1; then
  CLI=(uv run logo-finder)
else
  echo "✗ logo-finder not found. Run ./install.sh first." >&2; exit 1
fi

echo "› Locating $LOGO in $MOSAIC ..."
"${CLI[@]}" find "$LOGO" "$MOSAIC"

echo "› Cropping + upscaling → ${OUT}.png"
"${CLI[@]}" enhance "$LOGO" "$MOSAIC" -o "${OUT}.png" --size 1024

echo "› Rendering zoom → ${OUT}.mp4 / ${OUT}.gif"
"${CLI[@]}" animate "$LOGO" "$MOSAIC" -o "${OUT}.mp4" --gif "${OUT}.gif"

echo "✓ Done: ${OUT}.png, ${OUT}.mp4, ${OUT}.gif"
