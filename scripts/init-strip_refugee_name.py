#!/usr/bin/env python3
import mongoengine as me
import sys
from klabban.models import Refugee


def strip_refugee_name():
    refugees = Refugee.objects()
    for refugee in refugees:
        refugee.name = refugee.name.strip()
        refugee.save()

if __name__ == "__main__":
    DB_NAME = "klabbandb"
    if len(sys.argv) > 1:
        me.connect(db=DB_NAME, host=sys.argv[1])
    else:
        me.connect(db=DB_NAME)
    print(f"connect to {DB_NAME}")

    strip_refugee_name()
    print("======= create user success ========")
