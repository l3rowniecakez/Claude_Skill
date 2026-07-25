import os

from google_auth_oauthlib.flow import InstalledAppFlow

CONFIG_DIR = os.path.expanduser("~/.config/redmine-summary-to-email")
CLIENT_SECRET_PATH = os.path.join(CONFIG_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def main():
    if not os.path.exists(CLIENT_SECRET_PATH):
        raise SystemExit(
            "Missing {}\n"
            "Download the OAuth Desktop client JSON from Google Cloud Console "
            "(Google Auth Platform > Clients) and save it there first.".format(
                CLIENT_SECRET_PATH
            )
        )

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
    creds = flow.run_local_server(port=8765, open_browser=False, prompt="consent")

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN_PATH, 0o600)

    print("SAVED_TOKEN_OK: {}".format(TOKEN_PATH))


if __name__ == "__main__":
    main()
