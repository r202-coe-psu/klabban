import mongoengine as me
from datetime import datetime


class File(me.Document):

    meta = {"collection": "files"}

    file = me.FileField(required=True, collection_name="files")
    title = me.StringField(required=True)
    description = me.StringField()
    mimetype = me.StringField(required=True)
    uploaded_by = me.ReferenceField("User", dbref=True)
    uploaded_date = me.DateTimeField(required=True, default=datetime.now)
    filesize = me.FloatField(required=True)
    metadata = me.DictField()

    refugee_camp = me.ReferenceField("RefugeeCamp",dbref=True)
    owner = me.ReferenceField("User", dbref=True, required=True)
