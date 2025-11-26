import datetime
import mongoengine as me


REFUGEE_STATUS_CHOICES = [
    ("active", "กำลังพักพิง"),
    ("back_home", "กลับบ้านแล้ว"),
    ("deactive", "ปิดการใช้งาน"),
]

GENDER = [("male", "ชาย"), ("female", "หญิง"), ("other", "ไม่ระบุ")]


class Refugee(me.Document):
    meta = {
        "collection": "refugees",
        "indexes": ["name", "status", "refugee_camp", "created_by"],
    }

    refugee_camp = me.ReferenceField("RefugeeCamp")
    name = me.StringField(required=True, max_length=255)
    # extra fields
    gender = me.StringField(choices=GENDER)
    phone = me.StringField(max_length=32)
    congenital_disease = me.StringField(max_length=512)
    nick_name = me.StringField(max_length=255)
    nationality = me.StringField(max_length=128)
    ethnicity = me.StringField(max_length=128)
    country = me.StringField(max_length=128)
    age = me.IntField()
    address = me.StringField(max_length=512)
    pets = me.StringField(max_length=512)
    expected_days = me.IntField()
    people_count = me.IntField(default=1, min_value=1)
    emergency_contact = me.StringField(max_length=255)

    remark = me.StringField()
    registration_date = me.DateTimeField(default=datetime.datetime.now)
    back_home_date = me.DateTimeField()
    is_public_searchable = me.BooleanField(default=True)

    # universal field
    metadata = me.DictField()

    status = me.StringField(
        choices=REFUGEE_STATUS_CHOICES,
        default="active",
    )

    created_by = me.ReferenceField("User")
    updated_by = me.ReferenceField("User")
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
