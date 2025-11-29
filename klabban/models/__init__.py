from flask_mongoengine import MongoEngine
from flask import Flask
from klabban.models.users import User
from klabban.models.refugees import (
    Refugee,
    RefugeeStatusLog,
    RefugeeCampsLog,
    REFUGEE_STATUS_CHOICES,
    RefugeeNoteLog,
)
from klabban.models.refugee_camps import RefugeeCamp
from klabban.models.oauth2 import OAuth2Token
from klabban.models.export_refugee_files import ExportRefugeeFile
from klabban.models.import_refugee_files import ImportRefugeeFile
from klabban.models.report import Report, STATUS_CHOICES
from klabban.models.missing_persons import MissingPerson
from klabban.models.import_missing_person_files import ImportMissingPersonFile


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
