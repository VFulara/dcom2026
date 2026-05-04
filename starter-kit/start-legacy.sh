#!/usr/bin/env bash
# Start the legacy Planning Board (CDS v6 + OpenUI5)
# Kills any process on port 4004 first, then starts cds watch.

set -e

PORT=4004

echo "=== Planning Board (Legacy) ==="
echo ""

# Kill anything on port 4004
if lsof -i :${PORT} -t >/dev/null 2>&1; then
  echo "Stopping process on port ${PORT}..."
  lsof -i :${PORT} -t | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# Install if node_modules missing
if [ ! -d "node_modules/@sap/cds" ]; then
  echo "Installing dependencies..."
  npm install --silent
fi

echo "Starting at http://localhost:${PORT}"
echo "Open that URL in your browser — the Planning Board loads directly."
echo "(Press Ctrl+C to stop)"
echo ""

npx cds watch
