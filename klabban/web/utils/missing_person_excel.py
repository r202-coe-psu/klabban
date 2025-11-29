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
from klabban.models.missing_persons import (
    MISSING_PERSON_STATUS_CHOICES,
    TITLE_NAME_CHOICES,
)


REQUIRE_HEADERS = [
    "ชื่อคนหาย/เสียชีวิต",
    "ชื่อผู้แจ้ง",
]

HEADER = [
    # ข้อมูลคนหาย/เสียชีวิต
    "วันที่มาเเจ้งเหตุ",
    "คำนำหน้าชื่อคนหาย/เสียชีวิต",
    "ชื่อคนหาย/เสียชีวิต",
    "นามสกุลคนหาย/เสียชีวิต",
    "อายุคนหาย/เสียชีวิต",
    "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
    "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
    "ประเทศคนหาย/เสียชีวิต",
    "จังหวัดคนหาย/เสียชีวิต",
    "อำเภอคนหาย/เสียชีวิต",
    "ตำบลคนหาย/เสียชีวิต",
    "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต",
    # ข้อมูลเพิ่มเติม
    "ลักษณะรูปพรรณ",
    "เก็บดีเอ็นเอญาติ" "คำให้การ/สอบปากคำ",
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


def get_template():
    # ข้อมูลตัวอย่าง Sheet 1: ข้อมูลผู้สูญหาย
    missing_data = {
        "วันที่มาเเจ้งเหตุ": ["15/11/2025", "16/11/2025"],
        "คำนำหน้าชื่อคนหาย/เสียชีวิต": ["นาย", "นางสาว"],
        "ชื่อคนหาย/เสียชีวิต": ["สมชาย", "สมหญิง"],
        "นามสกุลคนหาย/เสียชีวิต": ["ใจดี", "ดีใจ"],
        "อายุคนหาย/เสียชีวิต": [30, 25],
        "เบอร์โทรศัพท์คนหาย/เสียชีวิต": ["0812345678", "0823456789"],
        "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต": ["1234567890123", "9876543210987"],
        "ประเทศคนหาย/เสียชีวิต": ["ไทย", "ไทย"],
        "จังหวัดคนหาย/เสียชีวิต": ["กรุงเทพมหานคร", "กรุงเทพมหานคร"],
        "อำเภอคนหาย/เสียชีวิต": ["บางรัก", "บางรัก"],
        "ตำบลคนหาย/เสียชีวิต": ["สี่พระยา", "สี่พระยา"],
        "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต": ["123/45 ถนนสุขุมวิท", "678/90 ถนนสุขุมวิท"],
        "ลักษณะรูปพรรณ": ["สูง 170 ซม. ผิวขาว", "สูง 160 ซม. ผิวขาว"],
        "เก็บดีเอ็นเอญาติ": ["เก็บเเล้ว", ""],
        "คำให้การ/สอบปากคำ": ["ออกไปทำงานแล้วหลับมาไม่พบ", "ออกไปซื้อของแล้วหายไป"],
        "วันที่รับศพ": ["", ""],
        "ความสัมพันธ์กับผู้หาย/เสียชีวิต": ["พ่อ", "แม่"],
        "คำนำหน้าชื่อผู้แจ้ง": ["นางสาว", "นาง"],
        "ชื่อผู้แจ้ง": ["สมหญิง", "ดีใจ"],
        "นามสกุลผู้แจ้ง": ["ดีใจ", "ใจดี"],
        "อายุผู้แจ้ง": [28, 32],
        "หมายเลขบัตรประชาชนผู้แจ้ง": ["9876543210987", "1234567890123"],
        "ประเทศผู้แจ้ง": ["ไทย", "ไทย"],
        "จังหวัดผู้แจ้ง": ["กรุงเทพมหานคร", "กรุงเทพมหานคร"],
        "อำเภอผู้แจ้ง": ["บางรัก", "บางรัก"],
        "ตำบลผู้แจ้ง": ["สี่พระยา", "สี่พระยา"],
        "ที่อยู่บ้านเลขที่ผู้แจ้ง": ["678/90 ถนนสุขุมวิท", "123/45 ถนนสุขุมวิท"],
        "เบอร์โทรศัพท์ผู้แจ้ง": ["0812345678", "0823456789"],
        "CODE": ["HY74/68 PSU", "HY75/69 PSU"],
    }

    # ข้อมูลตัวอย่าง Sheet 2: ข้อมูลผู้เสียชีวิต
    death_data = {
        "วันที่มาเเจ้งเหตุ": ["15/11/2025", "16/11/2025"],
        "คำนำหน้าชื่อคนหาย/เสียชีวิต": ["นาง", "เด็กชาย"],
        "ชื่อคนหาย/เสียชีวิต": ["สมหมาย", "สมบัติ"],
        "นามสกุลคนหาย/เสียชีวิต": ["รักดี", "ดีรัก"],
        "อายุคนหาย/เสียชีวิต": [65, 10],
        "เบอร์โทรศัพท์คนหาย/เสียชีวิต": ["0812345678", "0823456789"],
        "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต": ["3210987654321", "2109876543210"],
        "ประเทศคนหาย/เสียชีวิต": ["ไทย", "ไทย"],
        "จังหวัดคนหาย/เสียชีวิต": ["เชียงใหม่", "เชียงใหม่"],
        "อำเภอคนหาย/เสียชีวิต": ["เมือง", "เมือง"],
        "ตำบลคนหาย/เสียชีวิต": ["ช้างเผือก", "ช้างเผือก"],
        "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต": ["456/78 ถนนห้วยแก้ว", "789/12 ถนนห้วยแก้ว"],
        "ลักษณะรูปพรรณ": ["สูง 155 ซม. ผิวคล้ำ", "สูง 140 ซม. ผิวขาว"],
        "เก็บดีเอ็นเอญาติ": ["เก็บเเล้ว", ""],
        "คำให้การ/สอบปากคำ": ["พบศพบริเวณริมแม่น้ำ", "ประสบอุบัติเหตุทางรถยนต์"],
        "วันที่รับศพ": ["15/11/2025", "16/11/2025"],
        "ความสัมพันธ์กับผู้หาย/เสียชีวิต": ["ลูกชาย", "ลูกชาย"],
        "คำนำหน้าชื่อผู้แจ้ง": ["นาย", "นาง"],
        "ชื่อผู้แจ้ง": ["สมพร", "ดีพร"],
        "นามสกุลผู้แจ้ง": ["รักดี", "ดีรัก"],
        "อายุผู้แจ้ง": [40, 38],
        "หมายเลขบัตรประชาชนผู้แจ้ง": ["5432109876543", "6543210987654"],
        "ประเทศผู้แจ้ง": ["ไทย", "ไทย"],
        "จังหวัดผู้แจ้ง": ["เชียงใหม่", "เชียงใหม่"],
        "อำเภอผู้แจ้ง": ["เมือง", "เมือง"],
        "ตำบลผู้แจ้ง": ["ช้างเผือก", "ช้างเผือก"],
        "ที่อยู่บ้านเลขที่ผู้แจ้ง": ["456/78 ถนนห้วยแก้ว", "789/12 ถนนห้วยแก้ว"],
        "เบอร์โทรศัพท์ผู้แจ้ง": ["0898765432", "0887654321"],
        "CODE": ["CM01/25", "CM02/25"],
    }

    df_missing = pd.DataFrame(missing_data)
    df_death = pd.DataFrame(death_data)

    # ========== กำหนด dtype ให้แต่ละคอลัมน์ ==========

    # คอลัมน์ที่เป็น string/text
    text_columns = [
        "คำนำหน้าชื่อคนหาย/เสียชีวิต",
        "ชื่อคนหาย/เสียชีวิต",
        "นามสกุลคนหาย/เสียชีวิต",
        "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
        "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
        "ประเทศคนหาย/เสียชีวิต",
        "จังหวัดคนหาย/เสียชีวิต",
        "อำเภอคนหาย/เสียชีวิต",
        "ตำบลคนหาย/เสียชีวิต",
        "ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต",
        "ลักษณะรูปพรรณ",
        "เก็บดีเอ็นเอญาติ",
        "คำให้การ/สอบปากคำ",
        "วันที่รับศพ",
        "ความสัมพันธ์กับผู้หาย/เสียชีวิต",
        "คำนำหน้าชื่อผู้แจ้ง",
        "ชื่อผู้แจ้ง",
        "นามสกุลผู้แจ้ง",
        "หมายเลขบัตรประชาชนผู้แจ้ง",
        "ประเทศผู้แจ้ง",
        "จังหวัดผู้แจ้ง",
        "อำเภอผู้แจ้ง",
        "ตำบลผู้แจ้ง",
        "ที่อยู่บ้านเลขที่ผู้แจ้ง",
        "เบอร์โทรศัพท์ผู้แจ้ง",
        "CODE",
        "วันที่มาเเจ้งเหตุ",
    ]

    # คอลัมน์ที่เป็นตัวเลข
    numeric_columns = [
        "อายุคนหาย/เสียชีวิต",
        "อายุผู้แจ้ง",
    ]

    # แปลง dtype สำหรับ Sheet ผู้สูญหาย
    for col in text_columns:
        if col in df_missing.columns:
            df_missing[col] = df_missing[col].astype(str)

    for col in numeric_columns:
        if col in df_missing.columns:
            df_missing[col] = df_missing[col].astype("Int64")  # nullable integer

    # แปลง dtype สำหรับ Sheet ผู้เสียชีวิต
    for col in text_columns:
        if col in df_death.columns:
            df_death[col] = df_death[col].astype(str)

    for col in numeric_columns:
        if col in df_death.columns:
            df_death[col] = df_death[col].astype("Int64")

    output = BytesIO()
    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        date_format="dd/mm/yyyy",
        datetime_format="dd/mm/yyyy",
    ) as writer:

        # เขียน Sheet 1: ผู้สูญหาย
        df_missing.to_excel(writer, sheet_name="ผู้สูญหาย", index=False)

        # เขียน Sheet 2: ผู้เสียชีวิต
        df_death.to_excel(writer, sheet_name="ผู้เสียชีวิต", index=False)

        workbook: xlsxwriter.Workbook = writer.book

        # Format สำหรับ header
        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1}
        )

        # Format สำหรับ text (text alignment)
        text_format = workbook.add_format({"num_format": "@"})  # @ = text format

        # Format สำหรับตัวเลข
        number_format = workbook.add_format({"num_format": "0"})

        # สร้าง Choices sheet
        sheet_choices = "Choices_ตัวเลือกห้ามลบ"
        list_sheet = workbook.add_worksheet(sheet_choices)
        list_sheet.hide()

        # Validation choices
        title_choices = [choice[1] for choice in TITLE_NAME_CHOICES if choice[1] != "-"]
        dna_choices = ["เก็บเแล้ว"]

        validations = {
            "คำนำหน้าชื่อคนหาย/เสียชีวิต": title_choices,
            "คำนำหน้าชื่อผู้แจ้ง": title_choices,
            "เก็บดีเอ็นเอญาติ": dna_choices,
        }

        list_row = 0

        # ========== จัด Format และ Validation สำหรับ Sheet 1: ผู้สูญหาย ==========
        worksheet_missing = writer.sheets["ผู้สูญหาย"]

        # Header format
        for col_num, value in enumerate(df_missing.columns.values):
            worksheet_missing.write(0, col_num, value, header_format)

        # เขียนข้อมูลพร้อม format
        for row_num in range(len(df_missing)):
            for col_num, col_name in enumerate(df_missing.columns):
                value = df_missing.iloc[row_num, col_num]

                # เลือก format ตามประเภทคอลัมน์
                if col_name in numeric_columns:
                    worksheet_missing.write(row_num + 1, col_num, value, number_format)
                elif col_name in [
                    "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
                    "หมายเลขบัตรประชาชนผู้แจ้ง",
                    "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
                    "เบอร์โทรศัพท์ผู้แจ้ง",
                ]:
                    # บังคับให้เป็น text สำหรับเลขบัตรประชาชนและเบอร์โทร
                    worksheet_missing.write_string(
                        row_num + 1, col_num, str(value), text_format
                    )
                else:
                    worksheet_missing.write(row_num + 1, col_num, value)

        # Data validation
        first_row, last_row = 2, 10000

        for column_name, source in validations.items():
            if column_name not in df_missing.columns:
                continue

            col_idx = df_missing.columns.get_loc(column_name)

            start_row = list_row
            for val in source:
                list_sheet.write(list_row, 0, val)
                list_row += 1
            end_row = list_row - 1

            rng = f"={sheet_choices}!$A${start_row+1}:$A${end_row+1}"
            worksheet_missing.data_validation(
                first_row=first_row,
                first_col=col_idx,
                last_row=last_row,
                last_col=col_idx,
                options={"validate": "list", "source": rng},
            )

        # ปรับความกว้างคอลัมน์และกำหนด format
        for i, col in enumerate(df_missing.columns):
            max_len = max(df_missing[col].astype(str).apply(len).max(), len(col)) + 2

            # กำหนด format สำหรับ column ทั้งคอลัมน์
            if col in [
                "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
                "หมายเลขบัตรประชาชนผู้แจ้ง",
                "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
                "เบอร์โทรศัพท์ผู้แจ้ง",
            ]:
                worksheet_missing.set_column(i, i, max_len, text_format)
            elif col in numeric_columns:
                worksheet_missing.set_column(i, i, max_len, number_format)
            else:
                worksheet_missing.set_column(i, i, max_len)

        # ========== จัด Format และ Validation สำหรับ Sheet 2: ผู้เสียชีวิต ==========
        worksheet_death = writer.sheets["ผู้เสียชีวิต"]

        # Header format
        for col_num, value in enumerate(df_death.columns.values):
            worksheet_death.write(0, col_num, value, header_format)

        # เขียนข้อมูลพร้อม format
        for row_num in range(len(df_death)):
            for col_num, col_name in enumerate(df_death.columns):
                value = df_death.iloc[row_num, col_num]

                if col_name in numeric_columns:
                    worksheet_death.write(row_num + 1, col_num, value, number_format)
                elif col_name in [
                    "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
                    "หมายเลขบัตรประชาชนผู้แจ้ง",
                    "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
                    "เบอร์โทรศัพท์ผู้แจ้ง",
                ]:
                    worksheet_death.write_string(
                        row_num + 1, col_num, str(value), text_format
                    )
                else:
                    worksheet_death.write(row_num + 1, col_num, value)

        # Data validation
        for column_name, source in validations.items():
            if column_name not in df_death.columns:
                continue

            col_idx = df_death.columns.get_loc(column_name)

            start_idx = 0
            for i, (key, _) in enumerate(validations.items()):
                if key == column_name:
                    break
                start_idx += len(validations[list(validations.keys())[i]])

            end_idx = start_idx + len(source) - 1

            rng = f"={sheet_choices}!$A${start_idx+1}:$A${end_idx+1}"
            worksheet_death.data_validation(
                first_row=first_row,
                first_col=col_idx,
                last_row=last_row,
                last_col=col_idx,
                options={"validate": "list", "source": rng},
            )

        # ปรับความกว้างคอลัมน์และกำหนด format
        for i, col in enumerate(df_death.columns):
            max_len = max(df_death[col].astype(str).apply(len).max(), len(col)) + 2

            if col in [
                "หมายเลขบัตรประชาชนคนหาย/เสียชีวิต",
                "หมายเลขบัตรประชาชนผู้แจ้ง",
                "เบอร์โทรศัพท์คนหาย/เสียชีวิต",
                "เบอร์โทรศัพท์ผู้แจ้ง",
            ]:
                worksheet_death.set_column(i, i, max_len, text_format)
            elif col in numeric_columns:
                worksheet_death.set_column(i, i, max_len, number_format)
            else:
                worksheet_death.set_column(i, i, max_len)

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
    errors = []

    # กำหนดประเภท sheet จากชื่อ
    sheet_type = detect_sheet_type(sheet_name)

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

        if pd.isna(row.get("ชื่อผู้แจ้ง")) or str(row.get("ชื่อผู้แจ้ง")).strip() == "":
            row_errors.append("ขาดชื่อผู้แจ้ง")

        # ตรวจสอบคำนำหน้าชื่อ
        if pd.notna(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")):
            title = str(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")).strip()
            if title:
                valid_titles = [choice[0] for choice in TITLE_NAME_CHOICES if choice[0]]
                valid_titles_thai = [
                    choice[1] for choice in TITLE_NAME_CHOICES if choice[1] != "-"
                ]

                if title not in valid_titles and title not in valid_titles_thai:
                    row_errors.append(
                        f"คำนำหน้าชื่อคนหาย/เสียชีวิตไม่ถูกต้อง ต้องเป็น: {', '.join(valid_titles_thai)}"
                    )

        if pd.notna(row.get("คำนำหน้าชื่อผู้แจ้ง")):
            title = str(row.get("คำนำหน้าชื่อผู้แจ้ง")).strip()
            if title:
                valid_titles = [choice[0] for choice in TITLE_NAME_CHOICES if choice[0]]
                valid_titles_thai = [
                    choice[1] for choice in TITLE_NAME_CHOICES if choice[1] != "-"
                ]

                if title not in valid_titles and title not in valid_titles_thai:
                    row_errors.append(
                        f"คำนำหน้าชื่อผู้แจ้งไม่ถูกต้อง ต้องเป็น: {', '.join(valid_titles_thai)}"
                    )

        # ตรวจสอบเฉพาะ sheet ผู้เสียชีวิต - ต้องมีวันที่รับศพ
        if pd.notna(row.get("วันที่รับศพ")) and sheet_type == "death":
            date_str = str(row.get("วันที่รับศพ")).strip()
            try:
                datetime.datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                row_errors.append("วันที่รับศพไม่ถูกต้อง ต้องอยู่ในรูปแบบ วัน/เดือน/ปี (dd/mm/yyyy)")

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
        # if pd.notna(row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต")):
        #     id_number = (
        #         str(row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต")).strip().split(".")[0]
        #     )
        #     if id_number and not id_number.isdigit():
        #         row_errors.append("หมายเลขบัตรประชาชนคนหาย/เสียชีวิตต้องเป็นตัวเลขเท่านั้น")
        #     elif id_number and len(id_number) != 13:
        #         row_errors.append("หมายเลขบัตรประชาชนคนหาย/เสียชีวิตต้องมี 13 หลัก")

        # if pd.notna(row.get("หมายเลขบัตรประชาชนผู้แจ้ง")):
        #     id_number = str(row.get("หมายเลขบัตรประชาชนผู้แจ้ง")).strip().split(".")[0]

        #     if id_number and not id_number.isdigit():
        #         row_errors.append("หมายเลขบัตรประชาชนผู้แจ้งต้องเป็นตัวเลขเท่านั้น")
        #     elif id_number and len(id_number) != 13:
        #         row_errors.append("หมายเลขบัตรประชาชนผู้แจ้งต้องมี 13 หลัก")

        # # ตรวจสอบเบอร์โทร
        # if pd.notna(row.get("เบอร์โทรศัพท์คนหาย/เสียชีวิต")):
        #     phone = re.sub(r"\D", "", str(row.get("เบอร์โทรศัพท์คนหาย/เสียชีวิต")))
        #     if phone and len(phone) not in [9, 10]:
        #         row_errors.append("เบอร์โทรศัพท์คนหาย/เสียชีวิตต้องมี 9-10 หลัก")

        # if pd.notna(row.get("เบอร์โทรศัพท์ผู้แจ้ง")):
        #     phone = re.sub(r"\D", "", str(row.get("เบอร์โทรศัพท์ผู้แจ้ง")))
        #     if phone and len(phone) not in [9, 10]:
        #         row_errors.append("เบอร์โทรศัพท์ผู้แจ้งต้องมี 9-10 หลัก")

        if row_errors:
            errors.append(f"[{sheet_name}] แถวที่ {index + 2}: {', '.join(row_errors)}")

    return errors


def detect_sheet_type(sheet_name):
    """
    ตรวจสอบประเภทของ sheet จากชื่อ
    Returns: 'death', 'missing'
    """
    sheet_name_lower = sheet_name.lower()

    # คำที่บ่งบอกว่าเป็นผู้เสียชีวิต
    death_keywords = ["เสียชีวิต", "ตาย", "death", "deceased", "died"]

    # คำที่บ่งบอกว่าเป็นผู้สูญหาย
    missing_keywords = ["สูญหาย", "หาย", "missing", "lost"]

    # เช็คว่าชื่อ sheet มีคำใดบ้าง
    for keyword in death_keywords:
        if keyword in sheet_name_lower:
            return "death"

    for keyword in missing_keywords:
        if keyword in sheet_name_lower:
            return "missing"

    # ถ้าไม่มีคำใดเลย ให้ถือว่าเป็นสูญหาย (default)
    return "missing"


def write_missing_persons_from_import_file(file, current_user, source):

    if file.filename.endswith(".xlsx"):
        excel_file = pd.ExcelFile(file)
        sheet_names = excel_file.sheet_names
        print(sheet_names)

        valid_sheets = ["ผู้สูญหาย", "ผู้เสียชีวิต"]
    else:
        valid_sheets = ["CSV"]

    total_record_count = 0
    total_updated_count = 0

    # เก็บสถิติแยกตามประเภท
    stats = {"missing": {"new": 0, "updated": 0}, "death": {"new": 0, "updated": 0}}

    # Loop through each sheet
    for sheet_name in valid_sheets:
        if file.filename.endswith(".xlsx"):
            file.seek(0)
            df = pd.read_excel(file, sheet_name=sheet_name)
        else:
            file.seek(0)
            df = pd.read_csv(file)

        # ตรวจสอบประเภทของ sheet
        sheet_type = detect_sheet_type(sheet_name)

        record_count, updated_count = process_missing_person_dataframe(
            df, current_user, sheet_name, source, sheet_type
        )

        # รวมสถิติ
        stats[sheet_type]["new"] += record_count
        stats[sheet_type]["updated"] += updated_count

        total_record_count += record_count
        total_updated_count += updated_count

    return total_record_count + total_updated_count


def process_missing_person_dataframe(df, current_user, sheet_name, source, sheet_type):
    record_count = 0
    updated_count = 0

    for index, row in df.iterrows():
        try:
            reporting_date = None
            if pd.notna(row.get("วันที่มาเเจ้งเหตุ")):
                if isinstance(row.get("วันที่มาเเจ้งเหตุ"), datetime.datetime):
                    reporting_date = row.get("วันที่มาเเจ้งเหตุ")
                else:
                    date_str = str(row.get("วันที่มาเเจ้งเหตุ")).strip()
                    if date_str and date_str.lower() not in ["nan", "none", ""]:
                        reporting_date = pd.to_datetime(
                            date_str, format="%d/%m/%Y", dayfirst=True
                        )
            # แปลงคำนำหน้าชื่อจากภาษาไทยเป็น key
            title_name = ""
            if pd.notna(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")):
                title_str = str(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")).strip()
                for key, value in TITLE_NAME_CHOICES:
                    if (
                        value.lower() == title_str.lower()
                        or key.lower() == title_str.lower()
                    ):
                        title_name = key
                        break

            # แปลงคำนำหน้าชื่อผู้แจ้งจากภาษาไทยเป็น key
            reporter_title_name = ""
            if pd.notna(row.get("คำนำหน้าชื่อผู้แจ้ง")):
                title_str = str(row.get("คำนำหน้าชื่อผู้แจ้ง")).strip()
                for key, value in TITLE_NAME_CHOICES:
                    if (
                        value.lower() == title_str.lower()
                        or key.lower() == title_str.lower()
                    ):
                        reporter_title_name = key
                        break

            # กำหนดสถานะตาม sheet type
            # ถ้า sheet เป็นผู้เสียชีวิต ให้เป็น 'death' เสมอ
            # ถ้า sheet เป็นผู้สูญหาย ให้เป็น 'missing' เสมอ
            status = sheet_type

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
            phone_number = ""
            if pd.notna(row.get("เบอร์โทรศัพท์คนหาย/เสียชีวิต")):
                phone_raw = str(row.get("เบอร์โทรศัพท์คนหาย/เสียชีวิต")).strip()
                phone_number = re.sub(r"\D", "", phone_raw)
                if not phone_number.startswith("0") and len(phone_number) == 9:
                    phone_number = "0" + phone_number

            reporter_phone = ""
            if pd.notna(row.get("เบอร์โทรศัพท์ผู้แจ้ง")):
                phone_raw = str(row.get("เบอร์โทรศัพท์ผู้แจ้ง")).strip()
                reporter_phone = re.sub(r"\D", "", phone_raw)
                if not reporter_phone.startswith("0") and len(reporter_phone) == 9:
                    reporter_phone = "0" + reporter_phone

            is_dna_collected = False
            if pd.notna(row.get("เก็บดีเอ็นเอญาติ")):
                dna_str = str(row.get("เก็บดีเอ็นเอญาติ")).strip()
                if dna_str == "เก็บเเล้ว":
                    is_dna_collected = True

            # ข้อมูลคนหาย/เสียชีวิต
            missing_first_name = format_str(row.get("ชื่อคนหาย/เสียชีวิต"))
            missing_last_name = format_str(row.get("นามสกุลคนหาย/เสียชีวิต"))
            missing_id_number = format_str(
                row.get("หมายเลขบัตรประชาชนคนหาย/เสียชีวิต")
            ).split(".")[0]

            # สร้าง metadata จากข้อมูลใน Excel
            excel_metadata = {
                "imported_from_excel_file": True,
                "sheet_name": sheet_name,
                "sheet_type": sheet_type,  # เพิ่มประเภท sheet
                "import_date": datetime.datetime.now().isoformat(),
                "row_number": index + 2,
                "original_data": {
                    # ข้อมูลคนหาย/เสียชีวิต
                    "missing_person": {
                        "reporting_date": (
                            reporting_date.isoformat() if reporting_date else None
                        ),
                        "title_name": format_str(row.get("คำนำหน้าชื่อคนหาย/เสียชีวิต")),
                        "first_name": missing_first_name,
                        "last_name": missing_last_name,
                        "age": missing_age,
                        "phone_number": phone_number,
                        "identification_number": missing_id_number,
                        "country": format_str(row.get("ประเทศคนหาย/เสียชีวิต")),
                        "province": format_str(row.get("จังหวัดคนหาย/เสียชีวิต")),
                        "district": format_str(row.get("อำเภอคนหาย/เสียชีวิต")),
                        "subdistrict": format_str(row.get("ตำบลคนหาย/เสียชีวิต")),
                        "address": format_str(row.get("ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต")),
                        "status": sheet_type,  # ใช้ status จาก sheet type
                    },
                    # ข้อมูลเพิ่มเติม
                    "additional_info": {
                        "physical_mark": format_str(row.get("ลักษณะรูปพรรณ")),
                        "is_dna_collected": is_dna_collected,
                        "statement": format_str(row.get("คำให้การ/สอบปากคำ")),
                        "body_received_date": format_str(row.get("วันที่รับศพ")),
                        "relationship": format_str(row.get("ความสัมพันธ์กับผู้หาย/เสียชีวิต")),
                    },
                    # ข้อมูลผู้แจ้ง
                    "reporter": {
                        "title_name": format_str(row.get("คำนำหน้าชื่อผู้แจ้ง")),
                        "first_name": format_str(row.get("ชื่อผู้แจ้ง")),
                        "last_name": format_str(row.get("นามสกุลผู้แจ้ง")),
                        "age": reporter_age,
                        "identification_number": format_str(
                            row.get("หมายเลขบัตรประชาชนผู้แจ้ง")
                        ),
                        "country": format_str(row.get("ประเทศผู้แจ้ง")),
                        "province": format_str(row.get("จังหวัดผู้แจ้ง")),
                        "district": format_str(row.get("อำเภอผู้แจ้ง")),
                        "subdistrict": format_str(row.get("ตำบลผู้แจ้ง")),
                        "address": format_str(row.get("ที่อยู่บ้านเลขที่ผู้แจ้ง")),
                        "phone": format_str(row.get("เบอร์โทรศัพท์ผู้แจ้ง")),
                    },
                    "code": format_str(row.get("CODE")),
                },
            }

            # ตรวจสอบว่ามีข้อมูลซ้ำหรือไม่
            existing_person = check_existing_missing_person(
                first_name=missing_first_name,
                last_name=missing_last_name,
                identification_number=missing_id_number if missing_id_number else None,
            )

            if existing_person:
                # Update ข้อมูลเดิม
                existing_person.reporting_date = reporting_date
                existing_person.title_name = title_name
                existing_person.first_name = missing_first_name
                existing_person.last_name = missing_last_name
                existing_person.age = missing_age
                existing_person.phone_number = phone_number
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

                # อัปเดตสถานะตาม sheet type
                existing_person.missing_person_status = status

                existing_person.physical_mark = format_str(row.get("ลักษณะรูปพรรณ"))
                existing_person.is_dna_collected = is_dna_collected
                existing_person.statement = format_str(row.get("คำให้การ/สอบปากคำ"))
                existing_person.body_received_date = body_received_date

                # ข้อมูลผู้แจ้ง
                existing_person.deceased_relationship = format_str(
                    row.get("ความสัมพันธ์กับผู้หาย/เสียชีวิต")
                )
                existing_person.reporter_title_name = reporter_title_name
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
                existing_person.source = source
                existing_person.code = format_str(row.get("CODE"))

                # อัปเดต metadata แต่เก็บประวัติเก่าไว้
                if not existing_person.metadata:
                    existing_person.metadata = {}

                # เก็บประวัติการ update
                if "import_history" not in existing_person.metadata:
                    existing_person.metadata["import_history"] = []

                existing_person.metadata["import_history"].append(
                    {
                        "updated_date": datetime.datetime.now().isoformat(),
                        "sheet_name": sheet_name,
                        "sheet_type": sheet_type,
                        "row_number": index + 2,
                    }
                )

                # อัปเดต metadata ปัจจุบัน
                existing_person.metadata.update(excel_metadata)

                existing_person.updated_by = current_user
                existing_person.updated_date = datetime.datetime.now()
                existing_person.save()
                updated_count += 1

                print(
                    f"[{sheet_name}] Updated {sheet_type}: {missing_first_name} {missing_last_name}"
                )

            else:
                # สร้างใหม่
                missing_person = models.MissingPerson(
                    # ข้อมูลคนหาย/เสียชีวิต
                    reporting_date=reporting_date,
                    title_name=title_name,
                    first_name=missing_first_name,
                    last_name=missing_last_name,
                    age=missing_age,
                    identification_number=missing_id_number,
                    phone_number=phone_number,
                    country=format_str(row.get("ประเทศคนหาย/เสียชีวิต")) or "Thailand",
                    province_info=format_str(row.get("จังหวัดคนหาย/เสียชีวิต")),
                    district_info=format_str(row.get("อำเภอคนหาย/เสียชีวิต")),
                    subdistrict_info=format_str(row.get("ตำบลคนหาย/เสียชีวิต")),
                    address_info=format_str(row.get("ที่อยู่บ้านเลขที่คนหาย/เสียชีวิต")),
                    # ใช้สถานะตาม sheet type
                    missing_person_status=status,
                    # ข้อมูลเพิ่มเติม
                    physical_mark=format_str(row.get("ลักษณะรูปพรรณ")),
                    is_dna_collected=is_dna_collected,
                    statement=format_str(row.get("คำให้การ/สอบปากคำ")),
                    body_received_date=body_received_date,
                    deceased_relationship=format_str(row.get("ความสัมพันธ์กับผู้หาย/เสียชีวิต")),
                    # ข้อมูลผู้แจ้ง
                    reporter_title_name=reporter_title_name,
                    reporter_first_name=format_str(row.get("ชื่อผู้แจ้ง")),
                    reporter_last_name=format_str(row.get("นามสกุลผู้แจ้ง")),
                    reporter_age=reporter_age,
                    reporter_identification_number=format_str(
                        row.get("หมายเลขบัตรประชาชนผู้แจ้ง")
                    ).split(".")[0],
                    reporter_country=format_str(row.get("ประเทศผู้แจ้ง")) or "Thailand",
                    reporter_province_info=format_str(row.get("จังหวัดผู้แจ้ง")),
                    reporter_district_info=format_str(row.get("อำเภอผู้แจ้ง")),
                    reporter_subdistrict_info=format_str(row.get("ตำบลผู้แจ้ง")),
                    reporter_address_info=format_str(row.get("ที่อยู่บ้านเลขที่ผู้แจ้ง")),
                    reporter_phone_number=reporter_phone,
                    code=format_str(row.get("CODE")),
                    source=source,
                    # เก็บ metadata ที่สร้างไว้
                    metadata=excel_metadata,
                    status="active",
                    created_by=current_user,
                    created_date=datetime.datetime.now(),
                    updated_by=current_user,
                    updated_date=datetime.datetime.now(),
                )

                missing_person.save()
                record_count += 1

                print(
                    f"[{sheet_name}] Created new {sheet_type}: {missing_first_name} {missing_last_name}"
                )

        except Exception as e:
            print(f"[{sheet_name}] Error processing row {index + 2}: {e}")

    return record_count, updated_count


def check_existing_missing_person(
    first_name, last_name=None, identification_number=None
):
    """Check if missing person already exists"""
    query = models.MissingPerson.objects(
        first_name=first_name,
        status="active",
    )
    # ถ้ามีนามสกุล ให้เช็คด้วย
    if last_name:
        query = query.filter(last_name=last_name)

    # ถ้ามีเลขบัตรประชาชน ให้เช็คด้วย

    if identification_number:
        query = query.filter(identification_number=identification_number)

    return query.first()


def format_str(value):
    """Convert NaN to empty string"""
    return str(value).strip() if pd.notna(value) else ""


def process_import_missing_person_file(
    import_missing_person_file,
    current_user,
    source,
):
    """Main process function"""
    file = import_missing_person_file.file
    source = import_missing_person_file.source

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
            source=source,
        )

        import_missing_person_file.upload_status = "completed"
        import_missing_person_file.record_count = record_count
        import_missing_person_file.save()

    except Exception as e:
        import_missing_person_file.upload_status = "failed"
        import_missing_person_file.error_messages.append(f"เกิดข้อผิดพลาด: {str(e)}")
        import_missing_person_file.save()
