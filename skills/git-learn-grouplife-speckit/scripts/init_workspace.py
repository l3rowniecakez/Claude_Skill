#!/usr/bin/env python3
"""Local scratch workspace for /git-learn-grouplife-speckit (one folder per App).

  <WORKDIR>/<Group>/<AppName>/
      source/                         READ-ONLY snapshot of the source the REQ files are derived from (see fetch_source.py)
      specs/<NNN>-<TabTitle>/req/     REQ_<SCR-ID>_<unit>.md per screen + README.md  (uploaded to Drive)

<WORKDIR> default = ~/grouplife-speckit  (override: env GROUPLIFE_SPECKIT_WORKDIR). Not a git repo; only a staging area — the
deliverable lives on Drive (speckit_drive.py). Nothing here ever touches the real source repo.

Usage:
  init_workspace.py init    <Group> <AppName>               -> creates the dirs; prints {"workspace": ...}
  init_workspace.py feature <Group> <AppName> <feature_dir> -> creates specs/<feature_dir>/req; prints paths
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")


def workdir():
    return os.environ.get("GROUPLIFE_SPECKIT_WORKDIR") or os.path.join(os.path.expanduser("~"), "grouplife-speckit")


def ws_path(group, app):
    return os.path.join(workdir(), group, app)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "init":
        ws = ws_path(a[1], a[2])
        for d in ("specs", "source"):
            os.makedirs(os.path.join(ws, d), exist_ok=True)
        print(json.dumps({"workspace": ws}, ensure_ascii=False, indent=2))
    elif len(a) == 4 and a[0] == "feature":
        ws = ws_path(a[1], a[2])
        req = os.path.join(ws, "specs", a[3], "req")
        os.makedirs(req, exist_ok=True)
        print(json.dumps({"workspace": ws, "feature_dir": os.path.dirname(req), "req_dir": req}, ensure_ascii=False, indent=2))
    else:
        print(__doc__); sys.exit(1)
