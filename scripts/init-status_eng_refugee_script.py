#!/usr/bin/env python3
import mongoengine as me
import sys

import datetime
from klabban.models import Refugee, RefugeeCamp, RefugeeStatusLog, User

def initialize_refugee_status():
    refugee_camps = RefugeeCamp.objects(name="คณะวิศวกรรมศาสตร์ มหาวิทยาลัยสงขลานครินทร์")
    count = 0
    if not refugee_camps:
        print("Refugee camp 'คณะวิศวกรรมศาสตร์ มหาวิทยาลัยสงขลานครินทร์' not found.")
    refugees = Refugee.objects(refugee_camp__in=refugee_camps)
    admin_user = User.objects(username="admin").first()
    for refugee in refugees:
        if refugee.status == "active":
            print(f"Set status for refugee '{refugee.name}' to 'back_home'")
            refugee.status = "back_home"
            refugee.back_home_date = datetime.datetime.now()
            count += 1
            refugee.status_log.append(
                RefugeeStatusLog(
                    status="back_home",
                    changed_by=admin_user,
                    ip_address="127.0.0.1",
                )
            )
            refugee.save()
    print(f"Total refugees updated to 'back_home': {count}")


if __name__ == "__main__":
    DB_NAME = "klabbandb"
    if len(sys.argv) > 1:
        me.connect(db=DB_NAME, host=sys.argv[1])
    else:
        me.connect(db=DB_NAME)
    print(f"connect to {DB_NAME}")

    initialize_refugee_status()
    print("======= change status success ========")
