#!/bin/bash

echo "=========================================="
echo "  JIRA Worklog Report - Setup"
echo "=========================================="

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    sudo apt update
    sudo apt install python3-full python3-venv -y
else
    echo "✅ Python3 found: $(python3 --version)"
fi

# Create virtual environment
VENV_DIR="$(dirname "$0")/venv"

if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment already exists at: $VENV_DIR"
    read -p "   Recreate? (y/n): " choice
    if [ "$choice" = "y" ]; then
        rm -rf "$VENV_DIR"
    else
        echo "✅ Using existing virtual environment."
        source "$VENV_DIR/bin/activate"
        pip install --upgrade jira openpyxl configparser autocorrect
        deactivate
        echo ""
        echo "✅ Setup complete! Run: ./run.sh"
        exit 0
    fi
fi

echo ""
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "📦 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install jira openpyxl configparser autocorrect

echo ""
echo "✅ Installed packages:"
pip list | grep -E "jira|openpyxl|configparser|autocorrect"

deactivate

echo ""
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "  Next steps:"
echo "  1. Edit config.ini with your JIRA details"
echo "  2. Run: ./run.sh"
echo ""