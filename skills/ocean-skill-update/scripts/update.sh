#!/usr/bin/env bash
# ocean-skill-update: pull skills/ from the public Claude_Skill GitHub repo and
# sync it into known Claude skill install locations on this machine.
#
# Usage:
#   update.sh                    -> install/update ALL skills from the repo
#   update.sh --only a,b,c       -> install/update ONLY the named skills
#   update.sh --list             -> just clone + print "name|description" per
#                                    skill in the repo, one per line, and exit
#                                    (does not touch any install location)
set -o pipefail

REPO_URL="https://github.com/l3rowniecakez/Claude_Skill.git"
CACHE_DIR="$HOME/.cache/ocean-skill-update/Claude_Skill"

MODE="all"
ONLY_FILTER=""
if [ "${1:-}" = "--list" ]; then
  MODE="list"
elif [ "${1:-}" = "--only" ]; then
  MODE="only"
  ONLY_FILTER=",${2:-},"
fi

TOTAL_STEPS=4
STEP=0

bar() {
  pct=$1; label=$2
  filled=$(( pct / 5 ))
  empty=$(( 20 - filled ))
  fill=""; i=0; while [ "$i" -lt "$filled" ]; do fill="${fill}#"; i=$((i+1)); done
  emp=""; i=0; while [ "$i" -lt "$empty" ]; do emp="${emp}."; i=$((i+1)); done
  printf "[%s%s] %3d%% %s\n" "$fill" "$emp" "$pct" "$label" 1>&2
}

step() {
  STEP=$((STEP+1))
  pct=$(( STEP * 100 / TOTAL_STEPS ))
  bar "$pct" "$1"
}

is_selected() {
  name="$1"
  [ "$MODE" != "only" ] && return 0
  case "$ONLY_FILTER" in
    *",$name,"*) return 0 ;;
    *) return 1 ;;
  esac
}

step "เตรียมพื้นที่ทำงาน..."
rm -rf "$CACHE_DIR"
mkdir -p "$(dirname "$CACHE_DIR")"

step "กำลังดึง skill ล่าสุดจาก GitHub..."
if ! git clone --depth 1 --quiet "$REPO_URL" "$CACHE_DIR" 2>/tmp/ocean-skill-update.err; then
  echo "ERROR: git clone ล้มเหลว"
  cat /tmp/ocean-skill-update.err
  exit 1
fi
if [ ! -d "$CACHE_DIR/skills" ]; then
  echo "ERROR: ไม่พบโฟลเดอร์ skills/ ใน repo ที่ clone มา"
  exit 1
fi
COMMIT=$(git -C "$CACHE_DIR" rev-parse --short HEAD)
COMMIT_DATE=$(git -C "$CACHE_DIR" log -1 --format=%cd --date=format:'%Y-%m-%d %H:%M')

if [ "$MODE" = "list" ]; then
  for src in "$CACHE_DIR"/skills/*/; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    smd="${src}SKILL.md"
    desc=""
    if [ -f "$smd" ]; then
      desc=$(awk '/^---$/{c++; next} c==1 && /^description:/{sub(/^description:[ \t]*/,""); print; exit}' "$smd")
      desc=${desc%\"}; desc=${desc#\"}
      desc=${desc%\'}; desc=${desc#\'}
    fi
    if [ ${#desc} -gt 110 ]; then
      desc="${desc:0:107}..."
    fi
    echo "${name}|${desc}"
  done
  exit 0
fi

# --- known Claude skill install locations only ---------------------------
# Deliberately NOT doing a broad filesystem-wide `find -iname skills` sweep
# here: many unrelated tools (VS Code extensions, bun/npm package caches,
# other CLI agents' plugin caches, ...) happen to also ship a `skills/*/
# SKILL.md`-shaped folder, and a generic sweep will silently overwrite their
# files too. Only touch paths that are specifically Claude Code CLI /
# Claude Desktop install locations.
step "กำลังค้นหาตำแหน่งติดตั้ง skill ในเครื่องนี้..."

TARGET_PATHS=()
TARGET_LABELS=()

add_target() {
  path="$1"; label="$2"
  for existing in "${TARGET_PATHS[@]}"; do
    [ "$existing" = "$path" ] && return
  done
  TARGET_PATHS+=("$path")
  TARGET_LABELS+=("$label")
}

# Claude Code CLI on this machine (Linux/WSL/macOS home) — always the primary target
add_target "$HOME/.claude/skills" "Claude Code CLI"

IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then
  IS_WSL=1
fi

# When running inside WSL, also look for Claude Desktop / Claude Code CLI installed
# natively on the Windows side (different users may have either or both).
if [ "$IS_WSL" -eq 1 ] && [ -d /mnt/c/Users ]; then
  for userdir in /mnt/c/Users/*/; do
    win_user=$(basename "$userdir")
    case "$win_user" in
      Public|Default|"Default User"|"All Users") continue ;;
    esac
    if [ -d "${userdir}AppData/Roaming/Claude" ]; then
      add_target "${userdir}AppData/Roaming/Claude/skills" "Claude Desktop (Windows user: $win_user)"
    fi
    if [ -d "${userdir}.claude" ]; then
      add_target "${userdir}.claude/skills" "Claude Code CLI (Windows user: $win_user)"
    fi
  done
fi

# Native macOS / Linux Claude Desktop install locations
if [ -d "$HOME/Library/Application Support/Claude" ]; then
  add_target "$HOME/Library/Application Support/Claude/skills" "Claude Desktop (macOS)"
fi
if [ -d "$HOME/.config/Claude" ]; then
  add_target "$HOME/.config/Claude/skills" "Claude Desktop (Linux)"
fi

# Native Windows (not WSL): if this bash session's own $HOME already IS the
# Windows user profile (e.g. Git Bash / MSYS2), $HOME/AppData/Roaming/Claude
# resolves directly — no /mnt/c involved. On real Linux/macOS this path never
# exists, so the check is a no-op there.
if [ -d "$HOME/AppData/Roaming/Claude" ]; then
  add_target "$HOME/AppData/Roaming/Claude/skills" "Claude Desktop (Windows, native)"
fi

TARGET_COUNT=${#TARGET_PATHS[@]}

NEW_LIST=()
UPDATED_LIST=()
SKIPPED_LIST=()
idx=0
for target in "${TARGET_PATHS[@]}"; do
  sub_pct=$(( 75 + (idx + 1) * 20 / TARGET_COUNT ))
  bar "$sub_pct" "กำลังก็อปปี้ไปยัง: $target"
  mkdir -p "$target"
  for src in "$CACHE_DIR"/skills/*/; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    if ! is_selected "$name"; then
      continue
    fi
    dest="$target/$name"
    if [ -d "$dest" ]; then
      UPDATED_LIST+=("$name -> $target")
    else
      NEW_LIST+=("$name -> $target")
    fi
    rm -rf "$dest"
    cp -r "$src" "$dest"
  done
  idx=$((idx+1))
done

step "เสร็จสิ้น"

echo ""
echo "=== สรุปผล /ocean-skill-update ==="
echo "Repo: $REPO_URL"
echo "Commit: $COMMIT ($COMMIT_DATE)"
if [ "$MODE" = "only" ]; then
  echo "โหมด: เลือกเฉพาะ skill ที่ระบุ ($ONLY_FILTER)"
fi
echo ""
echo "ตำแหน่งที่อัพเดท ($TARGET_COUNT):"
idx=0
for target in "${TARGET_PATHS[@]}"; do
  echo "  - $target   [${TARGET_LABELS[$idx]}]"
  idx=$((idx+1))
done
echo ""
echo "Skill ใหม่ที่เพิ่ม: ${#NEW_LIST[@]} รายการ"
for i in "${NEW_LIST[@]}"; do echo "  + $i"; done
echo ""
echo "Skill ที่อัพเดททับ: ${#UPDATED_LIST[@]} รายการ"
for i in "${UPDATED_LIST[@]}"; do echo "  * $i"; done
