# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root  # รันได้จากทุกที่ใน VS Code
"""
Bronze = เก็บข้อมูลดิบ ไม่แก้ค่าอะไร แค่อ่านเข้ามาแล้วบันทึกไว้
"""
import os
import pandas as pd

# สร้างโฟลเดอร์ output ถ้ายังไม่มี
os.makedirs("data/processed", exist_ok=True)

# อ่านไฟล์ต้นทาง
df = pd.read_excel("data/raw/Daily_Wind_Speed_Frequency_Merged.xlsx", sheet_name="Daily Data")

# บันทึกเป็นไฟล์ Bronze (เก็บดิบไว้เผื่อต้องใช้ใหม่)
df.to_csv("data/processed/bronze.csv", index=False)

print(f"Bronze: เก็บข้อมูลดิบ {len(df)} แถว")
print(df.head())
