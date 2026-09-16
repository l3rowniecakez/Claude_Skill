#!/usr/bin/env python3
"""Fetch a page (or raw file) from the internal Gitblit web UI using a saved
session (see ~/.config/gitblit-web/credentials.json, created separately,
outside this skill folder since it is mirrored to a public GitHub repo).

Usage:
  gitblit_client.py get <path>
      <path> is relative to the Gitblit base URL, e.g. "repositories/" or
      "tree/delphi%2Fgroupwork-system-2016.git/master/". Prints raw HTML to
      stdout. Prints {"error": ...} to stderr and exits non-zero on failure.
"""
import sys
import os
import re
import json
import urllib.parse

import requests
import urllib3

CRED_PATH = os.path.expanduser("~/.config/gitblit-web/credentials.json")

urllib3.disable_warnings()

FORM_ACTION_RE = re.compile(
    r'<form class="pull-right" id="\w+" method="post" action="([^"]+)"'
)


def load_config():
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(f"{CRED_PATH} not found")
    with open(CRED_PATH) as f:
        return json.load(f)


def open_session():
    """The nav-bar login form is a Wicket stateful callback: the actual POST
    target URL is only valid for the session/page instance that rendered it,
    so this does a GET first (to establish JSESSIONID + read the real form
    action) before POSTing credentials — a direct POST without that GET
    fails silently (200 OK, but not actually logged in)."""
    cfg = load_config()
    session = requests.Session()
    session.verify = False
    landing = cfg["base_url"] + "repositories/"
    resp = session.get(landing, timeout=20)
    resp.raise_for_status()
    match = FORM_ACTION_RE.search(resp.text)
    if not match:
        raise RuntimeError("could not find login form on the repositories page")
    post_url = urllib.parse.urljoin(landing, match.group(1))
    resp = session.post(
        post_url,
        data={
            "wicket:bookmarkablePage": ":com.gitblit.wicket.pages.RepositoriesPage",
            "id1_hf_0": "",
            "username": cfg["username"],
            "password": cfg["password"],
        },
        timeout=20,
    )
    resp.raise_for_status()
    if cfg["username"] not in resp.text:
        raise RuntimeError(f"session did not open as expected — check {CRED_PATH}")
    session.gitblit_base_url = cfg["base_url"]
    return session


def get(session, path):
    resp = session.get(session.gitblit_base_url + path, timeout=20)
    resp.raise_for_status()
    return resp.text


def get_raw(session, path):
    """Like get(), but returns raw bytes and doesn't assume text — used for
    the raw/ file-content endpoint, which may be binary."""
    resp = session.get(session.gitblit_base_url + path, timeout=30)
    resp.raise_for_status()
    return resp.content


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "get":
        print(json.dumps({"error": "usage: gitblit_client.py get <path>"}), file=sys.stderr)
        sys.exit(1)
    path = sys.argv[2]
    try:
        session = open_session()
        html = get(session, path)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(html)


if __name__ == "__main__":
    main()
