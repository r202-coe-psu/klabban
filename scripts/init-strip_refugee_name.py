#!/usr/bin/env python3
import mongoengine as me
import sys
from klabban.models import Refugee


def strip_refugee_name():
    refugees = Refugee.objects()
    count = 0
    for refugee in refugees:
        old_name = refugee.name
        refugee.name = refugee.name.strip()
        if old_name != refugee.name:
            print(f"Updating refugee name from '{old_name}' to '{refugee.name}'")
            count += 1
        refugee.save()
    print(f"Total refugee names updated: {count}")


if __name__ == "__main__":
    DB_NAME = "klabbandb"
    if len(sys.argv) > 1:
        me.connect(db=DB_NAME, host=sys.argv[1])
    else:
        me.connect(db=DB_NAME)
    print(f"connect to {DB_NAME}")

    strip_refugee_name()
    print("======= create user success ========")
