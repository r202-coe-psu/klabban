#!/usr/bin/env python3
import mongoengine as me
import sys
from klabban.models import User


def init_admin():
    if User.objects(username="admin").first():
        admin_user = User.objects(username="admin").first()
        admin_user.set_password("p@ssw0rd")
        admin_user.save()
        print("already have admin user in database")
        return

    admin_user = User(
        username="admin",
        email="admin@example.com",
        first_name="เจ้าหน้าที่",
        last_name="ดูแลระบบ",
        status="active",
        roles=["admin"],
    )
    admin_user.set_password("r202@k1abb4n")
    admin_user.save()


if __name__ == "__main__":
    DB_NAME = "klabbandb"
    if len(sys.argv) > 1:
        me.connect(db=DB_NAME, host=sys.argv[1])
    else:
        me.connect(db=DB_NAME)
    print(f"connect to {DB_NAME}")

    init_admin()
    print("======= create user success ========")
