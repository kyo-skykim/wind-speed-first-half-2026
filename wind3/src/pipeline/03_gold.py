# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root  # รันได้จากทุกที่ใน VS Code
"""
Gold = สรุปผลรายเดือน พร้อมเอาไปทำรายงาน/dashboard
"""
import os
import pandas as pd

os.makedirs("data/processed", exist_ok=True)

# อ่านจาก Silver
df = pd.read_csv("data/processed/silver.csv")

# สรุปรายเดือน: เฉลี่ย % ลมแต่ละแบบ + นับวันลมดี
summary = df.groupby("month", sort=False).agg(
    days=("date", "count"),
    avg_calm=("calm", "mean"),
    avg_light=("light", "mean"),
    avg_gentle=("gentle", "mean"),
    good_days=("quality", lambda x: (x == "GOOD").sum()),
).round(2)

# คิด % วันลมดีของเดือนนั้น
summary["good_pct"] = (summary["good_days"] / summary["days"] * 100).round(1)

summary.to_csv("data/processed/gold_monthly.csv")

print("Gold: สรุปรายเดือน")
print(summary)
