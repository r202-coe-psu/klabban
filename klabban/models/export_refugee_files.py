import datetime
import mongoengine as me


class ExportRefugeeFile(me.Document):
    meta = {
        "collection": "export_refugee_files",
        "indexes": ["refugee_camp", "created_date"],
    }

    refugee_camp = me.ReferenceField("RefugeeCamp", required=True)
    file = me.FileField()
    created_date = me.DateTimeField(default=datetime.datetime.now)
    creator = me.ReferenceField("User", required=True)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
    updater = me.ReferenceField("User")
