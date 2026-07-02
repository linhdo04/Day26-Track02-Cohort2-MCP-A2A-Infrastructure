#!/usr/bin/env bash
# Chọn Python/uvicorn/adk trong môi trường do uv quản lý.

load_dotenv_file() {
  local root="$1"
  local env_file="$root/.env"
  if [[ ! -f "$env_file" ]]; then
    echo "⚠ Không tìm thấy $env_file — GOOGLE_API_KEY có thể thiếu"
    return 0
  fi
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  export GOOGLE_GENAI_USE_VERTEXAI="${GOOGLE_GENAI_USE_VERTEXAI:-FALSE}"
  if [[ -z "${GOOGLE_API_KEY:-}" ]]; then
    echo "⚠ GOOGLE_API_KEY trống trong .env"
  else
    echo "→ .env loaded (GOOGLE_API_KEY set)"
  fi
}

resolve_lab_python() {
  local root="${1:-.}"
  local c candidates=()

  # `uv sync` tạo môi trường tái lập tại .venv.
  if [[ -x "$root/.venv/bin/python" ]]; then
    candidates+=("$root/.venv/bin/python")
  fi
  if command -v python >/dev/null 2>&1; then
    candidates+=("$(command -v python)")
  fi
  if command -v python3 >/dev/null 2>&1; then
    candidates+=("$(command -v python3)")
  fi

  for c in "${candidates[@]}"; do
    [[ -n "$c" && -x "$c" ]] || continue
    if "$c" -c "import google.adk" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

setup_lab_env() {
  local root="${1:?root required}"
  load_dotenv_file "$root"
  LAB_PYTHON="$(resolve_lab_python "$root")" || {
    echo "✗ Không tìm thấy Python có google-adk."
    echo "  Chạy: uv sync --frozen"
    exit 1
  }
  export PYTHONPATH="${PYTHONPATH:-}:$root"
  LAB_BIN="$(dirname "$LAB_PYTHON")"
  # python -m uvicorn — cùng env với google-adk (tránh Homebrew uvicorn)
  LAB_UVICORN=("$LAB_PYTHON" -m uvicorn)
  if [[ -x "$LAB_BIN/adk" ]]; then
    LAB_ADK="$LAB_BIN/adk"
  elif command -v adk >/dev/null 2>&1; then
    LAB_ADK="$(command -v adk)"
  else
    echo "✗ Không tìm thấy lệnh adk trong $LAB_BIN"
    exit 1
  fi
  echo "→ Python: $LAB_PYTHON"
  echo "→ ADK:    $LAB_ADK"
}
