#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Auto-setup if venv is missing
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️  Virtual environment not found. Running setup..."
    echo ""
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install jira openpyxl configparser autocorrect
    deactivate
    echo ""
    echo "✅ Setup complete."
    echo ""
fi

# Install missing packages if venv exists but packages are incomplete
source "$VENV_DIR/bin/activate"
python -c "import jira, openpyxl, autocorrect" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing missing dependencies..."
    pip install --upgrade jira openpyxl configparser autocorrect
fi
deactivate

# Check if config exists
if [ ! -f "$SCRIPT_DIR/config.ini" ]; then
    echo "❌ config.ini not found!"
    echo "   Please create config.ini with your JIRA details."
    exit 1
fi

echo "=========================================="
echo "  JIRA Worklog Report - Running"
echo "=========================================="

# Activate and run
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/worklog_report.py"
EXIT_CODE=$?
deactivate

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ Report generated successfully!"
    echo "=========================================="
    
    # Find the generated file
    EXCEL_FILE=$(ls -t "$SCRIPT_DIR"/Worklog_*.xlsx 2>/dev/null | head -1)
    if [ -n "$EXCEL_FILE" ]; then
        echo "  📄 File: $EXCEL_FILE"
        echo ""
        
        # Try to open the file
        if command -v xdg-open &> /dev/null; then
            read -p "  Open the file? (y/n): " open_choice
            if [ "$open_choice" = "y" ]; then
                xdg-open "$EXCEL_FILE"
            fi
        fi
    fi
else
    echo ""
    echo "❌ Error occurred. Check the output above."
fi