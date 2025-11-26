import datetime
import mongoengine as me


REFUGEE_STATUS_CHOICES = [
    ("active", "กำลังพักพิง"),
    ("back_home", "กลับบ้านแล้ว"),
    ("deactive", "ปิดการใช้งาน"),
]


class Refugee(me.Document):
    meta = {
        "collection": "refugees",
        "indexes": ["name", "status", "refugee_camp", "created_by"],
    }

    refugee_camp = me.ReferenceField("RefugeeCamp")
    nick_name = me.StringField(max_length=255)
    name = me.StringField(required=True, max_length=255)

    phone = me.StringField(max_length=32)
    address = me.StringField(max_length=512)

    nationality = me.StringField(max_length=128)
    ethnicity = me.StringField(max_length=128)
    remark = me.StringField()
    registration_date = me.DateTimeField(default=datetime.datetime.now)
    is_public_searchable = me.BooleanField(default=True)

    status = me.StringField(
        choices=REFUGEE_STATUS_CHOICES,
        default="active",
    )

    created_by = me.ReferenceField("User")
    updated_by = me.ReferenceField("User")
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
