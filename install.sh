#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/ipc-monitor"
VENV_DIR="$PROJECT_DIR/venv"
PLIST_NAME="com.ipc.monitor"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
FINAL_PLIST="$LAUNCH_AGENTS/$PLIST_NAME.plist"

echo "=== IPC Monitor Installer ==="
echo ""

# 1. Check Python 3.9+
PYTHON=$(command -v python3.11 || command -v python3.10 || command -v python3.9 || command -v python3 || true)
if [ -z "$PYTHON" ]; then
    echo "❌ Python 3.9+ not found. Install via: brew install python@3.11"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "❌ Python $PY_VER found, need 3.9+. Install via: brew install python@3.11"
    exit 1
fi
echo "✅ Python $PY_VER found at $PYTHON"

# 2. Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment…"
    "$PYTHON" -m venv "$VENV_DIR"
fi
echo "✅ Virtual environment: $VENV_DIR"

# 3. Install dependencies
echo "Installing Python packages…"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
echo "✅ Python packages installed"

# 4. Install Playwright Chromium
echo "Installing Playwright Chromium (this may take a minute)…"
"$VENV_DIR/bin/playwright" install chromium
echo "✅ Playwright Chromium installed"

# 5. Generate plists with real paths
mkdir -p "$LAUNCH_AGENTS"
VENV_PYTHON="$VENV_DIR/bin/python"

_install_plist() {
    local name="$1"
    local src="$PROJECT_DIR/$name.plist"
    local dst="$LAUNCH_AGENTS/$name.plist"
    sed \
        -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
        -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
        -e "s|__HOME__|$HOME|g" \
        "$src" > "$dst"
    if launchctl list | grep -q "$name" 2>/dev/null; then
        launchctl unload "$dst" 2>/dev/null || true
    fi
    launchctl load "$dst"
    echo "✅ $name registered"
}

_install_plist "com.ipc.monitor"
_install_plist "com.ipc.bot"

# 7. Done — manual test instructions
echo ""
echo "============================================="
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Open: $PROJECT_DIR/config.py"
echo "  2. Replace BOT_TOKEN and CHAT_ID with your Telegram values"
echo "  3. Run a test:  python $PROJECT_DIR/monitor.py"
echo ""
echo "Scheduled checks: 08:00, 11:00, 14:00, 17:00 (system local time)"
echo "⚠️  Make sure your Mac timezone is set to Europe/Prague"
echo "     (System Settings → General → Date & Time → Time Zone)"
echo "============================================="
