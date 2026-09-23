#!/bin/bash
# SMPF Deploy Helper — pushes to GitHub, triggers Render deploy

echo "=== SMPF Backend Deploy ==="
echo ""

cd /c/Users/RudiOosthuizen/smpf || exit 1

echo "[1/4] Adding changes..."
git add -A

echo "[2/4] Committing..."
git commit -m "SMPF deploy: $(date '+%Y-%m-%d %H:%M')"

echo "[3/4] Pushing to GitHub..."
git push origin main

echo "[4/4] Done! Render will auto-deploy from GitHub."
echo ""
echo "Monitor deploy at: https://dashboard.render.com"
