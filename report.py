import pandas as pd
from datetime import datetime, timedelta

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfT4Y2v7BaO_ylomuFIKHfqQ0y-w37ritzpxbJVJcw0EgtLvPhNqi1yhDbzfi-EBWpM33NSC8sSsWE/pub?output=csv"

def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    # Lọc các lớp bắt đầu trong 14 ngày tới
    today = pd.Timestamp.today().normalize() 
    cutoff = today + pd.Timedelta(days=14)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")

    # Dịch 2023 -> 2025 để test
    df["start_date"] = df["start_date"] + pd.DateOffset(years=2)

    # Có < 15 học viên
    mask = (today <= df["start_date"]) & (df["start_date"] <= cutoff) & (df["total_student"] < 15)
    return df.loc[mask]

FROM_EMAIL = "03nguyenhaphuong@gmail.com"
FROM_PASSWORD = "ackx pfeb wugn heoe" 
TO_EMAIL = "launguyen927@gmail.com"         

def send_email_with_attachment(df, today):
    # Gửi email kèm file Excel
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

    # Gửi email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

    print(f"✅ Đã gửi email báo cáo tới {TO_EMAIL}")


if __name__ == "__main__":
    df = load_data(CSV_URL)
    filtered = filter_data(df)

    today = datetime.today().date()
    print(f"\nHôm nay là {today.strftime('%d/%m/%Y')}")

    if not filtered.empty:
        print("Các lớp cần chú ý (bắt đầu trong 14 ngày tới và có < 15 học viên):")
        print(filtered)
    else:
        print("Không có lớp nào cần chú ý trong 14 ngày tới.")

    # Gửi mail sau khi in ra màn hình
    send_email_with_attachment(filtered, today)