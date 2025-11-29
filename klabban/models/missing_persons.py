import datetime
import mongoengine as me


class MissingPerson(me.Document):
    meta = {
        "collection": "missing_persons",
        "indexes": ["created_date"],
    }
    # section: missing person information
    title_name = me.StringField()  # คำนำหน้าชื่อคนหาย/เสียชีวิต
    first_name = me.StringField(required=True, max_length=255)  # ชื่อคนหาย/เสียชีวิต
    last_name = me.StringField(required=True, max_length=255)  # นามสกุลคนหาย/เสียชีวิต
    age = me.IntField()  # อายุคนหาย/เสียชีวิต
    identification_number = me.StringField(max_length=100)  # หมายเลขบัตรประชาชน
    country = me.StringField(default="Thailand")  # ประเทศของคนหาย/เสียชีวิต
    province_info = me.StringField()  # จังหวัดของคนหาย/เสียชีวิต
    district_info = me.StringField()  # อําเภอของคนหาย/เสียชีวิต
    subdistrict_info = me.StringField()  # ตําบลของคนหาย/เสียชีวิต
    address_info = me.StringField()  # ที่อยู่บ้านเลขที่ของคนหาย/เสียชีวิต
    missing_person_status = me.StringField(
        choices=("missing", "death"), default="missing"
    )  # สถานะคนหาย/เสียชีวิต
    # section: additional information
    physical_mark = me.StringField()  # ลักษณะรูปพรรณของคนหาย/เสียชีวิต
    statement = me.StringField()  # สอบปากคําจากผู้แจ้ง/คําให้การ
    body_received_date = me.DateTimeField()  # วันที่รับศพ
    deceased_relationship = me.StringField()  # ความสัมพันธ์กับผู้หาย/เสียชีวิต
    # section: reporter information
    reporter_title_name = me.StringField()  # คำนำหน้าชื่อผู้แจ้ง
    reporter_first_name = me.StringField()  # ชื่อผู้แจ้ง
    reporter_last_name = me.StringField()  # นามสกุลผู้แจ้ง
    reporter_age = me.IntField()  # อายุผู้แจ้ง
    reporter_identification_number = me.StringField(
        max_length=100
    )  # หมายเลขบัตรประชาชนผู้แจ้ง
    reporter_country = me.StringField(default="Thailand")  # ประเทศของผู้แจ้ง
    reporter_province_info = me.StringField()  # จังหวัดของผู้แจ้ง
    reporter_district_info = me.StringField()  # อําเภอของผู้แจ้ง
    reporter_subdistrict_info = me.StringField()  # ตําบลของผู้แจ้ง
    reporter_address_info = me.StringField()  # ที่อยู่บ้านเลขที่ของผู้แจ้ง
    reporter_phone_number = me.StringField()  # เบอร์โทรศัพท์ผู้แจ้ง

    code = me.StringField()  # CODE
    metadata = me.DictField()  # ข้อมูลเสริม
    status = me.StringField(
        choices=("active", "disactive"), default="active"
    )  # สถานะข้อมูล

    created_by = me.ReferenceField(
        "User",
    )
    updated_by = me.ReferenceField(
        "User",
    )
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
