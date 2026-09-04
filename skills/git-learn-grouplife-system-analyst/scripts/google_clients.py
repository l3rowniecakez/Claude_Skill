#!/usr/bin/env python3
"""Shared Sheets + Drive service builders for
/git-learn-grouplife-system-analyst, reusing the same OAuth token as the
other claude-google-access scripts (see reference_claude_google_access_oauth
memory) — reused directly here (instead of importing
~/.config/claude-google-access/read_sheet.py's get_service) because this
skill also needs Drive folder/file creation and move, which read_sheet.py
does not expose (it only builds a Sheets service)."""
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = os.path.expanduser("~/.config/claude-google-access/token.json")


def _creds():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def sheets_service():
    return build("sheets", "v4", credentials=_creds())


def drive_service():
    return build("drive", "v3", credentials=_creds())
