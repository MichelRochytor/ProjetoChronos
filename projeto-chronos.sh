#!/usr/bin/env bash
# ==============================================================================
# Projeto Chronos ⚡ — Ponto de Entrada da Aplicação Desktop
# Executa a aplicação utilizando o interpretador virtual isolado (.venv)
# ==============================================================================
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$APP_DIR"

# Sincroniza rapidamente possíveis atualizações da pasta dados/ vindas do GitHub Actions (18h e 00h)
if command -v git >/dev/null 2>&1 && [ -d "$APP_DIR/.git" ]; then
    timeout 5 git pull --ff-only --quiet 2>/dev/null || true
fi

PYTHON_BIN="$APP_DIR/.venv/bin/python"
MAIN_SCRIPT="$APP_DIR/ProjetoChronos.py"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$MAIN_SCRIPT" "$@"
