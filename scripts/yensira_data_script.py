import sys
from pathlib import Path
import os
import datetime
import pandas as pd
import mongoengine as me
from collections import Counter, defaultdict
from dotenv import dotenv_values

from klabban import models


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


def title_to_gender(x):
    if "นาย" in x or "เด็กชาย" in x or "ด.ช." in x:
        return "male"
    elif "นาง" in x or "เด็กหญิง" in x or "ด.ญ." in x:
        return "female"
    else:
        return "other"


def save(row, created_by=None, camp=None):
    """
    Save a row to the Refugee model.
    """
    refugee = models.Refugee.objects(
        name=row.get("name"),
        refugee_camp=camp,
    ).first()
    if refugee:
        print(f"Refugee '{row.get('name')}' already exists. Skip add.")
    else:
        refugee = models.Refugee(
            name=row.get("name"),
            refugee_camp=camp,
            created_by=created_by,
        )
        refugee.save()
        refugee.reload()
        print(f"save refugee '{refugee.name}' with ID: {refugee.id}")

    # print("row data:", row.to_dict())
    refugee.congenital_disease = row.get("โรค")
    refugee.phone = row.get("เบอร์โทร")
    refugee.gender = title_to_gender(row.get("title"))
    refugee.metadata["citizen_id"] = row.get("เลขบัตรประชาชน")
    refugee.metadata["HN"] = row.get("HN")
    refugee.metadata["patient"] = row.get("ผู้ป่วย", False)
    refugee.metadata["relative"] = row.get("ญาติ", False)
    # print("updated refugee data:", refugee.to_mongo().to_dict())

    refugee.save()
    print(f"update refugee '{refugee.name}' with ID: {refugee.id}")
    return refugee


def main():
    # usage: python psu_data_script.py [path_to_excel] [nrows] [save]
    # default path: ../data/psu_data.xlsx (two levels up from this script)
    # allow overriding path via first CLI arg (unless the arg is "save")
    if len(sys.argv) > 1 and sys.argv[1].lower() != "save":
        path = Path(sys.argv[1])
    # nrows = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5
    path_name = sys.argv[1] if len(sys.argv) > 1 else "data/yensira.xlsx"

    path = Path(path_name)
    print("Default path:", path)

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
    except Exception as e:
        print("Connected to MongoDB (could not determine DB name).")
        print(e)

    # query admin document (use find_one to get the document, not a cursor)
    admin = models.User.objects(username="admin").first()
    camp = models.RefugeeCamp.objects(name="อาคารเย็นศิระ 3").first()

    # obtain admin _id to use as created_by reference (None if not found)
    print("admin:", admin)
    print("camp_id:", camp)

    if not admin or not camp:
        print("Admin user or Refugee Camp not found in the database. Exiting.")
        return

    # Get list of all sheet names in the Excel file
    xl_file = pd.ExcelFile(path)
    sheet_names = [name for name in xl_file.sheet_names if name]
    print(f"Available sheets: {sheet_names}")

    # Read and process each sheet
    all_data_to_save = []

    for sheet_name in sheet_names:
        print(f"\nProcessing sheet: {sheet_name}")

        # Read the current sheet
        df = pd.read_excel(path, sheet_name=sheet_name)
        # print(f"Shape: {df.shape}")
        print("Columns:", df.columns.tolist())

        # Process the sheet data similar to the original logic
        # You can add sheet-specific processing here if needed

        # Combine columns 'ชื่อ-สกุล', 'Unnamed: 2', 'Unnamed: 3' into 'ชื่อ - นามสกุล'
        # Convert all columns to string and replace NaN with empty string
        df = df.astype(str).replace("nan", "")

        # Check if 'ชื่อ - นามสกุล' column exists and print its column number
        col_index = 1
        if "ชื่อ - สกุล" in df.columns:
            col_index = df.columns.get_loc("ชื่อ - สกุล")
            print(f"Column 'ชื่อ - สกุล' is at index: {col_index}")
        else:
            print("Column 'ชื่อ - สกุล' not found in this sheet")

        df["name"] = df.iloc[:, col_index : col_index + 4].apply(
            lambda x: " ".join(x.dropna().astype(str).str.strip()), axis=1
        )

        df = df.drop(df.columns[2:4], axis=1)
        # Rename the second column (index 1) to "title"
        df = df.rename(columns={df.columns[1]: "title"})

        # Convert 'ผู้ป่วย' and 'ญาติ' columns to boolean based on '/' presence
        if "ผู้ป่วย" in df.columns:
            df["ผู้ป่วย"] = df["ผู้ป่วย"].astype(str).str.contains("/", na=False)

        if "ญาติ" in df.columns:
            df["ญาติ"] = df["ญาติ"].astype(str).str.contains("/", na=False)

        print("after rename", df.columns)

        sheet_data = []
        for i, row in df.iterrows():
            if not row.get("name") or not str(row.get("name")).strip():
                continue
            sheet_data.append(row)

        all_data_to_save.extend(sheet_data)
        print(f"Added {len(sheet_data)} rows from sheet '{sheet_name}'")

    print(f"\nTotal rows from all sheets: {len(all_data_to_save)}")

    for i, row in enumerate(all_data_to_save):

        doc = save(row, created_by=admin, camp=camp)


if __name__ == "__main__":
    main()
