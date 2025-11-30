from flask_mongoengine import MongoEngine
from flask import Flask
from klabban.models.users import User
from klabban.models.refugees import (
    Refugee,
    RefugeeStatusLog,
    RefugeeCampsLog,
    REFUGEE_STATUS_CHOICES,
)
from klabban.models.refugee_camps import RefugeeCamp
from klabban.models.oauth2 import OAuth2Token
from klabban.models.export_refugee_files import ExportRefugeeFile
from klabban.models.import_refugee_files import ImportRefugeeFile
from klabban.models.missing_persons import MissingPerson, TITLE_NAME_CHOICES
from klabban.models.import_missing_person_files import ImportMissingPersonFile
from klabban.models.reports import (
    Report,
    REPORT_STATUS_CHOICES,
    REPORT_TYPE_CHOICES,
    STATUS_CHOICES,
)
from klabban.models.export_missing_person_file import ExportMissingPersonFile


import mongoengine as me

__all__ = [
    "User",
    "Refugee",
    "RefugeeStatusLog",
    "RefugeeCamp",
    "OAuth2Token",
    "ExportRefugeeFile",
    "RefugeeCampsLog",
    "RefugeeNoteLog",
    "ImportRefugeeFile",
    "MissingPerson",
    "Report",
    "ExportMissingPersonFile",
]

db = MongoEngine()


def init_db(app: Flask):
    db.init_app(app)


def init_mongoengine(settings):
    dbname = settings.get("MONGODB_DB")
    host = settings.get("MONGODB_HOST", "localhost")
    port = int(settings.get("MONGODB_PORT", "27017"))
    username = settings.get("MONGODB_USERNAME", "")
    password = settings.get("MONGODB_PASSWORD", "")

    me.connect(db=dbname, host=host, port=port, username=username, password=password)
