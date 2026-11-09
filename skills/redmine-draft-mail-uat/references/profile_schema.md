# โครง profile.json (ถ้าต้องเขียนเองเมื่อไม่มีเมล [แจ้ง UAT] ให้เรียนรู้)

ไฟล์: `~/.config/redmine-draft-mail-uat/profile.json` (เฉพาะเครื่อง/ผู้ใช้ — ไม่อยู่ใน skill)

```json
{
  "account": "user@company.co.th",
  "subject": {"recent_examples": ["[แจ้ง UAT] Task #123 UR 20260001 - ชื่อเรื่อง"]},
  "salutation_top": [["เรียน ทุกท่านที่เกี่ยวข้อง", 1]],
  "uat_path_blocks": [{"lines": ["\\\\server\\share\\UAT", "เข้าโปรแกรม App.exe"], "used": 1, "last_used": "2026-01-01"}],
  "contact_line_top": [["กรณีติดปัญหา แจ้งทาง Chat หรือแจ้งทาง loop mail นี้ได้เลยครับ", 1]],
  "separator_top": [["============================================================", 1]],
  "closing_top": [["จึงเรียนมาเพื่อทดสอบระบบ", 1]],
  "signature": "Best regards,\n\nชื่อ นามสกุล\nแผนก\nบริษัท\nE-mail: user@company.co.th",
  "html_style": {"before_color": "#ff0000", "after_color": "#38761d", "image_width_median": 542}
}
```
ฟิลด์ที่ `build_mail.py` ใช้: `html_style.*`, `separator_top`, `contact_line_top`, `closing_top`, `signature` (ที่เหลือใช้เพื่อเสนอตัวเลือกให้ผู้ใช้เลือก)
