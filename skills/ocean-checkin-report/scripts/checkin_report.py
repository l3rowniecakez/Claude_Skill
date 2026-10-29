#!/usr/bin/env python3
"""Count office (ci/co) / WFH / leave DAYS per person from a Google Chat check-in space.

Usage:
  checkin_report.py --name "กฤตกร"            [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--space ID|ชื่อห้อง] [--raw]
  checkin_report.py --all                     [--since ...] [--until ...]
  checkin_report.py --list-people             [--since ...] [--until ...]

Default range = last 3 months up to today. Default space = developer-check-in.
Read-only: uses ~/.config/claude-google-access/token.json (chat.messages.readonly).
"""
import argparse
import collections
import datetime as dt
import os
import re
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat_client import get_service, list_messages, resolve_space  # noqa: E402

DEFAULT_SPACE = "spaces/AAQA2x4c_Dw"  # developer-check-in
TZ = dt.timezone(dt.timedelta(hours=7))
MIDNIGHT_CUTOFF_HOUR = 5  # check-out posted before 05:00 belongs to the previous workday
LEAVE_CODES = {"sl": "SL", "sick": "SL", "vac": "VAC", "pl": "PL", "fam": "FAM", "mar": "MAR", "et": "ET"}
TIME_RANGE = re.compile(r"\d{1,2}[.:]\d{2}")
DATE_TOKEN = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
TH_MONTH = {7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.", 1: "ม.ค.",
            2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย."}


def first_word(text):
    return re.split(r"[\s\-:/]", text.strip().lower(), maxsplit=1)[0]


def parse_dates(text):
    """Explicit dates in a leave message: dd/mm/yyyy lists or a 'd1-d2' range (BE years ok)."""
    out = []
    for d, m, y in DATE_TOKEN.findall(text):
        y = int(y) - 543 if int(y) > 2400 else int(y)
        try:
            out.append(dt.date(y, int(m), int(d)))
        except ValueError:
            pass
    if len(out) == 2 and re.search(r"\d{4}\s*-\s*\d{1,2}/", text):  # range: expand weekdays
        a, b = out
        out = [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]
    return [d for d in out if d.weekday() < 5]


def classify(text):
    w = first_word(text)
    if w.startswith("wfh"):
        return "W", None
    if w in ("ci", "co"):
        return "O", None
    if w in LEAVE_CODES:
        return "L", LEAVE_CODES[w]
    return None, None


def fetch(space, since, until):
    svc = get_service()
    space, label = resolve_space(svc, space)
    return list_messages(svc, space, since.isoformat(), until.isoformat()), label


def build_days(msgs, user):
    """day -> {'kinds': set, 'leave': [(code, partial, text)], 'texts': [str], 'checkin': bool}"""
    days = collections.defaultdict(lambda: {"kinds": set(), "leave": [], "texts": [], "checkin": False})
    for m in msgs:
        if m.get("sender", {}).get("name") != user:
            continue
        text = m.get("text", "").strip()
        kind, code = classify(text)
        if not kind:
            continue
        t = dt.datetime.fromisoformat(m["createTime"].replace("Z", "+00:00")).astimezone(TZ)
        d = t.date()
        if t.hour < MIDNIGHT_CUTOFF_HOUR and kind in ("W", "O"):
            d -= dt.timedelta(days=1)
        if kind == "L":
            explicit = parse_dates(text)
            partial = bool(TIME_RANGE.search(text)) and not explicit
            for ld in explicit or [d]:
                days[ld]["kinds"].add("L")
                days[ld]["leave"].append((code, partial, text))
                days[ld]["texts"].append(f'{t:%H:%M} {text}')
            continue
        days[d]["kinds"].add(kind)
        if first_word(text) == "ci" or (kind == "W" and not re.match(r"wfh\s*-?\s*co", text.lower())):
            days[d]["checkin"] = True
        days[d]["texts"].append(f'{t:%H:%M} {text}')
    return days


def day_status(info):
    k = info["kinds"]
    if "O" in k and "W" in k:
        return "BOTH"
    if "O" in k:
        return "O"
    if "W" in k:
        return "W"
    return "L"


def report(name, days, since, until, today, raw=False):
    stat = {d: day_status(i) for d, i in days.items() if since <= d <= until}
    months = sorted({(d.year, d.month) for d in stat} | {(since.year, since.month), (until.year, until.month)})
    print(f"## {name}  ({since:%d/%m/%Y} – {until:%d/%m/%Y})\n")
    print("| เดือน | เข้าออฟฟิศ (วัน) | WFH (วัน) | ไม่ชัด ci+wfh (วัน) | ลาเต็มวัน (วัน) |")
    print("|---|---|---|---|---|")
    tot = collections.Counter()
    for y, mo in months:
        c = collections.Counter(s for d, s in stat.items() if (d.year, d.month) == (y, mo))
        leave_codes = collections.Counter(
            days[d]["leave"][0][0] for d, s in stat.items() if (d.year, d.month) == (y, mo) and s == "L")
        lv = f'{c["L"]} วัน' + (f' ({", ".join(f"{k} {v}" for k, v in leave_codes.items())})' if c["L"] else "")
        print(f'| {TH_MONTH[mo]} {y} | {c["O"]} วัน | {c["W"]} วัน | {c["BOTH"]} วัน | {lv} |')
        tot.update(c)
    print(f'| **รวม** | **{tot["O"]} วัน** | **{tot["W"]} วัน** | **{tot["BOTH"]} วัน** | **{tot["L"]} วัน** |\n')

    def fmt(ds):
        return ", ".join(d.strftime("%d/%m") for d in sorted(ds)) or "-"

    print(f'- วันเข้าออฟฟิศ: {fmt(d for d, s in stat.items() if s == "O")}')
    print(f'- วัน WFH: {fmt(d for d, s in stat.items() if s == "W")}')
    both = [d for d, s in stat.items() if s == "BOTH"]
    if both:
        print(f'- ไม่ชัด (มีทั้ง ci/co และ wfh วันเดียวกัน): {fmt(both)}')
    for d in sorted(d for d, s in stat.items() if s == "L"):
        print(f'- ลา {d:%d/%m}: {" / ".join(t for _, _, t in days[d]["leave"])}')
    partial = [(d, l) for d, s in stat.items() if s != "L" for l in days[d]["leave"]]
    for d, (code, _, t) in sorted(partial):
        print(f'- ลาบางช่วง (ยังนับเป็นวันทำงาน) {d:%d/%m}: {t}')
    co_only = [d for d, s in stat.items() if s in ("O", "W") and not days[d]["checkin"]]
    if co_only:
        print(f'- มีแค่ check-out ไม่มี check-in เช้า (ยังนับ): {fmt(co_only)}')
    missing = [since + dt.timedelta(days=i) for i in range((until - since).days + 1)]
    missing = [d for d in missing if d.weekday() < 5 and d not in stat and d != today]
    print(f'- วันธรรมดาที่ไม่มีข้อความเลย (อาจเป็นวันหยุด/ลาไม่แจ้ง): {fmt(missing)}')
    if until >= today and today.weekday() < 5 and today not in stat:
        print("- วันนี้ยังไม่ได้ check-in")
    if raw:
        print("\n### ข้อความดิบรายวัน")
        for d in sorted(days):
            if since <= d <= until:
                print(f'{d} {d:%a} [{stat[d]}] ' + " ;; ".join(days[d]["texts"]))


def main():
    today = dt.datetime.now(TZ).date()
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--name", help="substring of display name (Thai or English, case-insensitive)")
    g.add_argument("--all", action="store_true")
    g.add_argument("--list-people", action="store_true")
    ap.add_argument("--since", type=dt.date.fromisoformat)
    ap.add_argument("--until", type=dt.date.fromisoformat, default=today)
    ap.add_argument("--space", default=DEFAULT_SPACE, help="spaces/ID, ID, or display-name substring")
    ap.add_argument("--raw", action="store_true", help="also print raw messages per day")
    a = ap.parse_args()
    since = a.since or (a.until - dt.timedelta(days=92))
    msgs, space_label = fetch(a.space, since, a.until)
    print(f"ห้อง: {space_label} | ข้อความทั้งหมดในช่วง: {len(msgs)}\n")
    people = {}
    for m in msgs:
        s = m.get("sender", {})
        if s.get("type") == "HUMAN":
            people.setdefault(s["name"], s.get("displayName", s["name"]))

    if a.list_people:
        for uid, nm in sorted(people.items(), key=lambda x: x[1]):
            print(f"{nm}\t{uid}")
        return

    if a.all:
        print(f"| ชื่อ | เข้าออฟฟิศ (วัน) | WFH (วัน) | ไม่ชัด (วัน) | ลาเต็มวัน (วัน) |\n|---|---|---|---|---|")
        rows = []
        for uid, nm in people.items():
            days = build_days(msgs, uid)
            c = collections.Counter(day_status(i) for d, i in days.items() if since <= d <= a.until)
            if c:
                rows.append((nm, c))
        for nm, c in sorted(rows, key=lambda r: -r[1]["O"]):
            print(f'| {nm} | {c["O"]} | {c["W"]} | {c["BOTH"]} | {c["L"]} |')
        print(f"\nช่วง {since:%d/%m/%Y} – {a.until:%d/%m/%Y}, ทั้งหมด {len(rows)} คน")
        return

    q = a.name.lower()
    hits = {uid: nm for uid, nm in people.items() if q in nm.lower()}
    if not hits:
        sys.exit(f"ไม่พบชื่อที่มี '{a.name}' ในห้องช่วงนี้ — ลอง --list-people")
    if len(hits) > 1:
        print("พบหลายคน กรุณาระบุชื่อให้ชัดขึ้น:")
        for nm in hits.values():
            print(f"  - {nm}")
        sys.exit(2)
    uid, nm = next(iter(hits.items()))
    report(nm, build_days(msgs, uid), since, a.until, today, a.raw)


if __name__ == "__main__":
    main()
