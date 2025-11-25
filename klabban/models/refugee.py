import datetime
import mongoengine as me


class RefugeeCamp(me.Document):
    meta = {"collection": "refugee_camps", "indexes": ["name", "status", "created_by"]}

    id = me.ObjectIdField(primary_key=True)
    name = me.StringField(required=True)
    location_url = me.URLField()
    contact_info = me.StringField()
    line_id = me.StringField()

    status = me.StringField(choices=("deactive", "active"), default="active")

    created_by = me.ReferenceField("User", )
    updated_by = me.ReferenceField("User", )
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)

class Refugee(me.Document):
    meta = {
        "collection": "refugees",
        "indexes": ["name", "status", "refugee_camp", "created_by"],
    }

    id = me.ObjectIdField(primary_key=True)
    refugee_camp = me.ReferenceField("RefugeeCamp")
    nick_name = me.StringField()
    name = me.StringField(required=True)
    nationality = me.StringField()
    ethnicity = me.StringField()
    picture = me.FileField()  
    remark = me.StringField()
    registration_date = me.DateTimeField(default=datetime.datetime.now)
    is_public_searchable = me.BooleanField(default=True)
    
    status = me.StringField(
        choices=("deactive", "active", "back_home", "waiting"),
        default="waiting",
    )

    created_by = me.ReferenceField("User")
    updated_by = me.ReferenceField("User")
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
