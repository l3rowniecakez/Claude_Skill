#!/usr/bin/env python3
"""Browse the Gitblit web tree of a repo in the "delphi" group and locate
App folders — a folder whose immediate child is literally named "trunk"
(old SVN trunk/branches/tags layout, only trunk survived the migration to
git). The App Name is always the path segment right before "trunk", e.g.
for path "AccountSystem/GLPRO001_P/trunk" the App Name is "GLPRO001_P".

Gitblit already collapses a run of single-child directories into one
display name (e.g. "GroupLifeInsuranceSystem_Benefits/trunk" shown as one
row) — this script follows the href path (URL-decoded), not the display
text, so collapsed and non-collapsed folders are handled the same way.

Usage:
  scan_repo.py list-repos
      Prints JSON list of repo short-names under the "delphi" group, e.g.
      ["apprunjobs", "claim-work-legacy", ...].

  scan_repo.py list <repo> [path]
      Lists the immediate children of <path> (repo root if omitted).
      Prints JSON: {"path": "...", "entries": [{"type": "folder"|"file",
      "name": "...", "path": "..."}]}. A folder's "path" already reflects
      any Gitblit auto-collapse (may contain "/").

  scan_repo.py find <repo> <keyword> [--start PATH] [--max-requests N]
      Breadth-first search for a trunk-terminated App path whose App Name
      contains <keyword> (case-insensitive). Stops immediately on an exact
      (case-insensitive) App Name match. Otherwise explores keyword-matching
      folders first, then falls back to exploring every other folder (since
      an App can sit under an unrelated category folder name) until
      <max-requests> web requests are spent (default 150) — pass --start to
      scope the search under a known category folder and cut this down a
      lot. Prints JSON: {"matches": [{"app_name": "...", "path": "..."}],
      "requests_used": N, "truncated": bool}.
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


def list_repos(session):
    html = gitblit_client.get(session, "repositories/")
    names = re.findall(
        r'href="\.\./summary/delphi%2F([^"]+)\.git" class="list">', html
    )
    # de-dup while preserving order (each repo's name appears twice per row)
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


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


def trunk_match(entry_path):
    """If entry_path has "trunk" as one of its segments, return (app_name,
    canonical_path) where canonical_path is entry_path truncated right after
    "trunk" — Gitblit sometimes over-collapses past trunk into its own sole
    child (e.g. ".../CLPro61V2_P/trunk/Claim_Prog"), so this always drops
    anything past "trunk" rather than trusting the raw path as-is. Returns
    None if entry_path doesn't contain a "trunk" segment, or "trunk" is the
    very first segment (no parent App folder to name it after)."""
    segs = entry_path.split("/")
    if "trunk" not in segs:
        return None
    idx = segs.index("trunk")
    if idx == 0:
        return None
    return segs[idx - 1], "/".join(segs[:idx + 1])


def scan_all(session, repo, start_path="", max_requests=20000, progress_every=20):
    """Exhaustive crawl (no keyword filter) — every trunk-terminated App
    path reachable under start_path. Prints a progress line to stderr every
    `progress_every` requests since a full-repo crawl can take a while."""
    queue = deque([start_path])
    apps = []
    requests_used = 0
    truncated = False

    while queue:
        path = queue.popleft()
        if requests_used >= max_requests:
            truncated = True
            break
        entries = list_folder(session, repo, path)
        requests_used += 1
        if requests_used % progress_every == 0:
            print(
                f"[{repo}] {requests_used} requests, {len(apps)} apps found, "
                f"{len(queue)} folders queued...",
                file=sys.stderr,
            )
        for entry in entries:
            if entry["type"] != "folder":
                continue
            found = trunk_match(entry["path"])
            if found:
                app_name, canonical_path = found
                apps.append({"app_name": app_name, "path": canonical_path})
                continue
            queue.append(entry["path"])

    return {"apps": apps, "requests_used": requests_used, "truncated": truncated}


def find_trunk(session, repo, keyword, start_path="", max_requests=150):
    keyword_lower = keyword.lower()
    queue = deque([start_path])
    matches = []
    requests_used = 0
    truncated = False
    deferred = deque()

    while queue or deferred:
        path = queue.popleft() if queue else deferred.popleft()
        if requests_used >= max_requests:
            truncated = True
            break
        entries = list_folder(session, repo, path)
        requests_used += 1
        for entry in entries:
            if entry["type"] != "folder":
                continue
            found = trunk_match(entry["path"])
            if found:
                app_name, canonical_path = found
                if keyword_lower in app_name.lower():
                    matches.append({"app_name": app_name, "path": canonical_path})
                    if app_name.lower() == keyword_lower:
                        return {
                            "matches": matches,
                            "requests_used": requests_used,
                            "truncated": False,
                        }
                continue
            if keyword_lower in entry["name"].lower():
                queue.append(entry["path"])
            else:
                deferred.append(entry["path"])

    return {
        "matches": matches,
        "requests_used": requests_used,
        "truncated": truncated,
    }


def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list-repos")

    p_list = sub.add_parser("list")
    p_list.add_argument("repo")
    p_list.add_argument("path", nargs="?", default="")

    p_find = sub.add_parser("find")
    p_find.add_argument("repo")
    p_find.add_argument("keyword")
    p_find.add_argument("--start", default="")
    p_find.add_argument("--max-requests", type=int, default=150)

    p_scan_all = sub.add_parser("scan-all")
    p_scan_all.add_argument("repo")
    p_scan_all.add_argument("--start", default="")
    p_scan_all.add_argument("--max-requests", type=int, default=20000)

    args = parser.parse_args()
    if not args.cmd:
        print(json.dumps({"error": "no subcommand given"}), file=sys.stderr)
        sys.exit(1)

    try:
        session = gitblit_client.open_session()
        if args.cmd == "list-repos":
            result = list_repos(session)
        elif args.cmd == "list":
            result = {"path": args.path, "entries": list_folder(session, args.repo, args.path)}
        elif args.cmd == "find":
            result = find_trunk(session, args.repo, args.keyword, args.start, args.max_requests)
        elif args.cmd == "scan-all":
            result = scan_all(session, args.repo, args.start, args.max_requests)
        else:
            raise ValueError(f"unknown subcommand {args.cmd}")
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
