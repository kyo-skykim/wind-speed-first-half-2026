# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root  # รันได้จากทุกที่ใน VS Code
"""
Silver = ทำความสะอาด: แปลงวันที่ + เปลี่ยนชื่อคอลัมน์ + เพิ่มคอลัมน์ที่คำนวณ
"""
import os
import pandas as pd

os.makedirs("data/processed", exist_ok=True)

# อ่านจาก Bronze
df = pd.read_csv("data/processed/bronze.csv")

# เปลี่ยนชื่อคอลัมน์ให้อ่านง่าย
df = df.rename(columns={
    "Date": "date",
    "A - 3.9knot": "calm",       # ลมสงบ
    "B 4.0 - 7.8knot": "light",  # ลมเบา
    "C 7.9 - 11.7knot": "gentle",# ลมอ่อน
    "D 11.8 - 15.6knot": "moderate",
    "E 15.7 - 19.4knot": "fresh",
    "F > 19.4knot": "strong",
    "total %": "total",
})

# แปลงวันที่ text -> date จริง แล้วแยกเดือน
df["date"] = pd.to_datetime(df["date"], format="%Y.%m.%d")
df["month"] = df["date"].dt.strftime("%b")

# เพิ่มคอลัมน์: วันนี้ลมดีไหม (ดูจาก % ลมสงบ)
df["quality"] = df["calm"].apply(
    lambda x: "GOOD" if x >= 70 else "FAIR" if x >= 50 else "POOR"
)

# เก็บเฉพาะคอลัมน์ที่ใช้
df = df[["date", "month", "calm", "light", "gentle", "quality"]]

df.to_csv("data/processed/silver.csv", index=False)

print(f"Silver: ทำความสะอาดแล้ว {len(df)} แถว")
print(df.head())
