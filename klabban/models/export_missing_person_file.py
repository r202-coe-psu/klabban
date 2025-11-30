import datetime
import mongoengine as me


class ExportMissingPersonFile(me.Document):
    meta = {
        "collection": "export_missing_person_files",
        "indexes": ["created_date"],
    }

    file = me.FileField()
    file_name = me.StringField(required=True)
    created_date = me.DateTimeField(default=datetime.datetime.now)
    created_by = me.ReferenceField("User", required=True)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
    updated_by = me.ReferenceField("User")
