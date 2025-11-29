import datetime
import mongoengine as me


class ImportMissingPersonFile(me.document):
    meta = {
        "collection": "import_missing_person_files",
        "indexes": ["created_date"],
    }

    file = me.FileField()
    file_name = me.StringField(required=True)
    record_count = me.IntField(default=0)
    source = me.StringField(max_length=255)
    error_messages = me.ListField(me.StringField())
    uploaded_date = me.DateTimeField(default=datetime.datetime.now)
    created_date = me.DateTimeField(default=datetime.datetime.now)
    created_by = me.ReferenceField("User", required=True)
