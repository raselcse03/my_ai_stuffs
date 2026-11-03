#!/usr/bin/env bash
# =============================================================
# setup.sh — Install all dependencies for excel_converter
# =============================================================
set -euo pipefail

echo "=============================================="
echo "  Excel Converter — Dependency Setup"
echo "=============================================="

# ── 1. Detect OS ──────────────────────────────────────────────
OS="$(uname -s)"
echo "Detected OS: $OS"

# ── 2. System packages ────────────────────────────────────────
install_system_packages() {
    echo ""
    echo "[1/3] Installing system packages..."

    if [[ "$OS" == "Linux" ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq
            sudo apt-get install -y \
                libreoffice \
                libreoffice-calc \
                poppler-utils \
                python3 \
                python3-pip \
                python3-venv
        elif command -v yum &>/dev/null; then
            sudo yum install -y \
                libreoffice \
                poppler-utils \
                python3 \
                python3-pip
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y \
                libreoffice \
                poppler-utils \
                python3 \
                python3-pip
        else
            echo "⚠  Unknown Linux package manager. Please install manually:"
            echo "   - libreoffice"
            echo "   - poppler-utils"
            echo "   - python3 & python3-pip"
        fi

    elif [[ "$OS" == "Darwin" ]]; then
        if ! command -v brew &>/dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        echo "Installing LibreOffice and poppler via Homebrew..."
        brew install --cask libreoffice 2>/dev/null || echo "(LibreOffice already installed or skipped)"
        brew install poppler python3
    else
        echo "⚠  Unsupported OS: $OS"
        echo "   Please install LibreOffice and poppler-utils manually."
    fi
}

# ── 3. Python virtual environment ─────────────────────────────
setup_venv() {
    echo ""
    echo "[2/3] Setting up Python virtual environment..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VENV_DIR="$SCRIPT_DIR/venv"

    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        echo "  Created venv at $VENV_DIR"
    else
        echo "  venv already exists at $VENV_DIR"
    fi

    # Activate and install Python packages
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    echo ""
    echo "[3/3] Installing Python packages..."
    pip install --upgrade pip -q
    pip install \
        openpyxl \
        pdf2image \
        Pillow

    echo ""
    echo "  Python packages installed:"
    pip show openpyxl pdf2image Pillow | grep -E "^(Name|Version):"

    deactivate
}

# ── 4. Verify LibreOffice ──────────────────────────────────────
verify_libreoffice() {
    echo ""
    if command -v libreoffice &>/dev/null; then
        LO_VER=$(libreoffice --version 2>/dev/null | head -1)
        echo "✔ LibreOffice found: $LO_VER"
    elif command -v soffice &>/dev/null; then
        LO_VER=$(soffice --version 2>/dev/null | head -1)
        echo "✔ LibreOffice (soffice) found: $LO_VER"
    else
        echo "⚠  LibreOffice not found in PATH."
        echo "   On macOS, try: export PATH=\"\$PATH:/Applications/LibreOffice.app/Contents/MacOS\""
        echo "   On Linux, try: sudo apt-get install libreoffice"
    fi
}

# ── Run all steps ─────────────────────────────────────────────
install_system_packages
setup_venv
verify_libreoffice

echo ""
echo "=============================================="
echo "  ✅ Setup complete! Run: bash run.sh <your_excel_file.xlsx>"
echo "=============================================="
