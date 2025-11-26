import mongoengine as me
import pandas
import sys
from klabban.models import User, Refugee


def import_excel(base_path="."):
    user = User.objects(username="admin").first()

    if not user:
        print("admin user not found, please run init-admin.py first")
        return
    
    pd = pandas.read_excel(f"{base_path}/data/refugees.xlsx")

    for index, row in pd.iterrows():
        if refugee := Refugee.objects(name=row.get("name")).first():
            print(f"refugee {row.get('name')} already exists, skip")
            continue

        refugee = Refugee(
            name=row.get("name"),
            nick_name=row.get("nick_name", ""),
            phone=row.get("phone", ""),
            address=row.get("address", "")
        )
        refugee.save()
        print(f"refugee {row.get('name')} imported successfully")

    


if __name__ == "__main__":
    DB_NAME = "klabbandb"
    if len(sys.argv) > 1:
        me.connect(db=DB_NAME, host=sys.argv[1])
    else:
        me.connect(db=DB_NAME)
    print(f"connect to {DB_NAME}")

    import_excel()
    print("======= import excel success ========")
