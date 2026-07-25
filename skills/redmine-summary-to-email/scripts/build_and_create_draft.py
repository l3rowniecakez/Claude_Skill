import base64
import json
import os
import sys
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CONFIG_DIR = os.path.expanduser("~/.config/redmine-summary-to-email")
TOKEN_PATH = os.path.join(CONFIG_DIR, "gmail_token.json")


def load_creds():
    if not os.path.exists(TOKEN_PATH):
        raise SystemExit(
            "Missing {}\n"
            "Run authorize_gmail.py once on this machine first.".format(TOKEN_PATH)
        )
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        os.chmod(TOKEN_PATH, 0o600)
    return creds


def build_message(fields):
    # Always build via EmailMessage — hand-written raw UTF-8 header bytes
    # (e.g. a Thai Subject: line written directly) render as mojibake once
    # Gmail parses them, since they skip RFC 2047 encoding. EmailMessage
    # handles that encoding automatically.
    msg = EmailMessage()
    msg["From"] = fields["from"]
    msg["To"] = fields["to"]
    if fields.get("cc"):
        msg["Cc"] = fields["cc"]
    msg["Subject"] = fields["subject"]
    msg.set_content(fields["body"])
    return msg


def main():
    if len(sys.argv) != 3:
        print(
            "usage: build_and_create_draft.py <fields.json> <out.eml>",
            file=sys.stderr,
        )
        sys.exit(1)

    fields_path, eml_out_path = sys.argv[1], sys.argv[2]
    with open(fields_path, "r", encoding="utf-8") as f:
        fields = json.load(f)

    msg = build_message(fields)
    raw_bytes = msg.as_bytes()

    with open(eml_out_path, "wb") as f:
        f.write(raw_bytes)

    encoded = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")
    creds = load_creds()
    service = build("gmail", "v1", credentials=creds)
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": encoded}})
        .execute()
    )
    print("DRAFT_ID={}".format(draft["id"]))
    print("EML_SAVED={}".format(eml_out_path))


if __name__ == "__main__":
    main()
