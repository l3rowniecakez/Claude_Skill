#!/usr/bin/env python3
"""เรียนรู้ "พฤติกรรมการส่งเมลแจ้ง UAT" ของผู้ใช้คนนี้ จากเมลขาออก (Sent) ที่ subject ขึ้นต้น [แจ้ง UAT] / [แจ้งUAT]

ใช้ครั้งแรกบนทุกเครื่อง/ทุกบัญชี (หรือเมื่อสั่ง --refresh) — ผลลัพธ์เก็บที่ ~/.config/redmine-draft-mail-uat/
  profile.json   สรุปรูปแบบ (subject, คำขึ้นต้น, บล็อก Path UAT, หัวข้อที่ใช้, สี, ลายเซ็น ฯลฯ)
  samples/*.txt  ตัวอย่างข้อความเมลล่าสุด (เก็บในเครื่องเท่านั้น ไม่อยู่ใน skill / ห้าม push ขึ้น repo)

ใช้: python3 learn_style.py [--years 3] [--max 60] [--query '<gmail query เพิ่มเติม>'] [--refresh]
อ่านอย่างเดียว (ไม่ส่ง/ไม่แก้เมลใดๆ)
"""
import argparse, base64, collections, datetime, html as htmlmod, json, os, re, statistics, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

SUBJ_RE = re.compile(r"^\s*(?:(re|fwd?|fw|ตอบกลับ)\s*:\s*)*\[\s*แจ้ง\s*UAT\s*\]", re.I)
REPLY_RE = re.compile(r"^\s*(re|fwd?|fw|ตอบกลับ)\s*:", re.I)


def walk(p, out):
    out.append(p)
    for q in p.get("parts", []) or []:
        walk(q, out)


def body_of(parts, kind):
    for p in parts:
        if p["mimeType"] == kind and p["body"].get("data"):
            return base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8", "replace")
    return ""


def fetch_full(svc, mid, fmt="full"):
    """ดึงเมลพร้อม retry/backoff เมื่อชน rate limit (403 rateLimitExceeded / 429 / 5xx)"""
    import time
    from googleapiclient.errors import HttpError
    delay = 5
    for attempt in range(8):
        try:
            return svc.users().messages().get(userId="me", id=mid, format=fmt).execute()
        except HttpError as e:
            code = getattr(e.resp, "status", 0)
            if code in (403, 429, 500, 502, 503) and attempt < 7:
                print("  … rate limit (%s) รอ %ds แล้วลองใหม่" % (code, delay), flush=True)
                time.sleep(delay); delay = min(delay * 2, 60)
                continue
            raise


def strip_md(t):
    return re.sub(r"^\*+|\*+$", "", t.strip()).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=float, default=3)
    ap.add_argument("--max", type=int, default=60, help="จำนวนเมลต้นฉบับล่าสุดที่ใช้วิเคราะห์")
    ap.add_argument("--query", default="")
    ap.add_argument("--refresh", action="store_true", help="เรียนรู้ใหม่ทับ profile เดิม")
    a = ap.parse_args()

    if common.load_profile() and not a.refresh:
        sys.exit("มี profile อยู่แล้ว (%s) — ใช้ --refresh ถ้าต้องการเรียนรู้ใหม่" % common.PROFILE_PATH)

    svc, tokpath = common.gmail_service("read")
    me = svc.users().getProfile(userId="me").execute()["emailAddress"]
    since = (datetime.date.today() - datetime.timedelta(days=int(a.years * 365))).strftime("%Y/%m/%d")
    q = 'in:sent after:%s (subject:"[แจ้ง UAT]" OR subject:"[แจ้งUAT]") %s' % (since, a.query)
    ids, tok = [], None
    while True:
        r = svc.users().messages().list(userId="me", q=q, maxResults=100, pageToken=tok).execute()
        ids += [m["id"] for m in r.get("messages", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    print("พบเมลขาออกที่ match คำค้น: %d ฉบับ (บัญชี %s)" % (len(ids), me))

    # รอบที่ 1: ดึงเฉพาะ header (ถูก) เพื่อคัดต้นฉบับ [แจ้ง UAT] ที่ไม่ใช่ Re:/Fwd: แล้วเลือก N ฉบับล่าสุด
    meta = []
    for mid in ids:
        d = fetch_full(svc, mid, "metadata")
        h = {x["name"].lower(): x["value"] for x in d["payload"]["headers"]}
        subj = h.get("subject", "")
        if SUBJ_RE.match(subj) and not REPLY_RE.match(subj):
            meta.append((int(d["internalDate"]), mid, subj))
    meta.sort(reverse=True)
    meta = meta[: a.max]
    print("ต้นฉบับ (ไม่นับ Re:/Fwd:) ที่จะดึงเนื้อหา: %d ฉบับ" % len(meta), flush=True)

    # รอบที่ 2: ดึงเนื้อหาเต็มเฉพาะที่เลือก (ช้าๆ กันชน quota)
    import time
    mails = []
    for _, mid, _s in meta:
        d = fetch_full(svc, mid, "full")
        time.sleep(0.4)
        h = {x["name"].lower(): x["value"] for x in d["payload"]["headers"]}
        subj = h.get("subject", "")
        parts = []
        walk(d["payload"], parts)
        mails.append(dict(id=mid, date=int(d["internalDate"]), subject=subj,
                          to=len([x for x in h.get("to", "").split(",") if x.strip()]),
                          cc=len([x for x in h.get("cc", "").split(",") if x.strip()]),
                          text=body_of(parts, "text/plain"), html=body_of(parts, "text/html"),
                          images=len([p for p in parts if p["mimeType"].startswith("image/")])))
    mails.sort(key=lambda m: -m["date"])
    mails = mails[: a.max]
    if not mails:
        sys.exit("ไม่พบเมลต้นฉบับขึ้นต้น [แจ้ง UAT] ในช่วง %s ปี — ให้ถามผู้ใช้ว่าปกติส่งแจ้ง UAT อย่างไร แล้วเขียน profile เองตามโครงใน references/profile_schema.md" % a.years)
    print("ใช้วิเคราะห์: %d ฉบับ (ต้นฉบับ ไม่นับ Re:/Fwd:) ล่าสุด %s" % (len(mails), datetime.datetime.fromtimestamp(mails[0]["date"] / 1000).strftime("%Y-%m-%d")))

    # ---- subject
    kinds = collections.Counter()
    for m in mails:
        s = m["subject"]
        k = []
        if re.search(r"Task\s*#\d+", s): k.append("Task #N")
        if re.search(r"UR\s*:?\s*\[?\d{8}", s): k.append("UR YYYYNNNN")
        if re.search(r"GLF-\d+", s): k.append("GLF-N")
        if re.search(r"#\d+", s) and "Task" not in s: k.append("#N")
        kinds["+".join(k) or "อื่นๆ"] += 1
    recent_subjects = [m["subject"] for m in mails[:8]]
    prefix_forms = collections.Counter(re.match(r"^\s*(\[\s*แจ้ง\s*UAT\s*\])", m["subject"]).group(1).replace(" ", "_") for m in mails)

    # ---- plain text analysis
    sal, paths, contacts, closings, headings = collections.Counter(), collections.defaultdict(lambda: dict(n=0, last=0)), collections.Counter(), collections.Counter(), collections.Counter()
    seps = collections.Counter()
    sigs = collections.Counter()
    for m in mails:
        lines = [strip_md(l) for l in m["text"].splitlines()]
        for l in lines:
            if l.startswith("เรียน"):
                sal[l] += 1; break
        for i, l in enumerate(lines):
            if "ช่องทาง" in l and "UAT" in l:
                blk = []
                for x in lines[i + 1: i + 8]:
                    if not x:
                        if blk: break
                        continue
                    if set(x) <= set("=- *"): break
                    if "กรณีติดปัญหา" in x: break
                    blk.append(x)
                key = " | ".join(blk)
                if key:
                    paths[key]["n"] += 1; paths[key]["last"] = max(paths[key]["last"], m["date"])
            if re.fullmatch(r"=+", l.replace(" ", "")) and len(l) > 10:
                seps["=" * min(len(l), 60)] += 1
            if l.startswith("จึงเรียนมา"):
                closings[l] += 1
            if len(l) < 60 and re.match(r"^(วัตถุประสงค์|จุดประสงค์|เดิม|หลังแก้ไข|รายละเอียด|ขั้นตอนการ|ปัญหาก่อน|วิธิการ|วิธีการ|ช่องทาง|เหตุผล|ผลการทดสอบ|ข้อควร|หมายเหตุ)", l):
                headings[re.sub(r"\s*[:：].*$", "", l)] += 1
        tail = re.split(r"\r?\n-- ?\r?\n", m["text"])
        if len(tail) > 1:
            sigs[re.sub(r"[ \t]+\r?\n", "\n", tail[-1]).replace("\r", "").strip()] += 1

    for m in mails:
        plain = htmlmod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m["html"])))
        mt = re.search(r"\*{0,3}\s*(กรณีติดปัญหา.{0,160}?(?:ได้เลยครับ|ได้เลยค่ะ|ได้เลย))", plain)
        if mt:
            contacts[re.sub(r"\s+", " ", mt.group(1)).strip("* ")] += 1

    # ---- html style (สีของ "เดิม"/"หลังแก้ไข", ขนาดภาพ, ตัวหนา)
    def color_near(word):
        c = collections.Counter()
        for m in mails:
            for mt in re.finditer(r'<font[^>]*color="(#[0-9a-fA-F]{6})"[^>]*>(?:<[^>]+>)*\s*' + word, m["html"]):
                c[mt.group(1).lower()] += 1
        return c.most_common(1)[0][0] if c else None
    widths = [int(w) for m in mails for w in re.findall(r'<img[^>]*\swidth="(\d+)"', m["html"])]
    bold_ratio = statistics.mean([(m["html"].count("<b") / max(1, m["html"].count("<div"))) for m in mails if m["html"]] or [0])

    profile = dict(
        learned_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), account=me, token_used=os.path.basename(tokpath),
        window_years=a.years, mails_analyzed=len(mails),
        newest=datetime.datetime.fromtimestamp(mails[0]["date"] / 1000).strftime("%Y-%m-%d"),
        oldest=datetime.datetime.fromtimestamp(mails[-1]["date"] / 1000).strftime("%Y-%m-%d"),
        subject=dict(prefix_forms=dict(prefix_forms), kinds=dict(kinds), recent_examples=recent_subjects),
        salutation_top=sal.most_common(8),
        uat_path_blocks=[dict(lines=k.split(" | "), used=v["n"], last_used=datetime.datetime.fromtimestamp(v["last"] / 1000).strftime("%Y-%m-%d"))
                         for k, v in sorted(paths.items(), key=lambda kv: -kv[1]["last"])[:6]],
        contact_line_top=contacts.most_common(2),
        separator_top=seps.most_common(1),
        headings_top=headings.most_common(15),
        closing_top=closings.most_common(2),
        signature=(sigs.most_common(1)[0][0] if sigs else None),
        avg_images_per_mail=round(statistics.mean(m["images"] for m in mails), 1),
        median_to=statistics.median(m["to"] for m in mails), median_cc=statistics.median(m["cc"] for m in mails),
        html_style=dict(before_color=color_near("เดิม"), after_color=color_near("หลังแก้ไข"),
                        image_width_median=(int(statistics.median(widths)) if widths else None), bold_ratio=round(bold_ratio, 2)),
        source_mail_ids_recent=[m["id"] for m in mails[:5]],
    )
    os.makedirs(os.path.join(common.CONF_DIR, "samples"), exist_ok=True)
    json.dump(profile, open(common.PROFILE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for i, m in enumerate(mails[:3], 1):
        open(os.path.join(common.CONF_DIR, "samples", "sample%d_%s.txt" % (i, datetime.datetime.fromtimestamp(m["date"] / 1000).strftime("%Y%m%d"))), "w", encoding="utf-8").write(m["subject"] + "\n\n" + m["text"])
    os.chmod(common.PROFILE_PATH, 0o600)

    print("\n=== สรุปพฤติกรรมการส่งเมล UAT ของ %s ===" % me)
    print("ช่วงเมลที่วิเคราะห์: %s ถึง %s (%d ฉบับ)" % (profile["oldest"], profile["newest"], len(mails)))
    print("รูปแบบ subject:", dict(prefix_forms), dict(kinds))
    for s in recent_subjects[:5]: print("  ตย.:", s[:110])
    print("คำขึ้นต้นที่ใช้บ่อย:", [(s[:60], n) for s, n in sal.most_common(4)])
    print("บล็อก Path UAT (ล่าสุดก่อน):")
    for b in profile["uat_path_blocks"][:4]: print("  ใช้ %d ครั้ง ล่าสุด %s: %s" % (b["used"], b["last_used"], " / ".join(b["lines"])[:140]))
    print("หัวข้อที่ใช้บ่อย:", [(h, n) for h, n in headings.most_common(10)])
    print("ประโยคปิดท้าย:", closings.most_common(1), "| ภาพเฉลี่ย/ฉบับ:", profile["avg_images_per_mail"], "| กว้างภาพ (median):", profile["html_style"]["image_width_median"])
    print("สี เดิม/หลังแก้ไข:", profile["html_style"]["before_color"], profile["html_style"]["after_color"])
    print("\nบันทึก profile ที่", common.PROFILE_PATH)


if __name__ == "__main__":
    main()
