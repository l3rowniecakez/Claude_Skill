#!/usr/bin/env python3
"""Sparse-clone exactly ONE App's trunk folder from a delphi-group Gitblit
repo — never the whole repo's working tree. Uses `git sparse-checkout` in
cone mode so only the requested path is materialized on disk (the .git
object database still receives the whole repo's history — this Gitblit/JGit
server doesn't honor `--filter=blob:none` for a real bandwidth reduction,
confirmed in [[reference_groupwork_system_2016_repo]] — but the WORKING
TREE, which is what "don't sync the whole repo" is actually about, is
correctly limited to just this one App).

The working tree stays NESTED at <dest_dir>/<Sub Folder> (e.g.
<dest_dir>/Cashier_Program/CHPro002_P/trunk/...), not flattened to
<dest_dir> root — a flattened layout was tried and reverted 2026-08-26 (see
[[reference_gitclone_grouplife_skill]]): git can't track a file at a disk
path that doesn't match its repo-relative path, so flattening required
deleting `.git`, which meant the user could no longer `git add`/commit/push
changes from that folder. The user chose keeping `.git` (and the nested
path) over a flat layout once they realized push wouldn't work otherwise —
`.git` is what makes push/pull possible, never delete it.

Auth: SSH password login (no usable pubkey — see
[[reference_claimautomation_repo]]), credential read from
~/.config/gitblit-web/credentials.json (shared with the sibling
gitclone-grouplife-update skill's web session — same Gitblit account).
Non-interactive password entry via SSH_ASKPASS (gitblit_askpass.sh next to
this script) + SSH_ASKPASS_REQUIRE=force (needs OpenSSH >= 8.4).

Usage:
  clone_app.py <repo_clone_command_or_url> <sub_folder> <dest_dir>
      <repo_clone_command_or_url> is the sheet's "repo" column value, either
      the full "git clone ssh://<gitblit_user>@host:port/..." string or just
      the bare ssh:// URL — the "<gitblit_user>" placeholder (or any
      username already in the URL) is replaced with the real username from
      the credentials file. <sub_folder> is the sheet's "Sub Folder" value
      (must end in "trunk"). <dest_dir> must not already exist (this script
      refuses to clone into an existing/non-empty directory — remove or
      choose another path first, this script will never delete anything
      that existed before it ran).

      Prints JSON {"dest_dir": "...", "branch": "...", "checked_out_path":
      "..."} on success — <checked_out_path> is where the App's files
      actually are (<dest_dir>/<sub_folder>), and <dest_dir> stays a normal
      working git repo (`.git` at its root) that `git add`/commit/push work
      from normally — or {"error": "..."} on failure (and best-effort
      removes the partially-created dest_dir on failure, since a failed
      clone attempt's own half-written output isn't something the user
      asked to keep).
"""
import sys
import os
import re
import json
import shutil
import subprocess

CRED_PATH = os.path.expanduser("~/.config/gitblit-web/credentials.json")
ASKPASS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gitblit_askpass.sh")


def load_credentials():
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(f"{CRED_PATH} not found — ask the user for their Gitblit SSH username/password")
    with open(CRED_PATH) as f:
        return json.load(f)


def resolve_url(repo_field, username):
    url = repo_field.strip()
    prefix = "git clone "
    if url.startswith(prefix):
        url = url[len(prefix):]
    # swap out whatever username is currently in the ssh:// URL (the
    # "<gitblit_user>" placeholder, or a real one) for the real username
    url = re.sub(r'ssh://[^@]+@', f'ssh://{username}@', url)
    return url


def run(cmd, cwd, env):
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nstdout: {proc.stdout}\nstderr: {proc.stderr}")
    return proc.stdout


def clone_app(repo_field, sub_folder, dest_dir):
    if os.path.exists(dest_dir) and os.listdir(dest_dir):
        raise RuntimeError(f"{dest_dir} already exists and is not empty — refusing to clone into it")

    creds = load_credentials()
    url = resolve_url(repo_field, creds["username"])

    env = os.environ.copy()
    env["GITBLIT_SSH_PASSWORD"] = creds["password"]
    env["SSH_ASKPASS"] = ASKPASS_PATH
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["GIT_SSH_COMMAND"] = (
        "ssh -o PubkeyAuthentication=no -o PreferredAuthentications=keyboard-interactive,password "
        "-o StrictHostKeyChecking=accept-new"
    )
    env["GIT_TERMINAL_PROMPT"] = "0"

    os.makedirs(dest_dir, exist_ok=True)
    try:
        run(["git", "clone", "--no-checkout", "--filter=blob:none", url, "."], dest_dir, env)
        run(["git", "sparse-checkout", "init", "--cone"], dest_dir, env)
        run(["git", "sparse-checkout", "set", sub_folder], dest_dir, env)

        branch = "master"
        try:
            out = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], dest_dir, env)
            branch = out.strip().rsplit("/", 1)[-1]
        except Exception:
            pass

        run(["git", "checkout", branch], dest_dir, env)

        checked_out_path = os.path.join(dest_dir, sub_folder)
        if not os.path.isdir(checked_out_path):
            raise RuntimeError(
                f"clone completed but {checked_out_path} doesn't exist — sub_folder path may be wrong"
            )

        return {"dest_dir": dest_dir, "branch": branch, "checked_out_path": checked_out_path}
    except Exception:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"error": "usage: clone_app.py <repo_field> <sub_folder> <dest_dir>"}), file=sys.stderr)
        sys.exit(1)
    repo_field, sub_folder, dest_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        result = clone_app(repo_field, sub_folder, dest_dir)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
