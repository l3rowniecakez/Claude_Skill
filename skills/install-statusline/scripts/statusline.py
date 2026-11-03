#!/usr/bin/env python3
import json
import sys
import datetime
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

RESET = "\033[0m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
BAR_GREEN = "\033[38;5;120m"
BAR_YELLOW = "\033[38;5;229m"
BAR_ORANGE = "\033[38;5;216m"
BAR_RED = "\033[38;5;210m"

COTTON_CANDY = "\033[38;2;255;187;218m"
ASTRA = "\033[38;2;252;246;189m"
GRANNY_APPLE = "\033[38;2;208;244;222m"
TROPICAL_BLUE = "\033[38;2;192;228;246m"
MOON_RAKER = "\033[38;2;232;207;248m"

RESET_TIME = "\033[38;5;208m"

MODEL_COLOR = "\033[38;5;111m"

FOLDER_COLOR = "\033[38;5;222m"
REPO_COLOR = "\033[38;5;141m"
BRANCH_COLOR = "\033[38;5;78m"
TICKET_COLOR = "\033[38;5;213m"
DIRTY_COLOR = "\033[38;5;215m"
CLEAN_COLOR = "\033[38;5;120m"
SYNC_COLOR = "\033[38;5;117m"
NOGIT_COLOR = "\033[38;5;245m"
GITHUB_COLOR = "\033[38;5;252m"
EMAIL_COLOR = "\033[38;5;110m"

BAR_WIDTH = 15
BAR_FILLED_CHAR = "●"
BAR_EMPTY_CHAR = "○"


def fmt_time(ts):
    if ts is None:
        return None
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M")
    except (TypeError, ValueError, OSError):
        return None


def fmt_duration(ts):
    if ts is None:
        return None
    try:
        delta = ts - datetime.datetime.now().timestamp()
    except TypeError:
        return None
    if delta <= 0:
        return None
    total_minutes = int(delta // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h:{minutes:02d}m"
    return f"{minutes}m"


def fmt_session_duration(ms):
    if ms is None:
        return None
    total_minutes = int(ms / 1000 // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h:{minutes:02d}m"
    return f"{minutes}m"


def fmt_week_reset_date(ts):
    if ts is None:
        return None
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%a %d %b")
    except (TypeError, ValueError, OSError):
        return None


def fmt_days_hours(ts):
    if ts is None:
        return None
    try:
        delta = ts - datetime.datetime.now().timestamp()
    except TypeError:
        return None
    if delta <= 0:
        return None
    total_minutes = int(delta // 60)
    days, rem_minutes = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(rem_minutes, 60)
    if days:
        return f"{days}d:{hours}h"
    if hours:
        return f"{hours}h:{minutes:02d}m"
    return f"{minutes}m"


def fmt_tokens(n):
    if n is None:
        return None
    if n >= 1000:
        k = n / 1000
        if k == int(k):
            return f"{int(k)}k"
        return f"{k:.1f}k"
    return str(n)


def bar_color(pct):
    if pct < 40:
        return BAR_GREEN
    if pct < 70:
        return BAR_YELLOW
    if pct < 90:
        return BAR_ORANGE
    return BAR_RED


def progress_bar(pct, width=BAR_WIDTH):
    pct = max(0.0, min(100.0, pct))
    filled = round(width * pct / 100)
    color = bar_color(pct)
    bar = BAR_FILLED_CHAR * filled + BAR_EMPTY_CHAR * (width - filled)
    return f"{color}{bar}{RESET}"


IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
MSYS_PATH = re.compile(r"^/([A-Za-z])(?=/|$)")  # Git Bash style /c/Users/... on Windows


def to_native(p):
    """Normalize a path for this OS: Git Bash /c/x -> C:\\x, upper-case drive letter on Windows."""
    if not p:
        return p
    if IS_WIN:
        p = MSYS_PATH.sub(lambda m: m.group(1).upper() + ":", p)
        if len(p) >= 2 and p[1] == ":":
            p = p[0].upper() + p[1:]
        if len(p) == 2 and p[1] == ":":
            p += os.sep
    return os.path.normpath(p)


def norm_key(p):
    """Comparison form: case-insensitive on Windows, unchanged elsewhere."""
    return os.path.normcase(p)


def same_path(a, b):
    return norm_key(a) == norm_key(b)


def is_fs_root(p):
    return os.path.dirname(p) == p


HOME = to_native(os.path.expanduser("~"))
STATE_DIR = os.path.join(HOME, ".claude", "state", "statusline")


def _exclude_prefixes():
    pre = ["/tmp/", "/proc/", "/dev/", "/private/tmp/", "/private/var/folders/",
           os.path.join(HOME, ".claude") + os.sep, os.path.join(HOME, "ψ") + os.sep]
    for var in ("TMPDIR", "TEMP", "TMP"):  # macOS /var/folders/..., Windows %TEMP%
        v = os.environ.get(var)
        if v and os.path.isabs(v) and not is_fs_root(to_native(v)):
            pre.append(to_native(v).rstrip("\\/") + os.sep)
    return tuple(dict.fromkeys(norm_key(p) for p in pre))


EXCLUDE_PREFIXES = _exclude_prefixes()
PROJECT_MARKERS = (
    "package.json", "composer.json", "pom.xml", "pyproject.toml",
    "requirements.txt", "go.mod", "Cargo.toml",
)
PROJECT_MARKER_EXTS = (".dpr", ".dproj", ".sln", ".csproj")
MAX_ROWS = 5
GIT_TTL = 10
CACHE_VERSION = 6
MAX_NAMED_CLONES = 2
if IS_WIN:
    # C:\x, C:/x and Git Bash /c/x
    ABS_PATH = re.compile(r"(?<![\w/])(?:[A-Za-z]:[\\/]|/[A-Za-z]/)[^'\"`;|&<>\n*?]+")
else:
    # Linux/WSL roots + macOS /Users and /Volumes
    ABS_PATH = re.compile(r"/(?:mnt|home|opt|srv|var|workspace|Users|Volumes)/[^'\"`;|&<>\n\\]+")
READONLY_CMDS = {
    "cat", "ls", "grep", "egrep", "rg", "head", "tail", "find", "wc", "echo", "printf", "stat",
    "file", "diff", "cmp", "less", "more", "tree", "du", "df", "pwd", "which", "test", "[",
    "sort", "uniq", "cut", "tr", "awk", "jq", "basename", "dirname", "realpath", "readlink",
    "curl", "sleep", "true", "date", "env", "xxd", "od", "strings", "md5sum", "sha256sum",
}
READONLY_GIT = {
    "status", "log", "diff", "show", "branch", "rev-parse", "rev-list", "remote", "ls-files",
    "ls-remote", "ls-tree", "describe", "blame", "shortlog", "cat-file", "config", "tag",
    "fetch", "grep", "reflog", "whatchanged", "name-rev", "merge-base", "for-each-ref",
}
WRITE_REDIRECT = re.compile(r"(?<![0-9&>])>{1,2}(?!&)\s*(?!/dev/null)")


def run_git(cwd, *args):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=2.5 if IS_WIN else 1.5,
            # no console window flashing for every git call on Windows
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WIN else 0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def short_path(path):
    if same_path(path, HOME):
        return "~"
    if norm_key(path).startswith(norm_key(HOME + os.sep)):
        return "~" + path[len(HOME):]
    return path


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_json(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass


def find_project_root(path):
    """Nearest project folder containing path: VCS root first, then a project marker."""
    d = path if os.path.isdir(path) else os.path.dirname(path)
    marker_hit = None
    cur = d
    # stop at the filesystem root ("/", "C:\\") or HOME; the dirname of a root is itself
    while cur and not is_fs_root(cur) and not same_path(cur, HOME):
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        if os.path.isdir(os.path.join(cur, ".svn")):
            top = cur
            while not is_fs_root(top) and os.path.isdir(os.path.join(os.path.dirname(top), ".svn")):
                top = os.path.dirname(top)
            return top
        if marker_hit is None:
            try:
                names = os.listdir(cur)
            except OSError:
                names = []
            if any(n in PROJECT_MARKERS or n.endswith(PROJECT_MARKER_EXTS) for n in names):
                marker_hit = cur
        cur = os.path.dirname(cur)
    return marker_hit


def excluded(path):
    return norm_key(path).startswith(EXCLUDE_PREFIXES)


def resolve_path(cand):
    """Longest existing prefix of a (possibly space-containing) absolute path candidate."""
    cand = cand.strip().rstrip("/\\.,:" if not IS_WIN else "/\\.,")
    while len(cand) > 1:
        native = to_native(cand)
        if os.path.isabs(native) and not is_fs_root(native) and os.path.exists(native):
            return native
        cut = max(cand.rfind("/"), cand.rfind(" "), cand.rfind("\\") if IS_WIN else -1)
        if cut <= 0:
            return None
        cand = cand[:cut].rstrip()
    return None


def plain_folder_ok(d):
    """A non-project folder deep enough to count as a program folder (e.g. D:\\WORK\\BOT)."""
    if is_fs_root(d) or excluded(d + os.sep):
        return False
    if same_path(d, HOME) or norm_key(HOME + os.sep).startswith(norm_key(d + os.sep)):
        return False  # HOME itself or one of its ancestors
    if IS_WIN:
        drive, rest = os.path.splitdrive(d)
        return bool(drive) and len([p for p in re.split(r"[\\/]", rest) if p]) >= 2
    if d.startswith("/mnt/"):  # WSL /mnt/<drive>/<a>/<b>
        return d.count("/") >= 4
    if IS_MAC:
        if d.startswith("/Volumes/"):  # /Volumes/<disk>/<a>/<b>
            return d.count("/") >= 4
        if d.startswith(HOME + os.sep):  # ~/<a>/<b>
            return d[len(HOME):].count("/") >= 2
    return False


def resolve_root(fp, allow_plain=False):
    """Program folder for a touched path: VCS/project root, else (edits only) a plain work folder."""
    if not fp or excluded(fp):
        return None
    root = find_project_root(fp)
    if root:
        return root
    if allow_plain:
        d = fp if os.path.isdir(fp) else os.path.dirname(fp)
        if plain_folder_ok(d):
            return d
    return None


def child_repos(root):
    """Immediate sub-folders of a plain folder that are git clones (e.g. *_git_version)."""
    try:
        names = os.listdir(root)
    except OSError:
        return []
    return [n for n in names if os.path.exists(os.path.join(root, n, ".git"))]


def segment_is_readonly(seg):
    if WRITE_REDIRECT.search(seg):
        return False
    toks = seg.split()
    while toks and re.match(r"^[A-Za-z_]\w*=", toks[0]):
        toks.pop(0)
    if toks and toks[0] == "sudo":
        toks.pop(0)
    if not toks:
        return True
    if toks[0] == "cd":
        return True
    if toks[0] == "git":
        i = 1
        while i < len(toks) and toks[i].startswith("-"):
            i += 2 if toks[i] in ("-C", "-c") else 1
        return i < len(toks) and toks[i] in READONLY_GIT
    return os.path.basename(toks[0]) in READONLY_CMDS


def is_readonly_cmd(cmd):
    """True when every part of a shell command only reads (cat/grep/git status/...)."""
    return all(segment_is_readonly(seg) for seg in re.split(r"&&|\|\||;|\||\n", cmd))


def tool_events(block):
    """Yield ('path', p) for edited files and ('cmd', text) for mutating shell commands."""
    name = block.get("name")
    inp = block.get("input") or {}
    if name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        fp = inp.get("file_path") or inp.get("notebook_path")
        if isinstance(fp, str):
            yield "path", fp
    elif name == "Bash":
        cmd = inp.get("command") or ""
        if ABS_PATH.search(cmd) and not is_readonly_cmd(cmd):
            yield "cmd", cmd


def scan_transcript(transcript_path, session_id):
    """Incrementally collect {project_root: [first_seq, last_seq]} from edits in the transcript."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return {}
    cache_file = os.path.join(STATE_DIR, f"{session_id or 'unknown'}.json")
    cache = load_json(cache_file) or {}
    if cache.get("v") != CACHE_VERSION:
        cache = {}
    offset = cache.get("offset", 0)
    roots = cache.get("roots", {})
    children = cache.get("children", {})
    seq = cache.get("seq", 0)
    try:
        size = os.path.getsize(transcript_path)
    except OSError:
        return roots
    if size < offset:
        offset, roots, children, seq = 0, {}, {}, 0
    if size == offset:
        return roots

    with open(transcript_path, "rb") as f:
        f.seek(offset)
        chunk = f.read()
    end = chunk.rfind(b"\n")
    if end < 0:
        return roots
    consumed = end + 1

    events = []
    for raw in chunk[:consumed].split(b"\n"):
        if b'"tool_use"' not in raw or not (
            b'"file_path"' in raw or b'"notebook_path"' in raw or b'"Bash"' in raw
        ):
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        msg = obj.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                events.extend(tool_events(block))

    path_cache = {}

    def touch(root, n):
        entry = roots.get(root)
        roots[root] = [entry[0] if entry else n, n]

    def register_children(root):
        if root not in children and not os.path.exists(os.path.join(root, ".git")):
            children[root] = child_repos(root)

    # pass 1: resolve explicit paths into project roots
    numbered = []
    for kind, val in events:
        seq += 1
        numbered.append((seq, kind, val))
        cands = [val] if kind == "path" else ABS_PATH.findall(val)
        found = set()
        for c in cands:
            fp = to_native(c) if kind == "path" else resolve_path(c)
            if not fp or not os.path.isabs(fp):
                continue
            key = (fp, kind == "path")
            if key not in path_cache:
                path_cache[key] = resolve_root(fp, kind == "path") if os.path.exists(fp) else None
            root = path_cache[key]
            if root:
                found.add(root)
            elif kind == "cmd" and os.path.isdir(fp) and plain_folder_ok(fp):
                register_children(fp)  # a plain folder holding clones, e.g. .../JIRA/BOT
        if kind == "cmd" and len(found) > MAX_NAMED_CLONES:
            continue  # a command sweeping many repos is a survey, not work
        for root in found:
            touch(root, seq)
            register_children(root)

    # pass 2: shell commands that name a clone folder (paths hidden behind $vars)
    for n, kind, val in numbered:
        if kind != "cmd":
            continue
        named = [
            (parent, name)
            for parent, names in children.items() for name in names
            if re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", val)
        ]
        if len(named) <= MAX_NAMED_CLONES:  # a loop over many clones is a survey, not work
            for parent, name in named:
                touch(os.path.join(parent, name), n)

    save_json(cache_file, {"v": CACHE_VERSION, "offset": offset + consumed,
                           "roots": roots, "children": children, "seq": seq})
    return roots


def read_git_head(root):
    """Branch name read straight from .git/HEAD (no subprocess)."""
    git = os.path.join(root, ".git")
    try:
        if os.path.isfile(git):
            with open(git, encoding="utf-8") as f:
                line = f.read().strip()
            if line.startswith("gitdir:"):
                git = os.path.normpath(os.path.join(root, line[7:].strip()))
        with open(os.path.join(git, "HEAD"), encoding="utf-8") as f:
            head = f.read().strip()
    except OSError:
        return None
    if head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/"):]
    return f"detached@{head[:7]}"


GITHUB_REMOTE = re.compile(
    r"^(?:(?:https?|ssh|git)://(?:[^@/]+@)?|[^@/\s]+@)(?:ssh\.)?github\.com(?:-[\w.-]+)?(?::\d+)?[:/]+"
    r"([^/\s]+)/([^/\s]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
GITHUB_BRANCH_NUM = re.compile(r"(?:^|/)(?:gh[-_]?)?(\d{1,6})(?=[-_/]|$)(?!-\d)", re.IGNORECASE)


def parse_github(url):
    """'owner/repo' when a remote URL points at github.com (https / ssh / git@ / alias hosts), else None."""
    m = GITHUB_REMOTE.match((url or "").strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def git_remote(root):
    out = run_git(root, "config", "--get", "remote.origin.url")
    return out.strip() if out else None


def git_info(root, now, cache):
    """Branch + status for a git root, cached briefly (git status can be slow on /mnt/d)."""
    hit = cache.get(root)
    if hit and now - hit.get("t", 0) < GIT_TTL:
        return hit
    status = run_git(root, "status", "--porcelain=v2", "--branch", "-uno")
    if status is None:
        fail = {"t": now, "branch": read_git_head(root), "changed": None, "ahead": 0, "behind": 0,
                "remote": hit.get("remote") if hit else None}
        if hit and hit.get("changed") is not None:
            fail.update(changed=hit["changed"], ahead=hit.get("ahead", 0), behind=hit.get("behind", 0))
        return fail
    info = {"t": now, "branch": None, "changed": 0, "ahead": 0, "behind": 0, "remote": git_remote(root)}
    oid = None
    for line in status.splitlines():
        if line.startswith("# branch.head "):
            info["branch"] = line[len("# branch.head "):]
        elif line.startswith("# branch.oid "):
            oid = line[len("# branch.oid "):][:7]
        elif line.startswith("# branch.ab "):
            m = re.match(r"# branch\.ab \+(\d+) -(\d+)", line)
            if m:
                info["ahead"], info["behind"] = int(m.group(1)), int(m.group(2))
        elif line and line[0] in "12u":
            info["changed"] += 1
    if info["branch"] == "(detached)":
        info["branch"] = f"detached@{oid}" if oid else "detached"
    return info


def render_row(root, info):
    folder = os.path.basename(root) or root
    shown = folder if len(folder) <= 34 else folder[:33] + "…"
    parts = [f"{FOLDER_COLOR}📁 {shown}{RESET}"]
    if os.path.exists(os.path.join(root, ".git")):
        gh = parse_github(info.get("remote"))
        if gh:
            parts.append(f"{GITHUB_COLOR}🐙 GitHub:{gh}{RESET}")
        branch = info.get("branch")
        if branch:
            parts.append(f"{BRANCH_COLOR}🌿 Branch:{branch}{RESET}")
            m = re.search(r"(?:ticket|rm|issue)[/_-]?(\d+)", branch, re.IGNORECASE)
            if not m and gh:  # GitHub style: 123-fix-bug, feature/123-x, gh-45
                m = GITHUB_BRANCH_NUM.search(branch)
            if m:
                label = "Issue" if gh else "Ticket"
                parts.append(f"{TICKET_COLOR}🎫 {label}:#{m.group(1)}{RESET}")
        changed = info.get("changed")
        if changed:
            parts.append(f"{DIRTY_COLOR}✏️ Changes:{changed}{RESET}")
        elif changed == 0:
            parts.append(f"{CLEAN_COLOR}✅ Clean{RESET}")
        ahead, behind = info.get("ahead", 0), info.get("behind", 0)
        if ahead or behind:
            sync = (f"⬆️{ahead}" if ahead else "") + (f"⬇️{behind}" if behind else "")
            parts.append(f"{SYNC_COLOR}{sync}{RESET}")
    return " | ".join(parts)


def location_rows(data):
    """One row per program the session is working on, most recently edited first."""
    ws = data.get("workspace", {}) or {}
    cwd = ws.get("current_dir") or data.get("cwd") or os.getcwd()
    now = datetime.datetime.now().timestamp()

    roots = scan_transcript(data.get("transcript_path"), data.get("session_id"))
    is_git = lambda r: os.path.exists(os.path.join(r, ".git"))
    activity = {r: e[1] for r, e in roots.items() if is_git(r)}

    for d in [cwd] + list(ws.get("added_dirs") or []):
        d = to_native(d) if isinstance(d, str) and d else None
        root = find_project_root(d) if d and os.path.isdir(d) else None
        if root and is_git(root) and not excluded(root + os.sep):
            activity.setdefault(root, 0)

    hidden = set((load_json(os.path.join(STATE_DIR, f"hidden-{data.get('session_id') or 'unknown'}.json")) or {}).get("roots", []))
    ordered = sorted((r for r in activity if r not in hidden), key=lambda r: activity[r], reverse=True)
    save_json(os.path.join(STATE_DIR, f"shown-{data.get('session_id') or 'unknown'}.json"), {"roots": ordered})
    if not ordered:
        return []

    shown = ordered[:MAX_ROWS]
    git_roots = [r for r in shown if os.path.exists(os.path.join(r, ".git"))]
    cache_file = os.path.join(STATE_DIR, "gitinfo.json")
    cache = load_json(cache_file) or {}
    with ThreadPoolExecutor(max_workers=MAX_ROWS) as pool:
        infos = dict(zip(git_roots, pool.map(lambda r: git_info(r, now, cache), git_roots)))
    if infos:
        cache.update({r: i for r, i in infos.items() if i.get("t") == now})
        save_json(cache_file, cache)
    rows = [render_row(r, infos.get(r)) for r in shown]
    if len(ordered) > MAX_ROWS:
        rows.append(f"{NOGIT_COLOR}… และอีก {len(ordered) - MAX_ROWS} โปรแกรม{RESET}")
    return rows


def login_email():
    """Email of the logged-in Claude account (oauthAccount in ~/.claude.json), or None."""
    cfg_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    candidates = []
    if cfg_dir:
        candidates.append(os.path.join(cfg_dir, ".claude.json"))
    candidates += [os.path.join(HOME, ".claude.json"), os.path.join(HOME, ".claude", ".claude.json")]
    for p in candidates:
        acct = (load_json(p) or {}).get("oauthAccount")
        if isinstance(acct, dict) and acct.get("emailAddress"):
            return acct["emailAddress"]
    return None


def main():
    # Windows pipes default to the ANSI code page (cp874/cp1252), which cannot encode emoji
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        data = json.loads(sys.stdin.buffer.read())  # bytes: json detects UTF-8 itself
    except Exception:
        print("")
        return

    parts = []

    model = data.get("model", {}).get("display_name")
    if model:
        parts.append(f"{MODEL_COLOR}🤖 {model}{RESET}")

    effort = data.get("effort", {}).get("level")
    if effort:
        parts.append(f"\033[38;5;99m🧠 Effort:{effort}{RESET}")

    cost = data.get("cost", {}).get("total_cost_usd")
    if cost is not None:
        cost_sep = " " if cost < 10 else ""
        parts.append(f"\033[38;5;44m💰 Cost:{cost_sep}${cost:.2f}{RESET}")

    ctx_data = data.get("context_window", {}) or {}
    ctx = ctx_data.get("used_percentage")
    if ctx is not None:
        ctx_str = f"{ctx:.0f}%"
        input_tok = fmt_tokens(ctx_data.get("total_input_tokens"))
        window_size = fmt_tokens(ctx_data.get("context_window_size"))
        if input_tok and window_size:
            ctx_str += f" ({input_tok}/{window_size})"
        parts.append(f"\033[38;5;69m📄 Context:{ctx_str}{RESET}")

    duration_ms = data.get("cost", {}).get("total_duration_ms")
    session_time = fmt_session_duration(duration_ms)
    if session_time is not None:
        parts.append(f"\033[38;5;85m⏱️ Session:{session_time}{RESET}")

    rate = data.get("rate_limits", {}) or {}
    current_chunk = None
    weekly_chunk = None

    five = rate.get("five_hour", {}) or {}
    five_pct = five.get("used_percentage")
    if five_pct is not None:
        chunk = f"⚡ Current Limit : {progress_bar(five_pct)} {bar_color(five_pct)}{five_pct:>2.0f}%{RESET}"
        five_resets_at = five.get("resets_at")
        reset = fmt_time(five_resets_at)
        resets_in = fmt_duration(five_resets_at)
        if reset:
            chunk += f" | {RESET_TIME}⏳ Reset {reset}"
            if resets_in:
                chunk += f", in {resets_in}"
            chunk += RESET
        current_chunk = chunk

    week = rate.get("seven_day", {}) or {}
    week_pct = week.get("used_percentage")
    if week_pct is not None:
        week_reset_ts = week.get("resets_at")
        chunk = f"📆 Weekly  Limit : {progress_bar(week_pct)} {bar_color(week_pct)}{week_pct:>2.0f}%{RESET}"
        week_reset_display = fmt_week_reset_date(week_reset_ts)
        week_reset_time = fmt_time(week_reset_ts)
        week_resets_in = fmt_days_hours(week_reset_ts)
        if week_reset_display:
            chunk += f" | {RESET_TIME}⏳ Reset {week_reset_display}"
            if week_reset_time:
                chunk += f" {week_reset_time}"
            if week_resets_in:
                chunk += f", in {week_resets_in}"
            chunk += RESET
        weekly_chunk = chunk

    lines = [" | ".join(parts)]
    email = login_email()
    if email:
        lines.append(f"🔐 Login : {EMAIL_COLOR}{email}{RESET}")
    lines.extend(location_rows(data))
    if current_chunk:
        lines.append(current_chunk)
    if weekly_chunk:
        lines.append(weekly_chunk)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
