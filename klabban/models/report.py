import datetime
import mongoengine as me


STATUS_CHOICES = [
    ("unread", "ยังไม่ได้อ่าน"),
    ("read", "อ่านแล้ว"),
]


class Report(me.Document):
    meta = {
        "collection": "reports",
        "indexes": ["created_date"],
    }

    title = me.StringField(required=True, max_length=255)
    ip_address = me.StringField()
    status = me.StringField(default="unread", choices=STATUS_CHOICES)
    created_date = me.DateTimeField(default=datetime.datetime.now)
    created_by = me.ReferenceField("User")
