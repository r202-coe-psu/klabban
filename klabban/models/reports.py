import datetime
import mongoengine as me

STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
]

REPORT_STATUS_CHOICES = [
    ("unread", "Unread"),
    ("read", "Read"),
]

REPORT_TYPE_CHOICES = [
    ("cannot_back_home", "พบชื่อแต่ไม่สามารถเปลี่ยนสถานะกลับบ้านได้ (โปรดระบุชื่อผู้อพยพ)"),
    ("not_found", "ไม่พบชื่อผู้อพยพในระบบ"),
    ("bug", "บั๊กในระบบ"),
]

class Report(me.Document):
    meta = {
        "collection": "reports",
        "indexes": ["created_date"],
    }

    title = me.StringField(required=True, max_length=255)
    description = me.StringField(required=True, max_length=1024)
    staff_note = me.StringField(max_length=512)
    staff = me.ReferenceField("User")
    phone_number = me.StringField(max_length=32)
    report_type = me.StringField(choices=REPORT_TYPE_CHOICES, required=True)
    report_status = me.StringField(choices=REPORT_STATUS_CHOICES, default="unread")

    ip_address = me.StringField()

    status = me.StringField(choices=STATUS_CHOICES, default="active")
    created_date = me.DateTimeField(default=datetime.datetime.now)
