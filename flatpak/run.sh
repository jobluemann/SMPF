#!/bin/sh
# Run AIPLATFORMFREE desktop app (Electron).
# --no-sandbox is required inside flatpak because Chromium's sandbox
# conflicts with flatpak's own sandbox.
# --disable-gpu-sandbox and --use-gl=swiftshader keep rendering stable
# on systems without working GPU acceleration.
exec /app/aiplatformfree-console/aiplatformfree-console \
  --no-sandbox \
  --disable-gpu \
  "$@"
