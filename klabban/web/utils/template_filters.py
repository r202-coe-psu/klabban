from flask import url_for
import datetime


def static_url(filename: str):
    return add_date_url(url_for("static", filename=filename))


def add_date_url(url: str):
    now = datetime.datetime.now()
    return f"{url}?date={now.strftime('%Y%m%d')}"


def format_date(date: datetime.datetime, formatter: str = "%d/%m/%Y"):
    return date.strftime(formatter)


def format_number(data: str | int | float, digits: int = 0):
    if digits == 0:
        return f"{data:,.0f}"
    else:
        return f"{data:,.{digits}f}"


def format_month_th(month_num: str | int):
    months = [
        "มกราคม",
        "กุมภาพันธ์",
        "มีนาคม",
        "เมษายน",
        "พฤษภาคม",
        "มิถุนายน",
        "กรกฎาคม",
        "สิงหาคม",
        "กันยายน",
        "ตุลาคม",
        "พฤศจิกายน",
        "ธันวาคม",
    ]
    return months[int(month_num) - 1]


def format_thai_date(dt):
    if not isinstance(dt, datetime.datetime) and not isinstance(dt, datetime.date):
        return ""

    thai_year = dt.year + 543
    thai_months = {
        1: "มกราคม",
        2: "กุมภาพันธ์",
        3: "มีนาคม",
        4: "เมษายน",
        5: "พฤษภาคม",
        6: "มิถุนายน",
        7: "กรกฎาคม",
        8: "สิงหาคม",
        9: "กันยายน",
        10: "ตุลาคม",
        11: "พฤศจิกายน",
        12: "ธันวาคม",
    }
    thai_month = thai_months[dt.month]

    return f"{dt.day} {thai_month} {thai_year}"


def format_thai_date_short_month(dt):
    if not isinstance(dt, datetime.datetime):
        return ""

    thai_year = dt.year + 543
    thai_months = {
        1: "ม.ค.",
        2: "ก.พ.",
        3: "มี.ค.",
        4: "ม.ย.",
        5: "พ.ค.",
        6: "มิ.ย.",
        7: "ก.ค.",
        8: "ส.ค.",
        9: "ก.ย.",
        10: "ต.ค.",
        11: "พ.ย.",
        12: "ธ.ค.",
    }
    thai_month = thai_months[dt.month]

    return f"{dt.day} {thai_month} {thai_year}"


def format_thai_datetime_short_month(dt):
    if not isinstance(dt, datetime.datetime):
        return ""

    thai_year = dt.year + 543
    thai_months = {
        1: "ม.ค.",
        2: "ก.พ.",
        3: "มี.ค.",
        4: "ม.ย.",
        5: "พ.ค.",
        6: "มิ.ย.",
        7: "ก.ค.",
        8: "ส.ค.",
        9: "ก.ย.",
        10: "ต.ค.",
        11: "พ.ย.",
        12: "ธ.ค.",
    }
    thai_month = thai_months[dt.month]

    return f"{dt.day} {thai_month} {thai_year} {dt.hour:02}:{dt.minute:02} น."
