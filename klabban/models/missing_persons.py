import datetime
import mongoengine as me

TITLE_NAME_CHOICES = (
    ("", "-"),
    ("นาย", "นาย"),
    ("นาง", "นาง"),
    ("นางสาว", "นางสาว"),
    ("เด็กชาย", "เด็กชาย"),
    ("เด็กหญิง", "เด็กหญิง"),
)

MISSING_PERSON_STATUS_CHOICES = (
    ("missing", "สูญหาย"),
    ("death", "เสียชีวิต"),
)


class MissingPerson(me.Document):
    meta = {
        "collection": "missing_persons",
        "indexes": ["created_date"],
    }
    # section: missing person information
    reporting_date = me.DateTimeField()
    title_name = me.StringField()  # คำนำหน้าชื่อคนหาย/เสียชีวิต
    first_name = me.StringField(required=True, max_length=255)  # ชื่อคนหาย/เสียชีวิต
    last_name = me.StringField(max_length=255)  # นามสกุลคนหาย/เสียชีวิต
    age = me.IntField()  # อายุคนหาย/เสียชีวิต
    identification_number = me.StringField(max_length=100)  # หมายเลขบัตรประชาชน
    phone_number = me.StringField(max_length=20)  # เบอร์โทรศัพท์คนหาย/เสียชีวิต
    country = me.StringField(default="ไทย", max_length=100)  # ประเทศของคนหาย/เสียชีวิต
    province_info = me.StringField(max_length=255)  # จังหวัดของคนหาย/เสียชีวิต
    district_info = me.StringField(max_length=255)  # อําเภอของคนหาย/เสียชีวิต
    subdistrict_info = me.StringField(max_length=255)  # ตําบลของคนหาย/เสียชีวิต
    address_info = me.StringField(max_length=512)  # ที่อยู่บ้านเลขที่ของคนหาย/เสียชีวิต
    missing_person_status = me.StringField(
        choices=MISSING_PERSON_STATUS_CHOICES, default="missing"
    )  # สถานะคนหาย/เสียชีวิต
    # section: additional information
    physical_mark = me.StringField()  # ลักษณะรูปพรรณของคนหาย/เสียชีวิต
    statement = me.StringField()  # สอบปากคําจากผู้แจ้ง/คําให้การ
    body_received_date = me.DateTimeField()  # วันที่รับศพ
    deceased_relationship = me.StringField(max_length=255)  # ความสัมพันธ์กับผู้หาย/เสียชีวิต

    # section: reporter information
    reporter_title_name = me.StringField()  # คำนำหน้าชื่อผู้แจ้ง
    reporter_first_name = me.StringField(max_length=255)  # ชื่อผู้แจ้ง
    reporter_last_name = me.StringField(max_length=255)  # นามสกุลผู้แจ้ง
    reporter_age = me.IntField()  # อายุผู้แจ้ง
    reporter_identification_number = me.StringField(
        max_length=100
    )  # หมายเลขบัตรประชาชนผู้แจ้ง
    reporter_country = me.StringField(default="Thailand")  # ประเทศของผู้แจ้ง
    reporter_province_info = me.StringField(max_length=255)  # จังหวัดของผู้แจ้ง
    reporter_district_info = me.StringField(max_length=255)  # อําเภอของผู้แจ้ง
    reporter_subdistrict_info = me.StringField(max_length=255)  # ตําบลของผู้แจ้ง
    reporter_address_info = me.StringField(max_length=512)  # ที่อยู่บ้านเลขที่ของผู้แจ้ง
    reporter_phone_number = me.StringField(max_length=20)  # เบอร์โทรศัพท์ผู้แจ้ง
    is_dna_collected = me.BooleanField(default=False)  # เก็บตัวอย่างดีเอ็นเอหรือไม่
    code = me.StringField(max_length=255)  # CODE
    source = me.StringField()  # แหล่งที่มาของข้อมูล เช่น หน่วยงานที่รายงาน
    metadata = me.DictField()  # ข้อมูลเสริม
    status = me.StringField(
        choices=("active", "inactive"), default="active"
    )  # สถานะข้อมูล

    created_by = me.ReferenceField(
        "User",
    )
    updated_by = me.ReferenceField(
        "User",
    )
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
