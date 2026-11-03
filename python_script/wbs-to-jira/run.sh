#!/usr/bin/env bash
# =============================================================================
# run.sh — JIRA WBS Creator (all-in-one)
# =============================================================================
# Automatically checks/installs dependencies, validates config, and runs.
#
# Usage:
#   bash run.sh --wbs <path-to-wbs.md>
#   bash run.sh --wbs <path-to-wbs.md> --dry-run
#   bash run.sh --help
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYTHON_SCRIPT="create_jira_from_wbs.py"
CONFIG_FILE="config.ini"
PYTHON_MIN_VERSION="3.9"
REQUIRED_PACKAGES=("requests")

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*"; }

# ── Help ──────────────────────────────────────────────────────────────────────
show_help() {
    echo ""
    echo -e "${BOLD}JIRA WBS Creator — run.sh${RESET}"
    echo ""
    echo "  Usage:"
    echo "    bash run.sh --wbs <path-to-wbs.md> [--dry-run]"
    echo ""
    echo "  Options:"
    echo "    --wbs <file>   Path to the WBS markdown file (required)"
    echo "    --dry-run      Print what would be created without calling JIRA API"
    echo "    --help         Show this help message"
    echo ""
    echo "  Examples:"
    echo "    bash run.sh --wbs wbs-cr5-vpoint-card-linkage.md"
    echo "    bash run.sh --wbs wbs-cr5-vpoint-card-linkage.md --dry-run"
    echo ""
    echo "  Configuration:"
    echo "    Edit config.ini with your JIRA base URL, email, API token, and project key."
    echo ""
}

# ── Parse arguments ───────────────────────────────────────────────────────────
WBS_FILE=""
DRY_RUN_FLAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --wbs)
            WBS_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN_FLAG="--dry-run"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

echo ""
echo -e "${BOLD}=================================================${RESET}"
echo -e "${BOLD}  JIRA WBS Creator                              ${RESET}"
echo -e "${BOLD}=================================================${RESET}"
echo ""

# ── Step 1: Validate --wbs argument (fallback to config.ini) ─────────────────
if [ -z "$WBS_FILE" ] && [ -f "$CONFIG_FILE" ]; then
    WBS_FILE=$(grep -E "^\s*wbs_file\s*=" "$CONFIG_FILE" | tail -1 | cut -d'=' -f2- | tr -d ' \r\n' || true)
    if [ -n "$WBS_FILE" ]; then
        log_info "Using wbs_file from config.ini: $WBS_FILE"
    fi
fi

if [ -z "$WBS_FILE" ]; then
    log_error "--wbs argument is required."
    show_help
    exit 1
fi

if [ ! -f "$WBS_FILE" ]; then
    log_error "WBS file not found: $WBS_FILE"
    exit 1
fi

log_success "WBS file: $WBS_FILE"
[ -n "$DRY_RUN_FLAG" ] && log_warn "DRY-RUN mode — no JIRA tickets will be created."

# ── Step 2: Check Python is available ─────────────────────────────────────────
log_info "Checking Python..."

PYTHON_BIN=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VERSION=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$(echo "$VERSION" | cut -d. -f1)
        MINOR=$(echo "$VERSION" | cut -d. -f2)
        MIN_MAJOR=$(echo "$PYTHON_MIN_VERSION" | cut -d. -f1)
        MIN_MINOR=$(echo "$PYTHON_MIN_VERSION" | cut -d. -f2)
        if [ "$MAJOR" -gt "$MIN_MAJOR" ] || { [ "$MAJOR" -eq "$MIN_MAJOR" ] && [ "$MINOR" -ge "$MIN_MINOR" ]; }; then
            PYTHON_BIN="$cmd"
            log_success "Python $VERSION found."
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    log_error "Python $PYTHON_MIN_VERSION+ is required but not found."
    exit 1
fi

# ── Step 3: Create venv & install packages if needed ──────────────────────────
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    log_info "Creating virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
fi

# Check if required packages are installed; install missing ones
MISSING_PKGS=()
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! "$VENV_PYTHON" -c "import $pkg" 2>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    log_info "Installing missing packages: ${MISSING_PKGS[*]}"
    "$VENV_PIP" install --quiet "${MISSING_PKGS[@]}"
    log_success "Packages installed."
else
    log_success "All required packages are available."
fi

# ── Step 4: Check Python script exists ────────────────────────────────────────
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log_error "$PYTHON_SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

# ── Step 5: Validate config.ini ───────────────────────────────────────────────
echo ""
log_info "Validating configuration..."

if [ ! -f "$CONFIG_FILE" ]; then
    log_error "config.ini not found. Create it with your JIRA settings (see README.md)."
    exit 1
fi

parse_ini_value() {
    local file="$1" key="$2"
    grep -E "^\s*${key}\s*=" "$file" | tail -1 | sed 's/^[^=]*=\s*//' | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

CONFIG_KEYS=("server" "email" "api_token" "project")
CONFIG_LABELS=("JIRA Server URL" "JIRA Email" "JIRA API Token" "JIRA Project Key")
MISSING_KEYS=()

for i in "${!CONFIG_KEYS[@]}"; do
    value=$(parse_ini_value "$CONFIG_FILE" "${CONFIG_KEYS[$i]}")
    if [ -z "$value" ] || [[ "$value" == *"your-domain"* ]] || [[ "$value" == *"your-email"* ]]; then
        MISSING_KEYS+=("${CONFIG_LABELS[$i]} (${CONFIG_KEYS[$i]})")
    fi
done

if [ ${#MISSING_KEYS[@]} -gt 0 ] && [ -z "$DRY_RUN_FLAG" ]; then
    log_error "The following config.ini values are missing or still have placeholders:"
    for key in "${MISSING_KEYS[@]}"; do
        echo -e "         ${RED}✗${RESET} $key"
    done
    echo ""
    log_error "Edit config.ini with your actual JIRA credentials, then re-run."
    exit 1
fi

if [ -n "$DRY_RUN_FLAG" ] && [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    log_warn "Config has placeholder values — OK for dry-run."
else
    log_success "Configuration looks good."
fi

# ── Step 6: Launch ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}─────────────────────────────────────────────────${RESET}"
log_info "Launching JIRA ticket creation..."
echo -e "${BOLD}─────────────────────────────────────────────────${RESET}"
echo ""

"$VENV_PYTHON" "$PYTHON_SCRIPT" --wbs "$WBS_FILE" $DRY_RUN_FLAG
EXIT_CODE=$?

echo ""
echo -e "${BOLD}─────────────────────────────────────────────────${RESET}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  Done! All tickets processed successfully.${RESET}"
else
    echo -e "${RED}${BOLD}  Script exited with code $EXIT_CODE. Check output above.${RESET}"
fi
echo -e "${BOLD}─────────────────────────────────────────────────${RESET}"
echo ""

exit $EXIT_CODE
