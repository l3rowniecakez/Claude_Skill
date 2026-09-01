#!/bin/sh
# SSH_ASKPASS helper for non-interactive Gitblit SSH auth. Contains no
# secret itself — reads the password from the GITBLIT_SSH_PASSWORD env var
# that clone_app.py sets on the subprocess, so this file is safe to keep in
# the skill folder (which is mirrored to a public GitHub repo).
printf '%s' "$GITBLIT_SSH_PASSWORD"
