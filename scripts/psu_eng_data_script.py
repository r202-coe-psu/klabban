import sys
from pathlib import Path
import os
import datetime
import pandas as pd
import mongoengine as me
from collections import Counter, defaultdict
from dotenv import dotenv_values


def to_py_datetime(x):
    if pd.isna(x):
        return None
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    if isinstance(x, datetime.datetime):
        return x
    try:
        return pd.to_datetime(x, dayfirst=True).to_pydatetime()
    except Exception:
        return None


def format_gender(x):
    if x == "ชาย":
        return "male"
    elif x == "หญิง":
        return "female"
    else:
        return "other"


def map_row_to_doc(row, created_by_id=None, camp_id=None):
    """
    Map a pandas Series row (Thai column names) to a dict ready for insertion.
    Adjust keys according to your Refugee schema.
    """

    def _clean(val, to_str=False, to_int=False):
        # normalize pandas/Excel NaN and empty strings to None
        if pd.isna(val):
            return None
        if val == "-":
            return None
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return None
            return s if to_str or not to_int else (int(s) if s.isdigit() else None)

        # numeric handling
        if to_str:
            # convert floats that are whole numbers to plain int string (eg. 123.0 -> "123")
            try:
                if isinstance(val, float) and val.is_integer():
                    return str(int(val))
            except Exception:
                pass
            return str(val)
        if to_int:
            try:
                return int(val)
            except Exception:
                return None
        return val

    # column names seen in the sheet
    name = row.get("ชื่อ-สกุล")

    registration_date = to_py_datetime(row.get("SubmitTime"))
    age = row.get("อายุ")
    try:
        age = int(age) if pd.notna(age) else None
    except Exception:
        age = None

    congenital_disease = []
    if pd.notna(row.get("โรคประจำตัว")):
        congenital_disease.append(str(row.get("โรคประจำตัว")))
    if pd.notna(row.get("ถ้าหากมีโรคประจำตัว (โปรดตอบ)  และ ได้พกยาอะไรมาบ้าง")):
        congenital_disease.append(
            str(row.get("ถ้าหากมีโรคประจำตัว (โปรดตอบ)  และ ได้พกยาอะไรมาบ้าง"))
        )

    metadata = {
        "status": _clean(row.get("สถานะ"), to_str=True),
        "department": _clean(row.get("สังกัด"), to_str=True),
        "student_id": _clean(row.get("รหัส นศ"), to_str=True),
        "room": _clean(row.get("ห้องที่พัก"), to_str=True),
        "amount": _clean(row.get("จำนวน"), to_str=True),
    }

    doc = {
        "refugee_camp": camp_id,
        "nick_name": None,
        "name": _clean(name, to_str=True),
        "nationality": None,
        "ethnicity": None,
        "remark": _clean(row.get("หมายเหตุ"), to_str=True),
        "registration_date": registration_date,
        "is_public_searchable": True,
        "status": "active",
        "congenital_disease": (
            " | ".join(congenital_disease) if congenital_disease else None
        ),
        # extra fields from the sheet (clean NaN/empty values)
        "gender": format_gender(_clean(row.get("เพศ"), to_str=True)),
        "phone": _clean(row.get("เบอร์โทร"), to_str=True),
        "age": age,
        "address": _clean(row.get("บ้านเลขที่ ถนน ซอย"), to_str=True),
        "pets": _clean(row.get("สัตว์เลี้ยง"), to_str=True),
        "expected_days": _clean(row.get("คาดว่าจะเข้าพักอาศัยจำนวนกี่วัน"), to_int=True),
        "people_count": _clean(row.get("เข้าพักกี่คน"), to_int=True),
        "emergency_contact": _clean(
            row.get("บุคคลติดต่อฉุกเฉิน (ชื่อ-สกุล และเบอร์โทร)"), to_str=True
        ),
        "metadata": metadata,
        "created_by": created_by_id,
        "updated_by": created_by_id,
        "created_date": datetime.datetime.now(),
        "updated_date": datetime.datetime.now(),
    }
    # remove None entries for cleaner insert
    return {k: v for k, v in doc.items() if v is not None}


def duplicate_drop(data_to_save):
    counter = Counter()
    examples = defaultdict(list)
    for idx, doc in enumerate(data_to_save):
        name = doc.get("name")
        if not name:
            continue
        norm = name.strip().lower()
        counter[norm] += 1
        if len(examples[norm]) < 3:
            examples[norm].append((idx, name))

    duplicates = {n: c for n, c in counter.items() if c > 1}
    print(
        f"\nSummary: total_rows={len(data_to_save)}, unique_names={len(counter)}, duplicate_groups={len(duplicates)}"
    )
    if duplicates:
        print("Top duplicate name groups (count — examples index:name):")
        for norm, count in sorted(duplicates.items(), key=lambda x: -x[1])[:20]:
            ex = examples[norm]
            ex_str = ", ".join(f"{i}:{nm}" for i, nm in ex)
            print(f"{count} — {ex_str}")

    # remove duplicates by normalized name (keep first occurrence)
    seen = set()
    unique_docs = []
    dropped_docs = []
    for idx, doc in enumerate(data_to_save):
        name = doc.get("name")
        if not name:
            unique_docs.append(doc)
            continue
        norm = name.strip().lower()
        if norm in seen:
            dropped_docs.append((idx, name))
            continue
        seen.add(norm)
        unique_docs.append(doc)

    print(f"Dropped {len(dropped_docs)} duplicate rows")
    if dropped_docs:
        print(
            "Some dropped examples (index:name):",
            ", ".join(f"{i}:{n}" for i, n in dropped_docs[:10]),
        )
    return unique_docs


def main():
    # usage: python psu_data_script.py [path_to_excel] [nrows] [save]
    # default path: ../data/psu_data.xlsx (two levels up from this script)
    default_path = (
        Path(__file__).resolve().parents[2]
        / "/deployment/klabban/data/psu_eng_data.csv"
    )
    path = default_path
    # allow overriding path via first CLI arg (unless the arg is "save")
    if len(sys.argv) > 1 and sys.argv[1].lower() != "save":
        path = Path(sys.argv[1])
    # nrows = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5
    do_save = len(sys.argv) > 1 and sys.argv[1].lower() == "save"

    if not path.exists():
        print(f"File not found: {path}")
        return

    config = dotenv_values(".env")
    print(config)
    try:
        dbname = config.get("MONGODB_DB")
        host = config.get("MONGODB_HOST", "localhost")
        port = int(config.get("MONGODB_PORT", 27017))
        username = config.get("MONGODB_USERNAME", "")
        password = config.get("MONGODB_PASSWORD", "")
        me.connect(
            db=dbname, host=host, port=port, username=username, password=password
        )
        db = me.get_db()
    except Exception as e:
        print("Connected to MongoDB (could not determine DB name).")
        print(e)
        db = None

    # query admin document (use find_one to get the document, not a cursor)
    admin = None
    camp = None
    if db is not None:
        try:
            admin = db["users"].find_one({"username": "admin"})
            camp = db["refugee_camps"].find_one(
                {"name": "คณะวิศวกรรมศาสตร์ มหาวิทยาลัยสงขลานครินทร์"}
            )
        except Exception as e:
            print("Error querying admin user:", e)

    # obtain admin _id to use as created_by reference (None if not found)
    admin_id = admin.get("_id") if admin else None
    camp_id = camp.get("_id") if camp else None
    print("admin:", admin)
    print("camp_id:", camp_id)

    df = pd.read_csv(path)
    print(f"Loaded: {path}")
    print(f"Shape: {df.shape}")
    print(df.columns)
    # Index(['ชื่อ-สกุล', 'เพศ', 'สถานะ', 'สังกัด', 'รหัส นศ', 'ห้องที่พัก', 'จำนวน',
    #    'หมายเหตุ', 'SubmitTime', 'เวลาที่แจ้งออกจากที่พัก', 'จำนวนแจ้งออก'],
    #   dtype='object')

    data_to_save = []

    for i, row in df.iterrows():
        # skip rows with missing or empty name
        name_val = row.get("ชื่อ-สกุล")
        # use pandas isna to detect NaN/None, and also skip empty strings
        if pd.isna(name_val):
            continue
        if isinstance(name_val, str) and not name_val.strip():
            continue
        doc = map_row_to_doc(row, created_by_id=admin_id, camp_id=camp_id)
        data_to_save.append(doc)
    print("All sheet lens:", len(data_to_save))
    print(data_to_save[-1])

    data_to_save = duplicate_drop(data_to_save)

    if do_save:
        try:
            for doc in data_to_save:
                db["refugees"].insert_one(doc)
        except Exception as e:
            print("Error inserting documents:", e)


if __name__ == "__main__":
    main()
