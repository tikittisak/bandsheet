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

เปลี่ยนข้อความในเครื่องหมายคำพูดได้ตามงานรอบนั้น เช่น:

```bash
bash commands/push-site.sh "add: blue-bird bandsheet"
```

## Import ไฟล์ HTML ที่แก้จาก browser/download

ห้าม copy ไฟล์จาก Downloads ทับ `songs/*.html` ตรง ๆ ให้ดึงเฉพาะ data แล้ว regenerate จาก `_template.html`

```bash
python3 import_edited_song_html.py "/Users/ti_am1/Downloads/ศรัทธา edit.html" --output songs/sattha.html --check
python3 import_edited_song_html.py "/Users/ti_am1/Downloads/ศรัทธา edit.html" --output songs/sattha.html
python3 update_index.py
```

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
