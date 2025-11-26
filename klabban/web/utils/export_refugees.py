import io
import datetime
from openpyxl import Workbook

# สมมติว่า models อยู่ที่ models.py
from klabban.models.refugees import Refugee, REFUGEE_STATUS_CHOICES, GENDER
from klabban.models.export_refugee_files import ExportRefugeeFile
from klabban import models


def process_refugee_export(refugee_camp_id, current_user):
    """
    ดึงข้อมูล Refugee ตาม camp_id และสร้างไฟล์ Excel (BytesIO)
    """
    # สร้าง Dictionary สำหรับแปลงค่า Choice ให้เป็นข้อความภาษาไทย
    gender_map = dict(GENDER)
    status_map = dict(REFUGEE_STATUS_CHOICES)

    # 1. Query ข้อมูล
    refugees = Refugee.objects(refugee_camp=refugee_camp_id)

    # 2. สร้าง Workbook และ Worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Refugee Data"

    # 3. กำหนด Header (ชื่อคอลัมน์)
    headers = [
        "ชื่อ-นามสกุล",
        "ชื่อเล่น",
        "สถานะ",
        "เพศ",
        "อายุ",
        "สัญชาติ",
        "เชื้อชาติ",
        "ประเทศต้นทาง",
        "เบอร์โทร",
        "โรคประจำตัว",
        "ที่อยู่",
        "สัตว์เลี้ยง",
        "จำนวนคน (รวม)",
        "ผู้ติดต่อฉุกเฉิน",
        "หมายเหตุ",
        "วันที่ลงทะเบียน",
        "วันที่คาดว่าจะพัก (วัน)",
        "วันที่กลับบ้าน",
    ]
    ws.append(headers)

    # 4. วนลูปใส่ข้อมูล
    for r in refugees:
        # จัดการเรื่องวันที่ (ป้องกัน error กรณีเป็น None)
        reg_date = (
            r.registration_date.strftime("%Y-%m-%d %H:%M")
            if r.registration_date
            else ""
        )
        back_date = (
            r.back_home_date.strftime("%Y-%m-%d %H:%M") if r.back_home_date else ""
        )

        # แปลงค่าจาก key เป็น label ภาษาไทย (ถ้าไม่มี key ให้ใช้ค่าเดิม)
        gender_display = gender_map.get(r.gender, r.gender)
        status_display = status_map.get(r.status, r.status)

        row = [
            r.name,
            r.nick_name or "-",
            status_display,
            gender_display,
            r.age or 0,
            r.nationality or "-",
            r.ethnicity or "-",
            r.country or "-",
            r.phone or "-",
            r.congenital_disease or "-",
            r.address or "-",
            r.pets or "-",
            r.people_count,
            r.emergency_contact or "-",
            r.remark or "-",
            reg_date,
            r.expected_days or "",
            back_date,
        ]
        ws.append(row)

    # 5. Save ลง Memory Stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)  # เลื่อน pointer กลับไปที่จุดเริ่มต้นไฟล์
    refugee_camp = models.RefugeeCamp.objects.get(id=refugee_camp_id)
    export_refugee_file = ExportRefugeeFile.objects(refugee_camp=refugee_camp).first()
    if not export_refugee_file:
        export_refugee_file = ExportRefugeeFile(
            refugee_camp=refugee_camp,
            created_date=datetime.datetime.now(),
            creator=current_user,
        )
    export_refugee_file.updated_date = datetime.datetime.now()
    export_refugee_file.updater = current_user
    if not export_refugee_file.file:
        export_refugee_file.file.put(
            output,
            filename=f"refugee_export_{refugee_camp.name}.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        export_refugee_file.file.replace(
            output,
            filename=f"refugee_export_{refugee_camp.name}.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    export_refugee_file.save()
    return True
