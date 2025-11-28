import datetime
import pandas as pd
from klabban import models
import datetime
import xlsxwriter
import re
from openpyxl import load_workbook
from io import BytesIO
from klabban.models.refugees import REFUGEE_STATUS_CHOICES, GENDER

REQUIRE_HEADER = [
    "ชื่อ-นามสกุล",
    "วันที่ลงทะเบียน",
]

HEADER = [
    "ชื่อเล่น",
    "ชื่อ-นามสกุล",
    "ที่อยู่",
    "เบอร์โทรศัพท์",
    "สัญชาติ",
    "เชื้อชาติ",
    "ประเทศ",
    "อายุ",
    "เพศ",
    "โรคประจำตัว",
    "จำนวนคน",
    "สัตว์เลี้ยง",
    "จำนวนวันที่คาดว่าจะพัก",
    "กรณีติดต่อฉุกเฉิน",
    "หมายเหตุ",
    "วันที่ลงทะเบียน",
    "วันที่กลับบ้าน",
    "สถานะ",
]


def get_template():
    # เตรียม DataFrame พร้อมตัวอย่างข้อมูล
    example_data = {
        "ชื่อเล่น": ["แดง", "น้อย"],
        "ชื่อ-นามสกุล": ["สมชาย ใจดี", "สมหญิง รักสงบ"],
        "ที่อยู่": [
            "123 หมู่ 1 ต.สันทราย อ.สันทราย จ.เชียงใหม่",
            "456 หมู่ 2 ต.แม่เหียะ อ.เมือง จ.เชียงใหม่",
        ],
        "เบอร์โทรศัพท์": ["0812345678", "0898765432"],
        "สัญชาติ": ["ไทย", "ไทย"],
        "เชื้อชาติ": ["ไทย", "ไทย"],
        "ประเทศ": ["Thailand", "Myanmar"],
        "อายุ": [35, 28],
        "เพศ": ["ชาย", "หญิง"],
        "โรคประจำตัว": ["เบาหวาน", ""],
        "จำนวนคน": [4, 3],
        "สัตว์เลี้ยง": ["สุนัข 1 ตัว", ""],
        "จำนวนวันที่คาดว่าจะพัก": [30, 15],
        "กรณีติดต่อฉุกเฉิน": [
            "นายสมศักดิ์ (พี่ชาย) 0811111111",
            "นางสาวสมใจ (น้องสาว) 0822222222",
        ],
        "หมายเหตุ": ["ต้องการความช่วยเหลือด้านอาหาร", ""],
        "วันที่ลงทะเบียน": ["01/12/2024", "15/12/2024"],
        "วันที่กลับบ้าน": ["", ""],
        "สถานะ": ["กำลังพักพิง", "กำลังพักพิง"],
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
        status_choices = [choice[1] for choice in REFUGEE_STATUS_CHOICES]
        gender_choices = [choice[1] for choice in GENDER]

        validations = {
            "สถานะ": status_choices,
            "เพศ": gender_choices,
        }
        sheet_choices = "Choices_ตัวเลือกห้ามลบ"
        list_sheet = workbook.add_worksheet(sheet_choices)
        list_sheet.hide()  # ซ่อน sheet choices
        list_row = 0

        # loop สร้าง validation
        for column_name, source in validations.items():
            col_idx = df.columns.get_loc(column_name)

            # join string เพื่อเช็กความยาว
            joined = ",".join(map(str, source))
            if len(joined) > 255:
                # เขียนลง Lists sheet
                start_row = list_row
                for i, val in enumerate(source):
                    list_sheet.write(list_row, 0, val)
                    list_row += 1
                end_row = list_row - 1

                # ใช้ช่วง reference
                rng = f"={sheet_choices}!$A${start_row+1}:$A${end_row+1}"
                worksheet.data_validation(
                    first_row=first_row,
                    first_col=col_idx,
                    last_row=last_row,
                    last_col=col_idx,
                    options={"validate": "list", "source": rng},
                )
            else:
                # กรณีไม่เกิน 255 ใช้ list ได้เลย
                worksheet.data_validation(
                    first_row=first_row,
                    first_col=col_idx,
                    last_row=last_row,
                    last_col=col_idx,
                    options={"validate": "list", "source": list(source)},
                )

        # ปรับความกว้างคอลัมน์อัตโนมัติ
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

    output.seek(0)
    return output


def validate_import_file(import_refugee_file, file):
    if (
        file.filename
        and not file.filename.endswith(".xlsx")
        and not file.filename.endswith(".csv")
    ):
        import_refugee_file.error_messages.append(
            "นามสกุลไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์ Excel หรือ CSV"
        )
        import_refugee_file.save()
        return False

    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

    except Exception as e:
        print(e)
        import_refugee_file.error_messages = [
            "เกิดข้อผิดพลาดในการอ่านไฟล์ กรุณาตรวจสอบรูปแบบไฟล์"
        ]
        import_refugee_file.save()
        return False

    # ตรวจสอบ column ที่จำเป็น
    missed_columns = []
    for col in REQUIRE_HEADER:
        if col not in df.columns:
            missed_columns.append(col)

    if missed_columns:
        import_refugee_file.error_messages = [
            f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missed_columns)}"
        ]
        import_refugee_file.save()
        return False

    # ตรวจสอบข้อมูลที่ขาดหายในคอลัมน์ที่จำเป็น
    error_rows = []

    for index, row in df.iterrows():
        missing_fields = []

        for col in REQUIRE_HEADER:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                missing_fields.append(col)

        if missing_fields:
            error_rows.append(f"แถวที่ {index + 2}: ขาดข้อมูล {', '.join(missing_fields)}")

    if error_rows:
        import_refugee_file.error_messages = error_rows
        import_refugee_file.save()
        return False

    # บันทึก DataFrame สำหรับใช้ในการ import
    import_refugee_file.save()

    return True


# Helper function เพื่อแปลง NaN เป็น string ว่าง
def format_str(value):
    return str(value).strip() if pd.notna(value) else ""


def write_refugees_from_import_file(
    refugee_camp_id,
    file,
    current_user,
):
    if file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    record_count = 0

    for index, row in df.iterrows():
        try:
            # แปลงสถานะจากภาษาไทยเป็น key
            status = "active"  # default
            if pd.notna(row.get("สถานะ")):
                status_thai = str(row.get("สถานะ")).strip()
                for key, value in REFUGEE_STATUS_CHOICES:
                    if value == status_thai:
                        status = key
                        break

            # แปลงวันที่
            registration_date = None
            if pd.notna(row.get("วันที่ลงทะเบียน")):
                try:
                    if isinstance(row.get("วันที่ลงทะเบียน"), datetime.datetime):
                        registration_date = row.get("วันที่ลงทะเบียน").date()
                    else:
                        registration_date = pd.to_datetime(
                            row.get("วันที่ลงทะเบียน"), format="%d/%m/%Y", dayfirst=True
                        ).date()
                except:
                    registration_date = datetime.datetime.now().date()
            else:
                registration_date = datetime.datetime.now().date()

            back_home_date = None
            if pd.notna(row.get("วันที่กลับบ้าน")):
                try:
                    if isinstance(row.get("วันที่กลับบ้าน"), datetime.datetime):
                        back_home_date = row.get("วันที่กลับบ้าน").date()
                    else:
                        back_home_date = pd.to_datetime(
                            row.get("วันที่กลับบ้าน"), format="%d/%m/%Y", dayfirst=True
                        ).date()
                except:
                    back_home_date = None

            # แปลงตัวเลข
            age = None
            if pd.notna(row.get("อายุ")):
                try:
                    age = int(float(row.get("อายุ")))
                except:
                    age = None

            people_count = 1
            if pd.notna(row.get("จำนวนคน")):
                try:
                    people_count = int(float(row.get("จำนวนคน")))
                except:
                    people_count = 1

            expected_stay_days = None
            if pd.notna(row.get("จำนวนวันที่คาดว่าจะพัก")):
                try:
                    expected_stay_days = int(float(row.get("จำนวนวันที่คาดว่าจะพัก")))
                except:
                    expected_stay_days = None

            # แปลง gender
            gender = "undefined"  # default
            if pd.notna(row.get("เพศ")):
                gender_thai = str(row.get("เพศ")).strip()
                for key, value in GENDER:
                    if value == gender_thai:
                        gender = key
                        break

            # แปลงเบอร์โทร
            phone = ""
            if pd.notna(row.get("เบอร์โทรศัพท์")):
                phone = "0" + str(row.get("เบอร์โทรศัพท์")).strip()

            country = "Thailand"
            if pd.notna(row.get("ประเทศ")):
                country = str(row.get("ประเทศ")).strip()

            ethinicity = "ไทย"
            if pd.notna(row.get("เชื้อชาติ")):
                ethinicity = str(row.get("เชื้อชาติ")).strip()

            nationality = "ไทย"
            if pd.notna(row.get("สัญชาติ")):
                nationality = str(row.get("สัญชาติ")).strip()

            refugee = models.Refugee(
                refugee_camp=refugee_camp_id,
                nick_name=format_str(row.get("ชื่อเล่น")),
                name=format_str(row.get("ชื่อ-นามสกุล")),
                address=format_str(row.get("ที่อยู่")),
                phone=phone,
                nationality=nationality,
                ethnicity=ethinicity,
                country=country,
                age=age,
                gender=gender,
                congenital_disease=format_str(row.get("โรคประจำตัว")),
                people_count=people_count,
                pets=format_str(row.get("สัตว์เลี้ยง")),
                expected_days=expected_stay_days,
                emergency_contact=format_str(row.get("กรณีติดต่อฉุกเฉิน")),
                remark=format_str(row.get("หมายเหตุ")),
                registration_date=registration_date,
                back_home_date=back_home_date,
                status=status,
                metadata={"imported_from_excel_file": True},
                created_by=current_user,
                created_date=datetime.datetime.now(),
                updated_by=current_user,
                updated_date=datetime.datetime.now(),
            )

            refugee.save()
            record_count += 1

        except Exception as e:
            print(f"Error processing row {index + 2}: {e}")
    return record_count


def process_import_refugee_file(import_refugee_file, current_user, refugee_camp_id):
    file = import_refugee_file.file
    results = validate_import_file(import_refugee_file, file)
    if not results:
        import_refugee_file.file.delete()
        import_refugee_file.file = None
        import_refugee_file.upload_status = "failed"
        import_refugee_file.save()
        return
    file.seek(0)
    import_refugee_file.upload_status = "processing"
    import_refugee_file.save()
    record_count = write_refugees_from_import_file(
        refugee_camp_id=refugee_camp_id,
        file=file,
        current_user=current_user,
    )
    import_refugee_file.upload_status = "completed"
    import_refugee_file.record_count = record_count
    import_refugee_file.save()
