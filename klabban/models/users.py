import datetime
import mongoengine as me
from user_agents import parse
from flask_login import UserMixin


USER_ROLES = [
    ("user", "ผู้ใช้งานทั่วไป"),
    ("admin", "ผู้ดูแลระบบ"),
    ("refugee_camp_staff", "เจ้าหน้าที่ศูนย์พักพิง"),
]

TITLE_CHOICES = ["นาย", "นางสาว", "นาง"]

STATUS = [
    ("active", "ใช้งาน"),
    ("disactive", "ไม่ใช้งาน"),
    ("unregister", "ไม่ได้ลงทะเบียน"),
]


class User(me.Document, UserMixin):
    meta = {"collection": "users", "indexes": ["first_name", "last_name"]}

    """ข้อมูลทั่วไป"""
    display_name = me.StringField(default="")  # ชื่อที่แสดง
    first_name = me.StringField(max_length=128)  # ชื่อ
    last_name = me.StringField(max_length=128)  # นามสกุล
    username = me.StringField(required=True, min_length=3, max_length=64)  # ชื่อผู้ใช้งาน
    password = me.StringField(required=True, default="")  # รหัสผ่านผู้ใช้งาน
    email = me.StringField(max_length=128)  # email ผู้ใช้งาน

    """ข้อมูลติดต่อ"""
    emergency_contact = me.StringField(max_length=128, default="")  # เบอร์โทรฉุกเฉิน

    """ข้อมูลผู้ใช้งาน"""
    roles = me.ListField(
        me.StringField(
            default=USER_ROLES[0][0], choices=[role[0] for role in USER_ROLES]
        )
    )  # สิทธิ์การใช้งาน

    status = me.StringField(
        required=True, default="active", choices=STATUS
    )  # สถานะ ผู้ใช้งาน

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
        return f"{self.title}{self.first_name} {self.last_name}"

    def display_status(self):
        if "disactivate" in self.status:
            return "ยกเลิก"
        return "เปิดใช้งาน"

    def get_user_roles(self):
        if not self.role or not self.role.user_roles:
            return []
        return self.role.user_roles

    def get_display_roles(self):
        display_roles = []
        if not self.role or not self.role.user_roles:
            return display_roles
        role_dict = dict(USER_ROLES)
        for role in self.role.user_roles:
            display_roles.append(role_dict.get(role, role))
        return display_roles
