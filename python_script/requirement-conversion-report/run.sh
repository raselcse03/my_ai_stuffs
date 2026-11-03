#!/usr/bin/env bash
# =============================================================
# run.sh — Entry point for Excel → PDF + Image converter
# Usage:  bash run.sh <path/to/file.xlsx> [--dpi 200]
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/python_script.py"
OUTPUT_DIR="$SCRIPT_DIR/converted requirements"

# ── Validate argument ─────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    echo "Usage: bash run.sh <path/to/file.xlsx> [--dpi 150|200|300]"
    echo ""
    echo "Examples:"
    echo "  bash run.sh requirements.xlsx"
    echo "  bash run.sh /path/to/requirements.xlsx --dpi 300"
    exit 1
fi

EXCEL_FILE="$1"
shift   # consume first argument; remaining args (e.g. --dpi 300) pass through

if [[ ! -f "$EXCEL_FILE" ]]; then
    echo "❌ File not found: $EXCEL_FILE"
    exit 1
fi

# ── Auto-setup if venv is missing ────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    echo "⚙  Virtual environment not found. Running setup first..."
    echo ""
    bash "$SCRIPT_DIR/setup.sh"
    echo ""
fi

# ── Activate venv ────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── macOS: add LibreOffice to PATH if needed ──────────────────
if [[ "$(uname -s)" == "Darwin" ]]; then
    if ! command -v libreoffice &>/dev/null; then
        export PATH="$PATH:/Applications/LibreOffice.app/Contents/MacOS"
    fi
fi

# ── Run converter ─────────────────────────────────────────────
echo "=============================================="
echo "  Excel Converter"
echo "=============================================="
echo "  File   : $EXCEL_FILE"
echo "  Output : $OUTPUT_DIR"
echo "=============================================="
echo ""

python "$PYTHON_SCRIPT" "$EXCEL_FILE" --output "$OUTPUT_DIR" "$@"

DEACTIVATE_CMD=$(command -v deactivate || true)
[[ -n "$DEACTIVATE_CMD" ]] && deactivate || true
