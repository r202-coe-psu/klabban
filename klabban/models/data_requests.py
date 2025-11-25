import datetime
import mongoengine as me


class SensitiveDataRequest(me.Document):
    meta = {
        "collection": "sensitive_data_requests",
        "indexes": ["requester", "approver", "status", "request_date"],
    }

    id = me.ObjectIdField(primary_key=True)
    requester = me.ReferenceField("User", required=True)
    approver = me.ReferenceField("User")
    status = me.StringField(
        choices=("pending", "approved", "rejected", "cancelled"),
        default="pending",
    )
    request_date = me.DateTimeField(default=datetime.datetime.now)
    created_date = me.DateTimeField(default=datetime.datetime.now)
    updated_date = me.DateTimeField(default=datetime.datetime.now)
