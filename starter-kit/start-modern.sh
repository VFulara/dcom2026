#!/usr/bin/env bash
# Start the modernised Planning Board (CDS v9 at port 4005 + React/Vite at port 5173)
# The legacy app continues running on port 4004 — both versions can run simultaneously.
# Run ./start-legacy.sh first if you want to compare both side by side.

set -e

BACKEND_PORT=4005
FRONTEND_PORT=5173
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODERN_DIR="${SCRIPT_DIR}/modern"

echo "=== Planning Board (Modernised) ==="
echo ""

if [ ! -d "${MODERN_DIR}" ]; then
  echo "Error: modern/ directory not found. Complete Phase 2 first."
  exit 1
fi

if [ ! -d "${MODERN_DIR}/ui" ]; then
  echo "Error: modern/ui/ directory not found. Ensure Phase 2 Agent B has completed."
  exit 1
fi

# Kill anything on required ports
for PORT in ${BACKEND_PORT} ${FRONTEND_PORT}; do
  if lsof -i :${PORT} -t >/dev/null 2>&1; then
    echo "Stopping process on port ${PORT}..."
    lsof -i :${PORT} -t | xargs kill -9 2>/dev/null || true
  fi
done
sleep 1

# Install modern backend deps if needed
if [ ! -d "${MODERN_DIR}/node_modules/@sap/cds" ]; then
  echo "Installing modern backend dependencies..."
  (cd "${MODERN_DIR}" && npm install --silent)
fi

# Install modern frontend deps if needed
if [ ! -d "${MODERN_DIR}/ui/node_modules" ]; then
  echo "Installing modern frontend dependencies..."
  (cd "${MODERN_DIR}/ui" && npm install --silent)
fi

echo ""
echo "Starting CDS v9 backend on http://localhost:${BACKEND_PORT}..."
(cd "${MODERN_DIR}" && npx cds watch) &
BACKEND_PID=$!

# Give the backend a moment to bind before Vite proxy tries to connect
sleep 3

echo "Starting Vite frontend on http://localhost:${FRONTEND_PORT}..."
(cd "${MODERN_DIR}/ui" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Modern app at  http://localhost:${FRONTEND_PORT}"
echo "Modern API at  http://localhost:${BACKEND_PORT}/odata/v4/backlog/"
echo "Legacy app at  http://localhost:4004  (run ./start-legacy.sh to start it)"
echo ""
echo "Press Ctrl+C to stop both modern servers"

trap "echo ''; echo 'Stopping modern servers...'; kill ${BACKEND_PID} ${FRONTEND_PID} 2>/dev/null; exit 0" INT

wait ${BACKEND_PID} ${FRONTEND_PID}
