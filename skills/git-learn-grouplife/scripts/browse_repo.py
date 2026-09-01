#!/usr/bin/env python3
"""Browse and read files from a delphi-group Gitblit repo over the web UI,
WITHOUT ever running `git clone` — this is the whole point of this skill's
sibling relationship to /git-clone-grouplife (same tracking sheet, same
repo/sub_folder values, but this script reads content remotely instead of
materializing it on disk).

Usage:
  browse_repo.py list <repo> <path>
      Lists the immediate children of <path> in <repo> (master branch).
      Prints JSON: {"path": "...", "entries": [{"type": "folder"|"file",
      "name": "...", "path": "..."}]}. A folder's "path" already reflects
      any Gitblit auto-collapse (may contain "/") — same behavior as
      /git-clone-grouplife-update's scan_repo.py.

  browse_repo.py tree <repo> <path> [--max-requests N]
      Recursively lists every file under <path> (default max-requests 500,
      each folder visited = 1 request). Prints JSON: {"files": [...],
      "folders_scanned": N, "requests_used": N, "truncated": bool}. If
      truncated is true, the crawl hit the request cap before finishing —
      narrow <path> further or raise --max-requests, don't assume the file
      list is complete.

  browse_repo.py read <repo> <path> [--max-bytes N]
      Fetches ONE file's raw content and prints JSON: {"path": "...",
      "size": N, "encoding": "...", "content": "..."} on success. Refuses
      (with {"error": ...}) if the file looks binary (a NUL byte in the
      first 8KB) or exceeds --max-bytes (default 2,000,000) — this skill is
      for reading source text, not dumping compiled/binary artifacts
      (.res, .dcu, .suo, images, etc.) through JSON.
"""
import sys
import os
import re
import json
import argparse
import urllib.parse
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitblit_client  # noqa: E402

GROUP = "delphi"

ROW_RE = re.compile(
    r'<td class="hidden-phone icon"><img src="(?:\.\./)+(folder|file)_16x16\.png"/></td>\s*'
    r'<td><span>\s*<a href="([^"]+)" class="list">'
)


def encoded_repo(repo):
    return urllib.parse.quote(f"{GROUP}/{repo}.git", safe="")


def list_folder(session, repo, path):
    enc_repo = encoded_repo(repo)
    if path:
        url = f"tree/{enc_repo}/master/{urllib.parse.quote(path, safe='')}"
    else:
        url = f"tree/{enc_repo}"
    html = gitblit_client.get(session, url)
    entries = []
    for kind, href in ROW_RE.findall(html):
        marker = "/tree/" if kind == "folder" else "/blob/"
        idx = href.find(marker)
        if idx == -1:
            continue
        rest = href[idx + len(marker):]
        # rest looks like "<enc_repo>/master/<enc_path>" (root listing omits
        # "/master/<path>" entirely when rest has no further slash)
        parts = rest.split("/", 2)
        enc_path = parts[2] if len(parts) == 3 else ""
        entry_path = urllib.parse.unquote(enc_path)
        name = entry_path.rsplit("/", 1)[-1] if entry_path else ""
        entries.append({
            "type": "folder" if kind == "folder" else "file",
            "name": name,
            "path": entry_path,
        })
    return entries


def tree(session, repo, start_path, max_requests=500):
    queue = deque([start_path])
    files = []
    folders_scanned = 0
    requests_used = 0
    truncated = False

    while queue:
        if requests_used >= max_requests:
            truncated = True
            break
        path = queue.popleft()
        entries = list_folder(session, repo, path)
        requests_used += 1
        folders_scanned += 1
        for entry in entries:
            if entry["type"] == "folder":
                queue.append(entry["path"])
            else:
                files.append(entry["path"])

    return {
        "files": files,
        "folders_scanned": folders_scanned,
        "requests_used": requests_used,
        "truncated": truncated,
    }


def decode_content(raw):
    """Returns (text, encoding_used) or (None, None) if raw looks binary."""
    if b"\x00" in raw[:8000]:
        return None, None
    for enc in ("utf-8", "cp874"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace"), "latin-1 (replaced undecodable bytes)"


def read_file(session, repo, path, max_bytes=2_000_000):
    enc_repo = encoded_repo(repo)
    enc_path = urllib.parse.quote(path, safe="")
    url = f"raw/{enc_repo}/master/{enc_path}"
    raw = gitblit_client.get_raw(session, url)

    if len(raw) > max_bytes:
        return {
            "error": f"file too large to display ({len(raw)} bytes, limit {max_bytes})",
            "path": path,
            "size": len(raw),
        }

    text, encoding = decode_content(raw)
    if text is None:
        return {
            "error": "binary file (contains a NUL byte) — not displayed as text",
            "path": path,
            "size": len(raw),
        }

    return {"path": path, "size": len(raw), "encoding": encoding, "content": text}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list")
    p_list.add_argument("repo")
    p_list.add_argument("path", nargs="?", default="")

    p_tree = sub.add_parser("tree")
    p_tree.add_argument("repo")
    p_tree.add_argument("path", nargs="?", default="")
    p_tree.add_argument("--max-requests", type=int, default=500)

    p_read = sub.add_parser("read")
    p_read.add_argument("repo")
    p_read.add_argument("path")
    p_read.add_argument("--max-bytes", type=int, default=2_000_000)

    args = parser.parse_args()
    if not args.cmd:
        print(json.dumps({"error": "no subcommand given"}), file=sys.stderr)
        sys.exit(1)

    try:
        session = gitblit_client.open_session()
        if args.cmd == "list":
            result = {"path": args.path, "entries": list_folder(session, args.repo, args.path)}
        elif args.cmd == "tree":
            result = tree(session, args.repo, args.path, args.max_requests)
        elif args.cmd == "read":
            result = read_file(session, args.repo, args.path, args.max_bytes)
        else:
            raise ValueError(f"unknown subcommand {args.cmd}")
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
