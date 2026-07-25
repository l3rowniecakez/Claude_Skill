#!/bin/bash
set -e
CONFIG_DIR="$HOME/.config/redmine-summary-to-email"
mkdir -p "$CONFIG_DIR"
python3 -m venv "$CONFIG_DIR/venv"
"$CONFIG_DIR/venv/bin/pip" install -q google-auth-oauthlib google-auth-httplib2 google-api-python-client
echo "venv ready at $CONFIG_DIR/venv"
