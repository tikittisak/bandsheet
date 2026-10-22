---
color: var(--mk-color-orange)
---
# Bandsheet Workflow

ไฟล์นี้คือ workflow หลักสำหรับ update index, ตรวจไฟล์ก่อน push, และ push ขึ้น GitHub

## เริ่มต้น

```bash
cd "/Users/ti_am1/vaults/ti.muse/apps/bandsheet"
```

หลังจากนั้นใช้คำสั่งด้านล่างได้เลย

## Workflow หลัก หลังแก้หรือเพิ่มเพลง

1. ดึงของล่าสุดจาก GitHub ก่อน ถ้าเคยแก้หรือ upload file ผ่านหน้าเว็บ GitHub

```bash
bash commands/sync-latest.sh
```

2. เช็กก่อน push จริง

```bash
bash commands/dry-run.sh
```

คำสั่งนี้มี **content guard**: ถ้า metadata, chord, lyric, section หรือ footer
ของเพลงเปลี่ยนโดยไม่ได้ระบุชื่อไฟล์ คำสั่งจะหยุดทันที งานแก้ template/CSS
จึงไม่สามารถเขียนทับเนื้อเพลงเงียบ ๆ ได้อีก

ก่อนแสดงรายการไฟล์ คำสั่งนี้จะตรวจ source truth, duplicate references,
playlist links, sheet metadata และ external dependencies พร้อมเขียนรายงานไว้ที่
`_work/reports/bandsheet-change-report-YYYY-MM-DD.md`

ถ้าต้องการตรวจอย่างเดียวโดยไม่ทำ dry-run:

```bash
bash commands/validate.sh
```

คำสั่งนี้จะ:
- อัปเดต index ให้ล่าสุด
- แสดงรายการไฟล์ที่จะถูกส่งขึ้น GitHub
- ไม่ stage, ไม่ commit, ไม่ push

3. ถ้ารายการไฟล์ถูกต้อง ค่อย push จริง

```bash
bash commands/push-site.sh "update bandsheet workflow and parkhaus songs"
```

ถ้าตั้งใจแก้ข้อมูลเพลง ต้องระบุทุกไฟล์แบบ exact allowlist ทั้งตอนตรวจและตอน push:

```bash
bash commands/dry-run.sh --allow-content songs/take-me-out.html
bash commands/push-site.sh "update: take me out bandsheet" --allow-content songs/take-me-out.html
```

ห้ามใช้ allowlist แบบกว้างหรือใส่ชื่อเพลงที่ไม่ได้เปลี่ยน; guard จะ reject
allowlist ที่ไม่มี semantic change เพื่อกันการอนุมัติค้างจากงานเก่า

หลัง Ti เปิดตรวจและยืนยันว่าเพลงถูกต้องแล้ว ให้ล็อก fingerprint ของ content:

```bash
python3 content_guard.py --lock songs/take-me-out.html \
  --approval-note "Ti reviewed full sheet after rehearsal correction"
```

`content-locks.json` จะเก็บเฉพาะ SHA-256 ของ metadata/chord/lyric/sections/footer
ไม่เก็บเนื้อเพลงซ้ำ เมื่อเพลงที่ล็อกแล้วเปลี่ยน `dry-run` และ `push` จะหยุด
แม้มี `--allow-content` จนกว่า Ti จะตรวจ revision ใหม่และสั่งล็อก fingerprint ใหม่

## ก่อนออกไปซ้อมหรือเล่นจริง

รัน preflight กับ playlist ที่จะใช้:

```bash
bash commands/rehearsal-check.sh playlists/tmj/2026-muse-cover-main.json
```

คำสั่งจะแสดงทุกเพลงว่า arrangement ครบหรือยัง และ content ตรงกับ fingerprint
ที่ Ti เคยยืนยันหรือไม่ ถ้ามีเพลง blank, incomplete หรือ unlocked จะคืน exit code ผิดพลาด
และเขียนรายงานไว้ใน `_work/reports/` ห้ามถือว่า playlist พร้อมหน้างานจนกว่าจะผ่าน
เพลงบรรเลงที่ตั้งใจไม่มี lyric block ให้ใส่ `"lyricsOptional": true` ใน playlist JSON
เพื่อให้ preflight แยกข้อยกเว้นที่ตั้งใจออกจากข้อมูลที่หาย

เปลี่ยนข้อความในเครื่องหมายคำพูดได้ตามงานรอบนั้น เช่น:

```bash
bash commands/push-site.sh "add: blue-bird bandsheet"
```

## Import ไฟล์ HTML ที่แก้จาก browser/download

ห้าม copy ไฟล์จาก Downloads ทับ `songs/*.html` ตรง ๆ ให้ดึงเฉพาะ data แล้ว regenerate จาก `_template.html`

สำคัญ: การแก้ที่ยังค้างอยู่ใน browser ไม่ได้ถูกบันทึกลง Git อัตโนมัติ ก่อนปิด tab,
เปลี่ยน URL/path, sync template หรือเริ่ม migration ต้องกด `Save HTML` ก่อน แล้วตรวจว่าไฟล์ export
อยู่จริง ถ้า Ti บอกว่าแก้เสร็จแล้วแต่หา export ไม่เจอ ให้หยุดและรายงาน `provenance gap` — ห้ามถือว่า
ไฟล์ใน Git คือ revision ล่าสุด และห้ามดึงเนื้อจาก web มาแทน revision ที่หาย

```bash
python3 import_edited_song_html.py "/Users/ti_am1/Downloads/ศรัทธา edit.html" --output songs/sattha.html --check
python3 import_edited_song_html.py "/Users/ti_am1/Downloads/ศรัทธา edit.html" --output songs/sattha.html
python3 update_index.py
bash commands/dry-run.sh --allow-content songs/sattha.html
```

หลัง import ให้เปิดไฟล์ output ตรวจเทียบกับ export และให้ Ti ยืนยันก่อนสร้าง content lock

## Workflow รอง อัปเดต index อย่างเดียว

ใช้เมื่อต้องการ rebuild หน้า index ในเครื่อง แต่ยังไม่อยากเช็กหรือ push

```bash
bash commands/update-index.sh
```

ปกติไม่ต้องรันก่อน `dry-run.sh` หรือ `push-site.sh` เพราะสองคำสั่งนั้นอัปเดต index ให้อัตโนมัติอยู่แล้ว

## ลำดับที่แนะนำ

```text
แก้/เพิ่มเพลง
→ bash commands/sync-latest.sh
→ bash commands/dry-run.sh
→ อ่านรายการไฟล์
→ ถ้าถูกต้อง: bash commands/push-site.sh "update bandsheet workflow and parkhaus songs"
```

## หยุดก่อน push ถ้าเห็นไฟล์แปลก ๆ

ถ้า `dry-run.sh` แสดงไฟล์ที่ไม่ตั้งใจ เช่น:

```text
.space/
song-transcription/
backup/
ไฟล์ทดลอง
ไฟล์รูปจำนวนมาก
```

ให้หยุดก่อน อย่าเพิ่งรัน `push-site.sh`
