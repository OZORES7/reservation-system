#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

if [ -x "./venv/bin/python" ] && "./venv/bin/python" -V >/dev/null 2>&1; then
  PYTHON="./venv/bin/python"
elif [ -x "./venv/Scripts/python.exe" ] && "./venv/Scripts/python.exe" -V >/dev/null 2>&1; then
  PYTHON="./venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

"$PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 &
API_PID=$!

"$PYTHON" -m http.server 3000 --bind 127.0.0.1 &
WEB_PID=$!

cleanup() {
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

echo "Frontend: http://127.0.0.1:3000"
echo "API:      http://127.0.0.1:8000"
echo "Press Ctrl+C to stop both servers."

wait "$API_PID" "$WEB_PID"
