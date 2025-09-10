import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

CSV_URL = os.environ["CSV_URL"]       
CONFIG_URL = os.environ["CONFIG_URL"] 
FROM_EMAIL = os.environ["FROM_EMAIL"]
FROM_PASSWORD = os.environ["FROM_PASSWORD"]
TO_EMAIL = os.environ["TO_EMAIL"]

def load_data(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def load_config(url: str) -> dict:
    config_df = pd.read_csv(url)
    config = dict(zip(config_df["key"], config_df["value"]))
    return {
        "days_ahead": int(config.get("days_ahead", 14)),
        "min_students": int(config.get("min_students", 15)),
    }

def filter_data(df: pd.DataFrame, days_ahead: int, min_students: int) -> pd.DataFrame:
    today = pd.Timestamp.today().normalize()
    cutoff = today + pd.Timedelta(days=days_ahead)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")

    # Dịch 2023 -> 2025
    df["start_date"] = df["start_date"] + pd.DateOffset(years=2)

    mask = (
        (today <= df["start_date"]) &
        (df["start_date"] <= cutoff) &
        (df["total_student"] < min_students)
    )
    return df.loc[mask]

def send_email_with_attachment(df, today):
    subject = f"Báo cáo danh sách lớp cần chú ý - {today.strftime('%d/%m/%Y')}"

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    if df.empty:
        body = f"Hôm nay là {today.strftime('%d/%m/%Y')}.\nKhông có lớp nào cần chú ý."
        msg.attach(MIMEText(body, "plain"))
    else:
        filename = f"report_{today}.xlsx"
        df.to_excel(filename, index=False)

        body = f"Hôm nay là {today.strftime('%d/%m/%Y')}.\nĐính kèm file danh sách lớp cần chú ý."
        msg.attach(MIMEText(body, "plain"))

        with open(filename, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

    print(f" Đã gửi email báo cáo tới {TO_EMAIL}")

if __name__ == "__main__":
    df = load_data(CSV_URL)
    config = load_config(CONFIG_URL)

    days_ahead = config["days_ahead"]
    min_students = config["min_students"]

    filtered = filter_data(df, days_ahead, min_students)
    today = datetime.today().date()

    print(f"\nHôm nay là {today.strftime('%d/%m/%Y')}")
    if not filtered.empty:
        print(f"Các lớp cần chú ý (bắt đầu trong {days_ahead} ngày tới và có < {min_students} học viên):")
        print(filtered)
    else:
        print(f"Không có lớp nào cần chú ý trong {days_ahead} ngày tới.")

    send_email_with_attachment(filtered, today)
