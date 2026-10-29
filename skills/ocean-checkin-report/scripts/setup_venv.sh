#!/usr/bin/env bash
# Create the Python venv used by /ocean-checkin-report (outside the skill folder, never synced).
set -euo pipefail
CFG="${OCEAN_CHAT_CONFIG_DIR:-$HOME/.config/ocean-google-chat}"
mkdir -p "$CFG" && chmod 700 "$CFG"
PY=$(command -v python3 || command -v python)
if [ ! -x "$CFG/.venv/bin/python3" ] && [ ! -x "$CFG/.venv/Scripts/python.exe" ]; then
  "$PY" -m venv "$CFG/.venv"
fi
VPY="$CFG/.venv/bin/python3"; [ -x "$VPY" ] || VPY="$CFG/.venv/Scripts/python.exe"
"$VPY" -m pip install -q --upgrade google-api-python-client google-auth google-auth-oauthlib
echo "VENV_PY=$VPY"
