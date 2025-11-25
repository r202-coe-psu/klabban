import datetime
import mongoengine as me
from user_agents import parse
from flask_login import UserMixin


USER_ROLES = [
    ("user", "ผู้ใช้งานทั่วไป"),
    ("admin", "ผู้ดูแลระบบ"),
    ("refugee_camp_staff", "เจ้าหน้าที่ศูนย์พักพิง"),
]

STATUS_CHOICES = [
    ("active", "ใช้งาน"),
    ("inactive", "ไม่ใช้งาน"),
]


class User(me.Document, UserMixin):
    meta = {"collection": "users", "indexes": ["username", "email"]}

    """ข้อมูลทั่วไป"""
    display_name = me.StringField(default="")  # ชื่อที่แสดง
    first_name = me.StringField(max_length=128)  # ชื่อ
    last_name = me.StringField(max_length=128)  # นามสกุล
    username = me.StringField(required=True, min_length=3, max_length=64)  # ชื่อผู้ใช้งาน
    password = me.StringField(required=True, default="")  # รหัสผ่านผู้ใช้งาน
    email = me.StringField(max_length=128)  # email ผู้ใช้งาน

    # สถานะและบทบาท
    status = me.StringField(
        required=True,
        default="active",
        choices=[status[0] for status in STATUS_CHOICES],
    )  # สถานะ ผู้ใช้งาน

    roles = me.ListField(
        me.StringField(choices=USER_ROLES, default=["user"])
    )  # สิทธิ์การใช้งาน

    resources = me.DictField()  # ข้อมูลเพิ่มเติมของผู้ใช้งานจาก OAuth2

    # ความสัมพันธ์
    refugee_camp = me.ReferenceField(
        "RefugeeCamp", required=False
    )  # ศูนย์พักพิง (optional)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    creator = me.ReferenceField("User", dbref=True, required=False)  # ผู้สร้าง
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )
    updater = me.ReferenceField("User", dbref=True, required=False)  # ผู้แก้ไขล่าสุด
    last_login_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    @property
    def is_super_admin(self):
        return "super_admin" in self.role.user_roles

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash

        if check_password_hash(self.password, password):
            return True
        return False

    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def display_status(self):
        status_dict = dict(STATUS_CHOICES)
        return status_dict.get(self.status, self.status)

    def get_display_roles(self):
        role_dict = dict(USER_ROLES)
        return [role_dict.get(role, role) for role in self.roles]

    def is_admin(self):
        return "admin" in self.roles

    def is_refugee_camp_staff(self):
        return "refugee_camp_staff" in self.roles
