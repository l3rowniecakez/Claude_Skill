#!/usr/bin/env python3
"""ครอป/เบลอ/ทึบ ข้อมูลอ่อนไหว (PDPA) ในภาพ screenshot ก่อนใส่ในเมล — ใช้ Pillow เท่านั้น

ใช้: python3 blur_images.py spec.json
spec.json = {"out_dir": "<dir>", "max_width": 1000,
             "images": [{"src": "a.png", "out": "step1.png",
                         "crop": [l, t, r, b],              # ไม่บังคับ — พิกัดอ้างอิงภาพต้นฉบับ
                         "blur": [[l, t, r, b], ...],       # เบลอแรง (pixelate + gaussian) พิกัดอ้างอิงภาพต้นฉบับ
                         "black": [[l, t, r, b], ...] }]}   # ทึบดำ (ใช้กับเลขบัตร/เลขบัญชีที่ต้องปิดแน่นอน)
ขั้นตอนที่ถูกต้อง: ให้ Claude เปิดภาพดู (Read) -> ระบุพิกัดทุกจุดที่เป็นข้อมูลส่วนบุคคล -> รันสคริปต์ -> เปิดภาพผลลัพธ์ดูซ้ำก่อนใช้ทุกครั้ง
(ไม่มี OCR อัตโนมัติ — การตัดสินว่าจุดไหนอ่อนไหวเป็นหน้าที่ของคนตรวจ ห้ามข้ามขั้นตรวจซ้ำ)
"""
import hashlib, json, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass
from PIL import Image, ImageFilter


def protect(img, box, mode):
    l, t, r, b = [int(v) for v in box]
    l, t = max(0, l), max(0, t); r, b = min(img.width, r), min(img.height, b)
    if r <= l or b <= t:
        return
    region = img.crop((l, t, r, b))
    if mode == "black":
        region = Image.new("RGB", region.size, (0, 0, 0))
    else:
        # pixelate แล้ว blur — ถอดความกลับไม่ได้ (ไม่ใช่เบลอเบาๆ ที่ยังอ่านได้)
        w, h = region.size
        small = region.resize((max(1, w // 12), max(1, h // 12)), Image.BILINEAR)
        region = small.resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(6))
    img.paste(region, (l, t))


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out_dir = spec["out_dir"]; os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    for it in spec["images"]:
        img = Image.open(it["src"]).convert("RGB")
        # เบลอ/ทึบก่อน (พิกัดอ้างอิงภาพต้นฉบับ) แล้วค่อยครอป/ย่อ — กันพลาดเรื่องพิกัดเลื่อน
        for bx in it.get("blur", []): protect(img, bx, "blur")
        for bx in it.get("black", []): protect(img, bx, "black")
        if it.get("crop"): img = img.crop(tuple(it["crop"]))
        mw = spec.get("max_width", 1000)
        if img.width > mw:
            img = img.resize((mw, int(img.height * mw / img.width)), Image.LANCZOS)
        out = os.path.join(out_dir, it["out"])
        img.save(out, optimize=True)
        print("%s  %dx%d  %d KB" % (out, img.width, img.height, os.path.getsize(out) // 1024))
        manifest.setdefault("files", {})[hashlib.sha256(open(out, "rb").read()).hexdigest()] = it["out"]
    json.dump(manifest, open(os.path.join(out_dir, ".pdpa_processed.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("บันทึก manifest (.pdpa_processed.json) — create_draft.py จะรับเฉพาะภาพที่ผ่านสคริปต์นี้ (ยังต้องเปิดดูภาพผลลัพธ์ซ้ำเอง)")


if __name__ == "__main__":
    main()
