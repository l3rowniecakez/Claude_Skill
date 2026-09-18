#!/usr/bin/env python3
"""Detect silent duplicate-code risk after `git merge --no-commit --no-ff <ticket_ref>`.

Scenario this catches: git's line-based 3-way merge applies cleanly (no
conflict) because the diff hunk context shifted, but the content ticket/N
adds already exists elsewhere in the merged file -- i.e. someone else
already merged this same code into master through a different path
(cherry-pick, manual re-apply, another ticket), and we're about to merge
it in a second time.

Run this AFTER `git merge --no-commit --no-ff <ticket_ref>` succeeds with
no conflicts, and BEFORE `git commit`. If it reports DUPLICATE_RISK_FOUND,
show the findings to the user and get explicit confirmation before
committing the merge. If CLEAN, proceed to commit as normal.

Usage: check_duplicate_merge.py <repo_path> <ticket_ref>
Exit 0 = clean, 1 = duplicate risk found, 2 = usage/setup error.
"""
import subprocess
import sys

MIN_BLOCK_LINES = 1
MIN_TOTAL_CONTENT_LEN = 25  # sum of stripped-line lengths in a block, not a single line's length


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout


def extract_added_blocks(diff_text):
    blocks = []
    cur = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            cur.append(line[1:])
        else:
            if len(cur) >= MIN_BLOCK_LINES:
                blocks.append(cur)
            cur = []
    if len(cur) >= MIN_BLOCK_LINES:
        blocks.append(cur)
    return blocks


def is_substantive(block):
    return sum(len(l.strip()) for l in block) >= MIN_TOTAL_CONTENT_LEN


def main():
    if len(sys.argv) != 3:
        print("usage: check_duplicate_merge.py <repo_path> <ticket_ref>")
        sys.exit(2)
    repo, ticket_ref = sys.argv[1], sys.argv[2]

    merge_base = run(["git", "-C", repo, "merge-base", "origin/master", ticket_ref], repo).strip()
    if not merge_base:
        print("ERROR: cannot find merge-base between origin/master and %s" % ticket_ref)
        sys.exit(2)

    changed_files = run(
        ["git", "-C", repo, "diff", "--name-only", merge_base, ticket_ref], repo
    ).splitlines()

    findings = []
    for f in changed_files:
        diff_text = run(["git", "-C", repo, "diff", merge_base, ticket_ref, "--", f], repo)
        blocks = [b for b in extract_added_blocks(diff_text) if is_substantive(b)]
        if not blocks:
            continue

        try:
            with open("%s/%s" % (repo, f), "r", encoding="utf-8", errors="ignore") as fh:
                merged_content = fh.read()
        except OSError:
            continue

        for block in blocks:
            block_text = "\n".join(block)
            occurrences = merged_content.count(block_text)
            if occurrences >= 2:
                findings.append((f, block[:3], occurrences))

    if findings:
        print("DUPLICATE_RISK_FOUND")
        for f, snippet, occ in findings:
            print("--- %s (พบเนื้อโค้ดเดียวกันซ้ำ %d ครั้งในไฟล์หลัง merge) ---" % (f, occ))
            for l in snippet:
                print("  " + l)
        sys.exit(1)
    else:
        print("CLEAN")
        sys.exit(0)


if __name__ == "__main__":
    main()
