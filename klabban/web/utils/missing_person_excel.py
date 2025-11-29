import datetime
import pandas as pd
from klabban import models
import datetime
import xlsxwriter
import re
from openpyxl import load_workbook
from io import BytesIO
from klabban.models.refugees import REFUGEE_STATUS_CHOICES, GENDER
from flask import flash

REQUIRE_HEADERS = [
    "ชื่อคนหาย/เสียชีวิต",
    "นามสกุลคนหาย/เสียชีวิต",
    "ชื่อผู้แจ้ง",
    "นามสกุลผู้แจ้ง",
]

HEADER = [
    # ข้อมูลคนหาย/เสียชีวิต
    "คำนำหน้าชื่อคนหาย/เสียชีวิต",
    "ชื่อคนหาย/เสียชีวิต",
    "นามสกุลคนหาย/เสียชีวิต",
    "อายุคนหาย/เสียชีวิต",
    "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
    "ประเทศคนหาย/เสียชีวิต",
    "จังหวัดคนหาย/เสียชีวิต",
    "อำเภอคนหาย/เสียชีวิต",
    "ตำบลคนหาย/เสียชีวิต",
    "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต",
    "สถานะ",  # missing หรือ death
    # ข้อมูลเพิ่มเติม
    "ลักษณะรูปพรรณ",
    "คำให้การ/สอบปากคำ",
    "วันที่รับศพ",
    "ความสัมพันธ์กับผู้หาย/เสียชีวิต",
    # ข้อมูลผู้แจ้ง
    "คำนำหน้าชื่อผู้แจ้ง",
    "ชื่อผู้แจ้ง",
    "นามสกุลผู้แจ้ง",
    "อายุผู้แจ้ง",
    "หมายเลขบัตรประชาชนผู้แจ้ง",
    "ประเทศผู้แจ้ง",
    "จังหวัดผู้แจ้ง",
    "อำเภอผู้แจ้ง",
    "ตำบลผู้แจ้ง",
    "ที่อยู่บ้านเลขที่ผู้แจ้ง",
    "เบอร์โทรศัพท์ผู้แจ้ง",
    "CODE",
]

MISSING_PERSON_STATUS_CHOICES = [
    ("missing", "สูญหาย"),
    ("death", "เสียชีวิต"),
]


def get_template():
    example_data = {
        "คำนำหน้าชื่อคนหาย/เสียชีวิต": ["นาย"],
        "ชื่อคนหาย/เสียชีวิต": ["สมชาย"],
        "นามสกุลคนหาย/เสียชีวิต": ["ใจดี"],
        "อายุคนหาย/เสียชีวิต": [30],
        "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต": ["1234567890123"],
        "ประเทศคนหาย/เสียชีวิต": ["ไทย"],
        "จังหวัดคนหาย/เสียชีวิต": ["กรุงเทพมหานคร"],
        "อำเภอคนหาย/เสียชีวิต": ["บางรัก"],
        "ตำบลคนหาย/เสียชีวิต": ["สี่พระยา"],
        "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต": ["123/45 ถนนสุขุมวิท"],
        "สถานะ": ["missing"],
        "ลักษณะรูปพรรณ": ["สูง 170 ซม. ผิวขาว"],
        "คำให้การ/สอบปากคำ": ["ออกไปทำงานแล้วหลับมาไม่พบ"],
        "วันที่รับศพ": [""],
        "ความสัมพันธ์กับผู้หาย/เสียชีวิต": ["พ่อ"],
        "คำนำหน้าชื่อผู้แจ้ง": ["นางสาว"],
        "ชื่อผู้แจ้ง": ["สมหญิง"],
        "นามสกุลผู้แจ้ง": ["ดีใจ"],
        "อายุผู้แจ้ง": [28],
        "หมายเลขบัตรประชาชนผู้แจ้ง": ["9876543210987"],
        "ประเทศผู้แจ้ง": ["ไทย"],
        "จังหวัดผู้แจ้ง": ["กรุงเทพมหานคร"],
        "อำเภอผู้แจ้ง": ["บางรัก"],
        "ตำบลผู้แจ้ง": ["สี่พระยา"],
        "ที่อยู่บ้านเลขที่ผู้แจ้ง": ["678/90 ถนนสุขุมวิท"],
        "เบอร์โทรศัพท์ผู้แจ้ง": ["0812345678"],
        "CODE": ["HY74/68 PSU"],
    }

    df = pd.DataFrame(example_data)

    output = BytesIO()
    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        date_format="dd/mm/yyyy",
        datetime_format="dd/mm/yyyy",
    ) as writer:
        df.to_excel(writer, sheet_name="ข้อมูลผู้อพยพ", index=False)

        workbook: xlsxwriter.Workbook = writer.book
        worksheet: xlsxwriter.workbook.Worksheet = writer.sheets["ข้อมูลผู้อพยพ"]

        # เพิ่ม format สำหรับ header และตัวอย่าง
        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1}
        )

        # จัด format header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # จัด format ตัวอย่าง
        for row_num in range(len(df)):
            for col_num in range(len(df.columns)):
                worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num])

        # ช่วงข้อมูลที่อนุญาตให้กรอก (เริ่มจากแถวที่ 3 เพราะแถว 1-2 เป็นตัวอย่าง)
        first_row, last_row = 3, 10000

        # source data
        # status_choices = [choice[1] for choice in REFUGEE_STATUS_CHOICES]
        # gender_choices = [choice[1] for choice in GENDER]

        # validations = {
        #     "สถานะ": status_choices,
        #     "เพศ": gender_choices,
        # }
        sheet_choices = "Choices_ตัวเลือกห้ามลบ"
        list_sheet = workbook.add_worksheet(sheet_choices)
        list_sheet.hide()  # ซ่อน sheet choices
        list_row = 0

        # loop สร้าง validation
        # for column_name, source in validations.items():
        #     col_idx = df.columns.get_loc(column_name)

        #     # join string เพื่อเช็กความยาว
        #     joined = ",".join(map(str, source))
        #     if len(joined) > 255:
        #         # เขียนลง Lists sheet
        #         start_row = list_row
        #         for i, val in enumerate(source):
        #             list_sheet.write(list_row, 0, val)
        #             list_row += 1
        #         end_row = list_row - 1

        #         # ใช้ช่วง reference
        #         rng = f"={sheet_choices}!$A${start_row+1}:$A${end_row+1}"
        #         worksheet.data_validation(
        #             first_row=first_row,
        #             first_col=col_idx,
        #             last_row=last_row,
        #             last_col=col_idx,
        #             options={"validate": "list", "source": rng},
        #         )
        #     else:
        #         # กรณีไม่เกิน 255 ใช้ list ได้เลย
        #         worksheet.data_validation(
        #             first_row=first_row,
        #             first_col=col_idx,
        #             last_row=last_row,
        #             last_col=col_idx,
        #             options={"validate": "list", "source": list(source)},
        #         )

        # ปรับความกว้างคอลัมน์อัตโนมัติ
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

    output.seek(0)
    return output


def validate_import_file(file, import_missing_person_files):
    if (
        file.filename
        and not file.filename.endswith(".xlsx")
        and not file.filename.endswith(".csv")
    ):
        import_missing_person_files.error_messages.append(
            "นามสกุลไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์ Excel หรือ CSV"
        )
        import_missing_person_files.save()
        return False

    try:
        if file.filename.endswith(".xlsx"):
            # อ่านทุก sheet
            excel_file = pd.ExcelFile(file)
            sheet_names = excel_file.sheet_names

            # ลบ sheet ที่เป็น choices หรือ hidden sheets
            valid_sheets = [s for s in sheet_names if not s.startswith("Choices_")]

            if not valid_sheets:
                import_missing_person_files.error_messages.append(
                    "ไม่พบ sheet ข้อมูลในไฟล์"
                )
                import_missing_person_files.save()
                return False

            all_errors = []
            total_rows = 0

            # validate แต่ละ sheet
            for sheet_name in valid_sheets:
                df = pd.read_excel(file, sheet_name=sheet_name)
                sheet_errors = validate_dataframe(df, sheet_name)

                if sheet_errors:
                    all_errors.extend(sheet_errors)
                else:
                    total_rows += len(df)

            if all_errors:
                import_missing_person_files.error_messages = all_errors
                import_missing_person_files.save()
                return False

            # บันทึกจำนวน sheet และ rows
            import_missing_person_files.metadata = {
                "total_sheets": len(valid_sheets),
                "total_rows": total_rows,
                "sheet_names": valid_sheets,
            }
            import_missing_person_files.save()

        else:  # CSV
            df = pd.read_csv(file)
            errors = validate_dataframe(df, "CSV")

            if errors:
                import_missing_person_files.error_messages = errors
                import_missing_person_files.save()
                return False

    except Exception as e:
        print(e)
        import_missing_person_files.error_messages = [
            f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}"
        ]
        import_missing_person_files.save()
        return False

    return True


def validate_dataframe(df, sheet_name):
    """Validate single dataframe"""
    errors = []

    # ตรวจสอบ column ที่จำเป็น
    missed_columns = []
    for col in REQUIRE_HEADERS:
        if col not in df.columns:
            missed_columns.append(col)

    if missed_columns:
        errors.append(f"[{sheet_name}] ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missed_columns)}")
        return errors

    # ตรวจสอบข้อมูลในแต่ละแถว
    for index, row in df.iterrows():
        row_errors = []

        # ตรวจสอบฟิลด์บังคับ
        if (
            pd.isna(row.get("ชื่อคนหาย/เสียชีวิต"))
            or str(row.get("ชื่อคนหาย/เสียชีวิต")).strip() == ""
        ):
            row_errors.append("ขาดชื่อคนหาย/เสียชีวิต")

        if (
            pd.isna(row.get("นามสกุลคนหาย/เสียชีวิต"))
            or str(row.get("นามสกุลคนหาย/เสียชีวิต")).strip() == ""
        ):
            row_errors.append("ขาดนามสกุลคนหาย/เสียชีวิต")

        if pd.isna(row.get("ชื่อผู้แจ้ง")) or str(row.get("ชื่อผู้แจ้ง")).strip() == "":
            row_errors.append("ขาดชื่อผู้แจ้ง")

        if pd.isna(row.get("นามสกุลผู้แจ้ง")) or str(row.get("นามสกุลผู้แจ้ง")).strip() == "":
            row_errors.append("ขาดนามสกุลผู้แจ้ง")

        # ตรวจสอบสถานะ
        if pd.notna(row.get("สถานะ")):
            status = str(row.get("สถานะ")).strip().lower()
            valid_statuses = [choice[0] for choice in MISSING_PERSON_STATUS_CHOICES]
            valid_statuses_thai = [
                choice[1] for choice in MISSING_PERSON_STATUS_CHOICES
            ]

            if status not in valid_statuses and status not in [
                s.lower() for s in valid_statuses_thai
            ]:
                row_errors.append(
                    f"สถานะไม่ถูกต้อง ต้องเป็น: {', '.join(valid_statuses_thai)}"
                )

        # ตรวจสอบอายุ
        if pd.notna(row.get("อายุคนหาย/เสียชีวิต")):
            try:
                age = int(float(row.get("อายุคนหาย/เสียชีวิต")))
                if age < 0 or age > 150:
                    row_errors.append("อายุคนหาย/เสียชีวิตต้องอยู่ระหว่าง 0-150 ปี")
            except:
                row_errors.append("อายุคนหาย/เสียชีวิตต้องเป็นตัวเลข")

        if pd.notna(row.get("อายุผู้แจ้ง")):
            try:
                age = int(float(row.get("อายุผู้แจ้ง")))
                if age < 0 or age > 150:
                    row_errors.append("อายุผู้แจ้งต้องอยู่ระหว่าง 0-150 ปี")
            except:
                row_errors.append("อายุผู้แจ้งต้องเป็นตัวเลข")

        # ตรวจสอบเลขบัตรประชาชน
        if pd.notna(row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต")):
            id_number = str(row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต")).strip()
            if id_number and not id_number.isdigit():
                row_errors.append("หมายเลขบัตรประชาชนคนหาย/เสียชีวิตต้องเป็นตัวเลขเท่านั้น")
            elif id_number and len(id_number) != 13:
                row_errors.append("หมายเลขบัตรประชาชนคนหาย/เสียชีวิตต้องมี 13 หลัก")

        if pd.notna(row.get("หมายเลขบัตรประชาชนผู้แจ้ง")):
            id_number = str(row.get("หมายเลขบัตรประชาชนผู้แจ้ง")).strip()
            if id_number and not id_number.isdigit():
                row_errors.append("หมายเลขบัตรประชาชนผู้แจ้งต้องเป็นตัวเลขเท่านั้น")
            elif id_number and len(id_number) != 13:
                row_errors.append("หมายเลขบัตรประชาชนผู้แจ้งต้องมี 13 หลัก")

        # ตรวจสอบเบอร์โทร
        if pd.notna(row.get("เบอร์โทรศัพท์ผู้แจ้ง")):
            phone = re.sub(r"\D", "", str(row.get("เบอร์โทรศัพท์ผู้แจ้ง")))
            if phone and len(phone) not in [9, 10]:
                row_errors.append("เบอร์โทรศัพท์ผู้แจ้งต้องมี 9-10 หลัก")

        # ตรวจสอบวันที่รับศพ (ถ้ามี)
        if pd.notna(row.get("วันที่รับศพ")):
            if not isinstance(row.get("วันที่รับศพ"), datetime.datetime):
                date_str = str(row.get("วันที่รับศพ")).strip()
                if date_str:
                    try:
                        pd.to_datetime(date_str, format="%d/%m/%Y", dayfirst=True)
                    except:
                        row_errors.append("รูปแบบวันที่รับศพไม่ถูกต้อง ต้องเป็น DD/MM/YYYY")

        if row_errors:
            errors.append(f"[{sheet_name}] แถวที่ {index + 2}: {', '.join(row_errors)}")

    return errors


def write_missing_persons_from_import_file(file, current_user):
    """Write missing persons from import file - support multiple sheets"""

    if file.filename.endswith(".xlsx"):
        excel_file = pd.ExcelFile(file)
        sheet_names = excel_file.sheet_names
        valid_sheets = [s for s in sheet_names if not s.startswith("Choices_")]
    else:
        valid_sheets = ["CSV"]

    total_record_count = 0
    total_updated_count = 0

    # Loop through each sheet
    for sheet_name in valid_sheets:
        if file.filename.endswith(".xlsx"):
            file.seek(0)
            df = pd.read_excel(file, sheet_name=sheet_name)
        else:
            file.seek(0)
            df = pd.read_csv(file)

        record_count, updated_count = process_missing_person_dataframe(
            df, current_user, sheet_name
        )
        total_record_count += record_count
        total_updated_count += updated_count

    print(
        f"Import summary: {total_record_count} new records, {total_updated_count} updated records"
    )
    return total_record_count + total_updated_count


def process_missing_person_dataframe(df, current_user, sheet_name):
    """Process single dataframe/sheet"""
    record_count = 0
    updated_count = 0

    for index, row in df.iterrows():
        try:
            # แปลงสถานะจากภาษาไทยเป็น key
            status = "missing"  # default
            if pd.notna(row.get("สถานะ")):
                status_str = str(row.get("สถานะ")).strip().lower()
                for key, value in MISSING_PERSON_STATUS_CHOICES:
                    if value.lower() == status_str or key.lower() == status_str:
                        status = key
                        break

            # แปลงวันที่รับศพ
            body_received_date = None
            if pd.notna(row.get("วันที่รับศพ")):
                try:
                    if isinstance(row.get("วันที่รับศพ"), datetime.datetime):
                        body_received_date = row.get("วันที่รับศพ")
                    else:
                        date_str = str(row.get("วันที่รับศพ")).strip()
                        if date_str:
                            body_received_date = pd.to_datetime(
                                date_str, format="%d/%m/%Y", dayfirst=True
                            )
                except:
                    body_received_date = None

            # แปลงอายุ
            missing_age = None
            if pd.notna(row.get("อายุคนหาย/เสียชีวิต")):
                try:
                    missing_age = int(float(row.get("อายุคนหาย/เสียชีวิต")))
                except:
                    missing_age = None

            reporter_age = None
            if pd.notna(row.get("อายุผู้แจ้ง")):
                try:
                    reporter_age = int(float(row.get("อายุผู้แจ้ง")))
                except:
                    reporter_age = None

            # แปลงเบอร์โทร
            reporter_phone = ""
            if pd.notna(row.get("เบอร์โทรศัพท์ผู้แจ้ง")):
                phone_raw = str(row.get("เบอร์โทรศัพท์ผู้แจ้ง")).strip()
                reporter_phone = re.sub(r"\D", "", phone_raw)
                if not reporter_phone.startswith("0") and len(reporter_phone) == 9:
                    reporter_phone = "0" + reporter_phone

            # ข้อมูลคนหาย/เสียชีวิต
            missing_first_name = format_str(row.get("ชื่อคนหาย/เสียชีวิต"))
            missing_last_name = format_str(row.get("นามสกุลคนหาย/เสียชีวิต"))
            missing_id_number = format_str(row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต"))

            # ตรวจสอบว่ามีข้อมูลซ้ำหรือไม่
            existing_person = check_existing_missing_person(
                first_name=missing_first_name,
                last_name=missing_last_name,
                identification_number=missing_id_number if missing_id_number else None,
            )

            if existing_person:
                # Update ข้อมูลเดิม
                existing_person.title_name = format_str(
                    row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")
                )
                existing_person.first_name = missing_first_name
                existing_person.last_name = missing_last_name
                existing_person.age = missing_age
                existing_person.identification_number = missing_id_number
                existing_person.country = format_str(row.get("ประเทศคนหาย/เสียชีวิต"))
                existing_person.province_info = format_str(row.get("จังหวัดคนหาย/เสียชีวิต"))
                existing_person.district_info = format_str(row.get("อำเภอคนหาย/เสียชีวิต"))
                existing_person.subdistrict_info = format_str(
                    row.get("ตำบลคนหาย/เสียชีวิต")
                )
                existing_person.address_info = format_str(
                    row.get("ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต")
                )
                existing_person.missing_person_status = status
                existing_person.physical_mark = format_str(row.get("ลักษณะรูปพรรณ"))
                existing_person.statement = format_str(row.get("คำให้การ/สอบปากคำ"))
                existing_person.body_received_date = body_received_date

                # ข้อมูลผู้แจ้ง
                existing_person.deceased_relationship = format_str(
                    row.get("ความสัมพันธ์กับผู้หาย/เสียชีวิต")
                )
                existing_person.reporter_title_name = format_str(
                    row.get("คำนำหน้าชื่อผู้แจ้ง")
                )
                existing_person.reporter_first_name = format_str(row.get("ชื่อผู้แจ้ง"))
                existing_person.reporter_last_name = format_str(row.get("นามสกุลผู้แจ้ง"))
                existing_person.reporter_age = reporter_age
                existing_person.reporter_identification_number = format_str(
                    row.get("หมายเลขบัตรประชาชนผู้แจ้ง")
                )
                existing_person.reporter_country = format_str(row.get("ประเทศผู้แจ้ง"))
                existing_person.reporter_province_info = format_str(
                    row.get("จังหวัดผู้แจ้ง")
                )
                existing_person.reporter_district_info = format_str(
                    row.get("อำเภอผู้แจ้ง")
                )
                existing_person.reporter_subdistrict_info = format_str(
                    row.get("ตำบลผู้แจ้ง")
                )
                existing_person.reporter_address_info = format_str(
                    row.get("ที่อยู่บ้านเลขที่ผู้แจ้ง")
                )
                existing_person.reporter_phone_number = reporter_phone
                existing_person.code = format_str(row.get("CODE"))

                existing_person.updated_by = current_user
                existing_person.updated_date = datetime.datetime.now()
                existing_person.save()
                updated_count += 1

            else:
                # สร้างใหม่
                missing_person = models.MissingPerson(
                    # ข้อมูลคนหาย/เสียชีวิต
                    title_name=format_str(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")),
                    first_name=missing_first_name,
                    last_name=missing_last_name,
                    age=missing_age,
                    identification_number=missing_id_number,
                    country=format_str(row.get("ประเทศคนหาย/เสียชีวิต")) or "Thailand",
                    province_info=format_str(row.get("จังหวัดคนหาย/เสียชีวิต")),
                    district_info=format_str(row.get("อำเภอคนหาย/เสียชีวิต")),
                    subdistrict_info=format_str(row.get("ตำบลคนหาย/เสียชีวิต")),
                    address_info=format_str(row.get("ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต")),
                    missing_person_status=status,
                    # ข้อมูลเพิ่มเติม
                    physical_mark=format_str(row.get("ลักษณะรูปพรรณ")),
                    statement=format_str(row.get("คำให้การ/สอบปากคำ")),
                    body_received_date=body_received_date,
                    deceased_relationship=format_str(row.get("ความสัมพันธ์กับผู้หาย/เสียชีวิต")),
                    # ข้อมูลผู้แจ้ง
                    reporter_title_name=format_str(row.get("คำนำหน้าชื่อผู้แจ้ง")),
                    reporter_first_name=format_str(row.get("ชื่อผู้แจ้ง")),
                    reporter_last_name=format_str(row.get("นามสกุลผู้แจ้ง")),
                    reporter_age=reporter_age,
                    reporter_identification_number=format_str(
                        row.get("หมายเลขบัตรประชาชนผู้แจ้ง")
                    ),
                    reporter_country=format_str(row.get("ประเทศผู้แจ้ง")) or "Thailand",
                    reporter_province_info=format_str(row.get("จังหวัดผู้แจ้ง")),
                    reporter_district_info=format_str(row.get("อำเภอผู้แจ้ง")),
                    reporter_subdistrict_info=format_str(row.get("ตำบลผู้แจ้ง")),
                    reporter_address_info=format_str(row.get("ที่อยู่บ้านเลขที่ผู้แจ้ง")),
                    reporter_phone_number=reporter_phone,
                    code=format_str(row.get("CODE")),
                    metadata={
                        "imported_from_excel_file": True,
                        "sheet_name": sheet_name,
                    },
                    status="active",
                    created_by=current_user,
                    created_date=datetime.datetime.now(),
                    updated_by=current_user,
                    updated_date=datetime.datetime.now(),
                )

                missing_person.save()
                record_count += 1

        except Exception as e:
            print(f"[{sheet_name}] Error processing row {index + 2}: {e}")

    return record_count, updated_count


def check_existing_missing_person(first_name, last_name, identification_number=None):
    """Check if missing person already exists"""
    query = models.MissingPerson.objects(
        first_name=first_name,
        last_name=last_name,
    )

    # ถ้ามีเลขบัตรประชาชน ให้เช็คด้วย
    if identification_number:
        query = query.filter(identification_number=identification_number)

    return query.first()


def format_str(value):
    """Convert NaN to empty string"""
    return str(value).strip() if pd.notna(value) else ""


def process_import_missing_person_file(import_missing_person_file, current_user):
    """Main process function"""
    file = import_missing_person_file.file

    # Validation
    results = validate_import_file(file, import_missing_person_file)
    if not results:
        import_missing_person_file.file.delete()
        import_missing_person_file.file = None
        import_missing_person_file.upload_status = "failed"
        import_missing_person_file.save()
        return

    file.seek(0)
    import_missing_person_file.upload_status = "processing"
    import_missing_person_file.save()

    try:
        record_count = write_missing_persons_from_import_file(
            file=file,
            current_user=current_user,
        )

        import_missing_person_file.upload_status = "completed"
        import_missing_person_file.record_count = record_count
        import_missing_person_file.save()

    except Exception as e:
        import_missing_person_file.upload_status = "failed"
        import_missing_person_file.error_messages.append(f"เกิดข้อผิดพลาด: {str(e)}")
        import_missing_person_file.save()
