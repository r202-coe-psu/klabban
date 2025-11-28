import datetime
import mongoengine as me

STATUS = ["pending", "processing", "completed", "failed"]


class ImportRefugeeFile(me.Document):
    meta = {
        "collection": "import_refugee_files",
        "indexes": ["created_date"],
    }

    refugee_camp = me.ReferenceField("RefugeeCamp", required=True)
    file = me.FileField()
    file_name = me.StringField(required=True)
    error_messages = me.ListField(me.StringField())
    uploaded_date = me.DateTimeField(default=datetime.datetime.now)
    created_date = me.DateTimeField(default=datetime.datetime.now)
    created_by = me.ReferenceField("User", required=True)
    upload_status = me.StringField(choices=STATUS, default="pending")
