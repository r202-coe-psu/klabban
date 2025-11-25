import datetime
import mongoengine as me


class RefugeeCamp(me.Document):
    meta = {"collection": "refugee_camps", "indexes": ["name", "status", "created_by"]}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()
    location_url = me.URLField()
    contact_info = me.StringField()
    line_id = me.StringField(max_length=128)
    other_link = me.StringField(max_length=2048)

    status = me.StringField(choices=("deactive", "active"), default="active")

    created_by = me.ReferenceField(
        "User",
    )
    updated_by = me.ReferenceField(
        "User",
    )
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
