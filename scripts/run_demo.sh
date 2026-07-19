#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

API_HOST="${AI_PRESALES_DEMO_API_HOST:-127.0.0.1}"
API_PORT="${AI_PRESALES_DEMO_API_PORT:-8000}"
UI_PORT="${AI_PRESALES_DEMO_UI_PORT:-8501}"

cleanup() {
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${UI_PID:-}" ]] && kill -0 "$UI_PID" 2>/dev/null; then
    kill "$UI_PID" 2>/dev/null || true
    wait "$UI_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI on http://${API_HOST}:${API_PORT}"
uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" &
API_PID=$!

echo "Starting Streamlit on http://localhost:${UI_PORT}"
streamlit run ui/app.py --server.port "$UI_PORT" --server.headless true &
UI_PID=$!

echo
echo "Demo is running:"
echo "  API:       http://${API_HOST}:${API_PORT}"
echo "  Streamlit: http://localhost:${UI_PORT}"
echo "Press Ctrl+C to stop both processes."

wait -n "$API_PID" "$UI_PID"
