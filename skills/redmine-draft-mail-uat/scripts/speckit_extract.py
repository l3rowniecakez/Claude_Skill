#!/usr/bin/env python3
"""ดึงข้อมูลจาก Spec Kit ของงาน (speckit/<feature>/ : req/REQ_*.md, spec.md, tasks.md) มาเป็นแหล่งข้อเท็จจริงของเมล [แจ้ง UAT]
เพื่อให้เมล UAT "ไปทิศทางเดียวกับ speckit": รู้ว่าทำอะไรไปบ้าง, มีหน้าจอ/เมนูไหนต้องให้ทดสอบ, ผลที่คาดหวัง, ต้องมีภาพหน้าจอไหน

ใช้:
  python3 speckit_extract.py <speckit_dir | ticket/workspace dir> [--feature 12345]            # พิมพ์รายงาน (Markdown) + เขียน speckit_summary.json
  python3 speckit_extract.py <dir> --skeleton content_skeleton.json                           # สร้าง content.json ตั้งต้นสำหรับ build_mail.py (ต้องแก้ต่อ)
  python3 speckit_extract.py <dir> --coverage content.json                                    # ตรวจว่าเมลที่ร่างครอบคลุมทุกหน้าจอใน REQ หรือยัง
ค้นหาโฟลเดอร์อัตโนมัติ: ถ้าให้ path ที่ไม่ใช่ speckit จะหา  **/speckit/<feature>/spec.md  ภายใน 5 ชั้น (feature มาจาก .specify/feature.json ถ้าไม่ระบุ)
อ่านอย่างเดียว ไม่แก้ไฟล์ใดใน speckit
"""
import argparse, glob, json, os, re, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass


def find_feature_dir(root, feature=None):
    root = os.path.abspath(os.path.expanduser(root))
    cands = []
    if os.path.exists(os.path.join(root, "spec.md")):
        return root
    for base in [root] + [os.path.join(root, *["*"] * n) for n in range(1, 6)]:
        for sk in glob.glob(os.path.join(base, "speckit")):
            fj = os.path.join(sk, ".specify", "feature.json")
            fd = feature
            if not fd and os.path.exists(fj):
                try:
                    fd = json.load(open(fj, encoding="utf-8")).get("feature_directory")
                except Exception:
                    fd = None
            if fd and os.path.exists(os.path.join(sk, fd, "spec.md")):
                cands.append(os.path.join(sk, fd))
            elif not fd:
                cands += [os.path.dirname(p) for p in glob.glob(os.path.join(sk, "*", "spec.md"))]
    cands = sorted(set(cands))
    if not cands:
        sys.exit("ไม่พบ speckit/<feature>/spec.md ใต้ %s — ถ้างานนี้ยังไม่มี speckit ให้ใช้ข้อมูลจาก RM/FormEdit แทน (หรือทำ speckit ก่อนตามกฎของ /redmine-ur)" % root)
    if len(cands) > 1:
        print("พบหลาย feature: %s — ใช้ตัวแรก (ระบุ --feature เพื่อเลือก)" % cands, file=sys.stderr)
    return cands[0]


def sections(text):
    parts = re.split(r"(?m)^## SECTION (\d+)[^\n]*\n", text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def table_rows(block):
    rows = []
    for l in block.splitlines():
        if l.startswith("|") and not re.match(r"^\|[\s\-|:]+\|$", l):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            rows.append(cells)
    return rows[1:] if rows else []  # ตัด header


def parse_req(path):
    t = open(path, encoding="utf-8").read()
    meta = {}
    for r in table_rows(t.split("## SECTION 1")[0]):
        if len(r) >= 2: meta[r[0]] = r[1].strip("`")
    sec = sections(t)
    stories = []
    for m in re.finditer(r"\*\*User Story \d+:\s*(.+?)\*\*(.*?)(?=\*\*User Story \d+:|\n---\n|\Z)", sec.get(1, ""), re.S):
        body = m.group(2)
        ex = re.search(r"\*\*ตัวอย่างข้อมูลจริง.*?\*\*:?(.*?)\*\*Acceptance Scenario", body, re.S)
        gwt = {k.lower(): (re.search(r"\*\*%s\*\*\s*(.+)" % k, body) or [None, ""])[1].strip() for k in ("Given", "When", "Then")}
        stories.append(dict(title=m.group(1).strip(), example=(ex.group(1).strip() if ex else ""), **gwt))
    buttons = [dict(label=re.sub(r"\s*\(`[^`]*`\)", "", r[0]), action=r[1] if len(r) > 1 else "", behavior=r[2] if len(r) > 2 else "")
               for r in table_rows(sec.get(3, "").split("### 3.3")[-1])] if "### 3.3" in sec.get(3, "") else []
    msgs = [dict(id=r[0], when=r[1], text=r[2]) for r in table_rows(sec.get(6, "")) if len(r) >= 3 and r[0].startswith("MSG")]
    openq = [dict(id=r[0], q=r[1], status=r[3], ans=r[4] if len(r) > 4 else "") for r in table_rows(sec.get(9, "")) if len(r) >= 4 and r[0].startswith("Q-")]
    acs = [dict(id=r[0], text=r[1], how=r[2] if len(r) > 2 else "") for r in table_rows(sec.get(11, "")) if r and r[0].startswith("AC-")]
    return dict(file=os.path.basename(path), screen_id=meta.get("Screen ID", ""), name=meta.get("ชื่อหน้าจอ", ""), module=meta.get("Module", ""),
                status=meta.get("สถานะ", ""), stories=stories, buttons=buttons, messages=msgs, open_questions=openq, acceptance=acs)


def parse_tasks(path):
    out = []
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            m = re.match(r"^- \[([ xX])\] (T\d+)\s*(?:\[P\])?\s*(?:\[(US\d+)\])?\s*(.+)", l.strip())
            if m: out.append(dict(done=m.group(1).lower() == "x", id=m.group(2), story=m.group(3) or "", text=m.group(4)[:160]))
    return out


def parse_spec(path):
    t = open(path, encoding="utf-8").read()
    stories = [dict(n=m.group(1), title=m.group(2).strip(), prio=m.group(3)) for m in re.finditer(r"### User Story (\d+) - (.+?) \(Priority: (P\d)\)", t)]
    frs = [dict(id=m.group(1), text=m.group(2).strip()[:200]) for m in re.finditer(r"- \*\*(FR-\d+)\*\*:\s*(.+)", t)]
    title = (re.search(r"# Feature Specification:\s*(.+)", t) or [None, ""])[1].strip()
    return dict(title=title, stories=stories, frs=frs)


def quoted(s):
    return re.findall(r"[\"“]([^\"”]{3,60})[\"”]", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--feature"); ap.add_argument("--skeleton"); ap.add_argument("--coverage"); ap.add_argument("--json-out")
    a = ap.parse_args()
    fd = find_feature_dir(a.path, a.feature)
    reqs = [parse_req(p) for p in sorted(glob.glob(os.path.join(fd, "req", "REQ_*.md")))]
    spec = parse_spec(os.path.join(fd, "spec.md"))
    tasks = parse_tasks(os.path.join(fd, "tasks.md"))
    summary = dict(feature_dir=fd, spec=spec, screens=reqs, tasks=tasks)
    if a.json_out:
        json.dump(summary, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if a.coverage:
        c = json.load(open(a.coverage, encoding="utf-8"))
        steps = c.get("steps", [])
        blob = " ".join([s.get("title", "") + " " + s.get("text", "") + " " + s.get("expect", "") for s in steps] + [json.dumps(c.get("details", []), ensure_ascii=False), json.dumps(c.get("table", {}), ensure_ascii=False)])
        print("# Coverage: เมล UAT เทียบ speckit (%s)" % fd)
        miss_total = 0
        for r in reqs:
            phrases = set(b["label"] for b in r["buttons"] if len(b["label"]) >= 3)
            for s in r["stories"]: phrases |= set(quoted(s["when"])) | set(quoted(s["then"]))
            phrases |= set(quoted(r["name"]))
            hit = [p for p in phrases if p in blob]; miss = sorted(set(phrases) - set(hit))
            ok = (len(hit) >= max(1, len(phrases) // 2)) if phrases else (r["name"][:12] in blob)
            miss_total += 0 if ok else 1
            print("- [%s] %s  %s (พบ %d/%d วลีสำคัญ)" % ("x" if ok else " ", r["screen_id"], r["name"][:70], len(hit), len(phrases)))
            if miss: print("    วลีที่ยังไม่ปรากฏในเมล: " + ", ".join(miss[:8]))
        need = [s for s in steps if s.get("image_placeholder") and not s.get("image")]
        have = [s for s in steps if s.get("image")]
        print("\nภาพ: ใส่แล้ว %d | ยังเป็น placeholder %d" % (len(have), len(need)))
        for s in need: print("  - ต้องถ่าย: " + s["image_placeholder"])
        print("\nหน้าจอที่ยังไม่ครอบคลุม: %d" % miss_total)
        return

    done = [t for t in tasks if t["done"]]; todo = [t for t in tasks if not t["done"]]
    print("# สรุปจาก Spec Kit: %s\nfeature dir: %s" % (spec["title"], fd))
    print("\n## งานตาม tasks.md: เสร็จ %d / ค้าง %d" % (len(done), len(todo)))
    print("   (ค้างที่เป็นการเขียนโค้ด/ฟีเจอร์ = ยังไม่พร้อม UAT ห้ามเขียนในเมลว่าให้ทดสอบ | ค้างที่เป็นทดสอบ/ยืนยัน/deploy = สิ่งที่ UAT จะช่วยปิด ใส่ในเมลได้)")
    for t in todo: print("  - [ ] %s %s %s" % (t["id"], t["story"], t["text"]))
    print("\n## User Story (spec.md)")
    for s in spec["stories"]: print("  - US%s [%s] %s" % (s["n"], s["prio"], s["title"]))
    print("\n## หน้าจอ/เมนูที่ต้องมีขั้นตอน UAT + ภาพ (จาก req/REQ_*.md): %d หน้าจอ" % len(reqs))
    for r in reqs:
        print("\n### %s — %s\n  โปรแกรม/โมดูล: %s | สถานะ REQ: %s" % (r["screen_id"], r["name"], r["module"], r["status"]))
        for s in r["stories"]:
            print("  • %s\n      Given: %s\n      When : %s\n      Then : %s" % (s["title"], s["given"][:160], s["when"][:160], s["then"][:200]))
            if s["example"]: print("      ตัวอย่างข้อมูล (ระวัง PDPA/ทดสอบ SIT): " + re.sub(r"\s+", " ", s["example"])[:220])
        if r["buttons"]: print("  ปุ่ม/เมนู: " + " | ".join(b["label"] for b in r["buttons"]))
        for m in r["messages"]: print("  ข้อความที่ผู้ใช้เห็น (%s): %s" % (m["id"], m["text"][:120]))
        for q in r["open_questions"]:
            if q["status"].lower() == "open": print("  ⚠ ยังเปิด %s: %s" % (q["id"], q["q"][:130]))
        print("  ภาพที่ต้องมี: ภาพหน้าจอก่อนทำ + หลังทำของแต่ละ scenario ข้างต้น (ปิดข้อมูลส่วนบุคคลทุกภาพ)")

    if a.skeleton:
        steps, rows, n = [], [], 0
        for r in reqs:
            for s in r["stories"]:
                n += 1
                steps.append(dict(title="%d. %s — %s" % (n, r["name"][:60], s["when"][:140] or s["title"]), text=("เงื่อนไขเริ่มต้น: " + s["given"][:180]) if s["given"] else "",
                                  image_placeholder="รอแทรกภาพ: %s — %s (ปิดข้อมูลส่วนบุคคล)" % (r["screen_id"], s["title"][:60]), expect=s["then"][:260]))
                rows.append(["%d. %s" % (n, s["title"][:50]), r["name"][:50], "{{เลข Batch/รายการที่เตรียมไว้บน UAT}}", s["then"][:80]])
        skeleton = dict(subject="[แจ้ง UAT] {{Task #N UR YYYYNNNN - %s}}" % spec["title"][:80], salutation="เรียน {{ฝ่าย/ชื่อผู้รับ}} และทุกท่านที่เกี่ยวข้อง", title=spec["title"],
                        redmine="{{Task #N UR YYYYNNNN - ชื่อเรื่อง}}", path_blocks=[dict(label="{{ฝ่ายที่ใช้}}", path="{{ตาม profile uat_path_blocks (ล่าสุด)}}", program="{{โปรแกรม.exe}}")],
                        objectives=["{{สรุปจาก spec.md ข้อ User Story/FR}}"], before=["{{เดิม}}"], after=["{{หลังแก้ไข}}"],
                        details=[dict(title="%s (%s)" % (r["name"][:70], r["screen_id"]), bullets=[b["label"] + ": " + (b["behavior"] or b["action"])[:120] for b in r["buttons"][:6]]) for r in reqs],
                        table=dict(title="เคสทดสอบที่เตรียมไว้ให้บน UAT", headers=["เคส", "เมนู / แท็บ", "ข้อมูลที่เตรียมไว้", "ผลที่ควรได้"], rows=rows),
                        steps=steps, image_width=640)
        json.dump(skeleton, open(a.skeleton, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\nเขียน content ตั้งต้นที่ %s (ต้องปรับถ้อยคำ/ตัดงานที่ยังไม่เสร็จ/ใส่ข้อมูลจริง ก่อน build_mail.py)" % a.skeleton)


if __name__ == "__main__":
    main()
