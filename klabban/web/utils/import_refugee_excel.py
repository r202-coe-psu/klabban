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
from klabban.web.utils.config import REFUGEE_REQUIRE_HEADER, REFUGEE_HEADER


def get_template():
    # เตรียม DataFrame พร้อมตัวอย่างข้อมูล
    example_data = {
        "ชื่อเล่น": ["แดง", "น้อย"],
        "ชื่อ-นามสกุล": ["สมชาย ใจดี", "สมหญิง รักสงบ"],
        "เลขบัตรประจำตัวประชาชน": ["1234567890123", "9876543210987"],
        "ที่อยู่": [
            "123 หมู่ 1 ต.สันทราย อ.สันทราย จ.เชียงใหม่",
            "456 หมู่ 2 ต.แม่เหียะ อ.เมือง จ.เชียงใหม่",
        ],
        "เบอร์โทรศัพท์": ["0812345678", "0898765432"],
        "สัญชาติ": ["ไทย", "ไทย"],
        "เชื้อชาติ": ["ไทย", "ไทย"],
        "ประเทศ": ["Thailand", "Thailand"],
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
        "หมายเหตุ": ["", ""],
        "วันที่ลงทะเบียน": ["01/12/2024", "15/12/2024"],
        "วันที่กลับบ้าน": ["", ""],
        "สถานะ": ["กำลังพักพิง", "กำลังพักพิง"],
        "ศูนย์พักพิง": ["มหาวิทยาลัยสงขลาครินทร์", "มหาวิทยาลัยสงขลาครินทร์"],
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


def check_existing_refugee(
    refugee_camp,
    name,
):
    query = models.Refugee.objects(
        refugee_camp=refugee_camp,
        name=name,
    )

    return query.first()


def get_refugee_camp_from_name(name):
    query = models.RefugeeCamp.objects(name=name, status="active")
    return query.first()


def validate_import_file(import_refugee_file, file, refugee_camp_param):
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
            # ตรวจสอบชื่อ sheet ก่อนอ่านข้อมูล
            xl_file = pd.ExcelFile(file)
            if "ข้อมูลผู้อพยพ" in xl_file.sheet_names:
                df = pd.read_excel(file, sheet_name="ข้อมูลผู้อพยพ")
            else:
                # ถ้าไม่พบ sheet ที่ต้องการ ให้อ่าน sheet แรก
                df = pd.read_excel(file, sheet_name=0)
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
    for col in REFUGEE_REQUIRE_HEADER:
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

        for col in REFUGEE_REQUIRE_HEADER:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                missing_fields.append(col)

        if missing_fields:
            error_rows.append(f"แถวที่ {index + 2}: ขาดข้อมูล {', '.join(missing_fields)}")

        # ตรวจสอบว่าศูนย์พักพิงมีอยู่ในระบบหรือไม่
        if pd.notna(row.get("ศูนย์พักพิง")):
            if refugee_camp_param != "all":
                camp_name = str(row.get("ศูนย์พักพิง")).strip()
                if camp_name != refugee_camp_param:
                    error_rows.append(
                        f"แถวที่ {index + 2}: ศูนย์พักพิงไม่ตรงกับที่เลือก ({refugee_camp_param})"
                    )
            else:
                camp_name = str(row.get("ศูนย์พักพิง")).strip()
                refugee_camp = get_refugee_camp_from_name(camp_name)
                if not refugee_camp:
                    error_rows.append(
                        f"แถวที่ {index + 2}: ไม่พบศูนย์พักพิง '{camp_name}' ในระบบ"
                    )
                elif refugee_camp.status != "active":
                    error_rows.append(
                        f"แถวที่ {index + 2}: ศูนย์พักพิง '{camp_name}' ไม่ได้เปิดใช้งาน"
                    )

        # ตรวจสอบรูปแบบวันที่ลงทะเบียน
        if pd.notna(row.get("วันที่ลงทะเบียน")):
            if not isinstance(row.get("วันที่ลงทะเบียน"), datetime.datetime):
                date_str = str(row.get("วันที่ลงทะเบียน")).strip()
                try:
                    # ลองหลายรูปแบบวันที่
                    try:
                        # รูปแบบ DD/MM/YYYY
                        pd.to_datetime(date_str, format="%d/%m/%Y", dayfirst=True)
                    except:
                        try:
                            # รูปแบบ YYYY-MM-DD HH:MM (จาก export)
                            pd.to_datetime(date_str, format="%Y-%m-%d %H:%M")
                        except:
                            # รูปแบบ YYYY-MM-DD
                            pd.to_datetime(date_str, format="%Y-%m-%d")
                except:
                    error_rows.append(
                        f"แถวที่ {index + 2}: รูปแบบวันที่ลงทะเบียนไม่ถูกต้อง ต้องเป็น DD/MM/YYYY หรือ YYYY-MM-DD เช่น 25/12/2024 หรือ 2024-12-25"
                    )

        # ตรวจสอบรูปแบบวันที่กลับบ้าน (ถ้ามี)
        if pd.notna(row.get("วันที่กลับบ้าน")):
            if not isinstance(row.get("วันที่กลับบ้าน"), datetime.datetime):
                date_str = str(row.get("วันที่กลับบ้าน")).strip()
                if date_str:  # ถ้าไม่ใช่ค่าว่าง
                    try:
                        # ลองหลายรูปแบบวันที่
                        try:
                            # รูปแบบ DD/MM/YYYY
                            pd.to_datetime(date_str, format="%d/%m/%Y", dayfirst=True)
                        except:
                            try:
                                # รูปแบบ YYYY-MM-DD HH:MM (จาก export)
                                pd.to_datetime(date_str, format="%Y-%m-%d %H:%M")
                            except:
                                # รูปแบบ YYYY-MM-DD
                                pd.to_datetime(date_str, format="%Y-%m-%d")
                    except:
                        error_rows.append(
                            f"แถวที่ {index + 2}: รูปแบบวันที่กลับบ้านไม่ถูกต้อง ต้องเป็น DD/MM/YYYY หรือ YYYY-MM-DD เช่น 25/12/2024 หรือ 2024-12-25"
                        )

        # ตรวจสอบค่าตัวเลข
        if pd.notna(row.get("อายุ")):
            try:
                age = int(float(row.get("อายุ")))
                if age < 0 or age > 150:
                    error_rows.append(f"แถวที่ {index + 2}: อายุต้องอยู่ระหว่าง 0-150 ปี")
            except:
                error_rows.append(f"แถวที่ {index + 2}: อายุต้องเป็นตัวเลขเท่านั้น")

        if pd.notna(row.get("จำนวนคน")):
            try:
                people_count = int(float(row.get("จำนวนคน")))
                if people_count < 1:
                    error_rows.append(f"แถวที่ {index + 2}: จำนวนคนต้องมากกว่า 0")
            except:
                error_rows.append(f"แถวที่ {index + 2}: จำนวนคนต้องเป็นตัวเลขเท่านั้น")

        if pd.notna(row.get("จำนวนวันที่คาดว่าจะพัก")):
            try:
                expected_days = int(float(row.get("จำนวนวันที่คาดว่าจะพัก")))
                if expected_days < 0:
                    error_rows.append(f"แถวที่ {index + 2}: จำนวนวันต้องเป็นค่าบวก")
            except:
                error_rows.append(f"แถวที่ {index + 2}: จำนวนวันต้องเป็นตัวเลขเท่านั้น")

        # ตรวจสอบเพศ
        if pd.notna(row.get("เพศ")):
            gender_thai = str(row.get("เพศ")).strip()
            valid_genders = [choice[1] for choice in GENDER]
            if gender_thai not in valid_genders:
                error_rows.append(
                    f"แถวที่ {index + 2}: เพศไม่ถูกต้อง ต้องเป็น {', '.join(valid_genders)}"
                )

        # ตรวจสอบสถานะ
        if pd.notna(row.get("สถานะ")):
            status_thai = str(row.get("สถานะ")).strip()
            valid_statuses = [choice[1] for choice in REFUGEE_STATUS_CHOICES]
            if status_thai not in valid_statuses:
                error_rows.append(
                    f"แถวที่ {index + 2}: สถานะไม่ถูกต้อง ต้องเป็น {', '.join(valid_statuses)}"
                )

    if error_rows:
        import_refugee_file.error_messages = error_rows
        import_refugee_file.save()
        return False

    import_refugee_file.save()

    return True


# Helper function เพื่อแปลง NaN เป็น string ว่าง
def format_str(value):
    return str(value).strip() if pd.notna(value) else ""


def write_refugees_from_import_file(
    refugee_camp,
    file,
    current_user,
    source,
):
    if file.filename.endswith(".xlsx"):
        # ตรวจสอบชื่อ sheet ก่อนอ่านข้อมูล
        xl_file = pd.ExcelFile(file)
        if "ข้อมูลผู้อพยพ" in xl_file.sheet_names:
            df = pd.read_excel(file, sheet_name="ข้อมูลผู้อพยพ")
        else:
            # ถ้าไม่พบ sheet ที่ต้องการ ให้อ่าน sheet แรก
            df = pd.read_excel(file, sheet_name=0)
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
                        date_str = str(row.get("วันที่ลงทะเบียน")).strip()
                        try:
                            # รูปแบบ DD/MM/YYYY
                            registration_date = pd.to_datetime(
                                date_str, format="%d/%m/%Y", dayfirst=True
                            ).date()
                        except:
                            try:
                                # รูปแบบ YYYY-MM-DD HH:MM
                                registration_date = pd.to_datetime(
                                    date_str, format="%Y-%m-%d %H:%M"
                                ).date()
                            except:
                                # รูปแบบ YYYY-MM-DD
                                registration_date = pd.to_datetime(
                                    date_str, format="%Y-%m-%d"
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
                        date_str = str(row.get("วันที่กลับบ้าน")).strip()
                        try:
                            # รูปแบบ DD/MM/YYYY
                            back_home_date = pd.to_datetime(
                                date_str, format="%d/%m/%Y", dayfirst=True
                            ).date()
                        except:
                            try:
                                # รูปแบบ YYYY-MM-DD HH:MM
                                back_home_date = pd.to_datetime(
                                    date_str, format="%Y-%m-%d %H:%M"
                                ).date()
                            except:
                                # รูปแบบ YYYY-MM-DD
                                back_home_date = pd.to_datetime(
                                    date_str, format="%Y-%m-%d"
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

            if pd.notna(row.get("ศูนย์พักพิง")):
                if refugee_camp == "all":
                    camp_name = str(row.get("ศูนย์พักพิง")).strip()
                    refugee_camp_obj = models.RefugeeCamp.objects(
                        name=camp_name, status="active"
                    ).first()
                    if refugee_camp_obj:
                        refugee_camp_id = refugee_camp_obj.id
                if refugee_camp != "all":
                    refugee_camp_id = refugee_camp.id

            if pd.notna(row.get("ชื่อ-นามสกุล")) and pd.notna(row.get("ชื่อเล่น")):
                existing_refugee = check_existing_refugee(
                    refugee_camp=refugee_camp_id,
                    name=str(row.get("ชื่อ-นามสกุล")).strip(),
                )
                if existing_refugee:
                    # Update ข้อมูลเดิม
                    existing_refugee.nick_name = format_str(row.get("ชื่อเล่น"))
                    existing_refugee.name = format_str(row.get("ชื่อ-นามสกุล"))
                    existing_refugee.identification_number = format_str(
                        row.get("เลขบัตรประจำตัวประชาชน")
                    )
                    existing_refugee.address = format_str(row.get("ที่อยู่"))
                    existing_refugee.phone = phone
                    existing_refugee.nationality = nationality
                    existing_refugee.ethnicity = ethinicity
                    existing_refugee.country = country
                    existing_refugee.age = age
                    existing_refugee.gender = gender
                    existing_refugee.congenital_disease = format_str(
                        row.get("โรคประจำตัว")
                    )
                    existing_refugee.people_count = people_count
                    existing_refugee.pets = format_str(row.get("สัตว์เลี้ยง"))
                    existing_refugee.expected_days = expected_stay_days
                    existing_refugee.emergency_contact = format_str(
                        row.get("กรณีติดต่อฉุกเฉิน")
                    )
                    existing_refugee.remark = format_str(row.get("หมายเหตุ"))
                    existing_refugee.registration_date = registration_date
                    existing_refugee.back_home_date = back_home_date
                    existing_refugee.source = source
                    existing_refugee.status = status
                    existing_refugee.updated_by = current_user
                    existing_refugee.updated_date = datetime.datetime.now()

                    existing_refugee.save()
                    record_count += 1
                else:
                    refugee = models.Refugee(
                        refugee_camp=refugee_camp_id,
                        nick_name=format_str(row.get("ชื่อเล่น")),
                        name=format_str(row.get("ชื่อ-นามสกุล")),
                        identification_number=format_str(
                            row.get("เลขบัตรประจำตัวประชาชน")
                        ),
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
                        source=source,
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


def process_import_refugee_file(import_refugee_file, current_user, refugee_camp):
    file = import_refugee_file.file
    results = validate_import_file(import_refugee_file, file, refugee_camp)
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
        refugee_camp=refugee_camp,
        file=file,
        current_user=current_user,
        source=import_refugee_file.source,
    )
    import_refugee_file.upload_status = "completed"
    import_refugee_file.record_count = record_count
    import_refugee_file.save()
