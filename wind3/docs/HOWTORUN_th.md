# วิธีรัน (ภาษาไทย)

ดูรายละเอียดเต็มใน `README.md` ที่ root ของโปรเจกต์

## สรุปขั้นตอน
```bash
# 1) ติดตั้งไลบรารี (ทำครั้งเดียว)
pip install -r requirements.txt

# 2) รัน pipeline + วิเคราะห์ + โมเดล
python src/pipeline/01_bronze.py     # ดิบ  -> data/processed/bronze.csv
python src/pipeline/02_silver.py     # สะอาด -> data/processed/silver.csv
python src/pipeline/03_gold.py       # สรุป  -> data/processed/gold_monthly.csv
python src/analysis/analyst_data.py  # -> reports/data/analyst_data.json
python src/modeling/ds_analysis.py   # -> reports/data/dashboard_data.json

# 3) สร้างแดชบอร์ด
python src/dashboards/build_bi_dashboard.py   # -> reports/wind_bi_dashboard.html
python src/dashboards/build_ds_dashboard.py   # -> reports/wind_ds_dashboard.html
```

## ปัญหาที่พบบ่อย
- `ModuleNotFoundError` → ยังไม่ได้ `pip install -r requirements.txt` หรือเลือก Python interpreter ผิดใน VS Code (Ctrl+Shift+P → "Python: Select Interpreter")
- ไฟล์ `.html` เปิดด้วยเบราว์เซอร์ ไม่ใช่รันแบบ Python
- ทุกสคริปต์อ้างอิง path จาก root อัตโนมัติ จึงรันจากที่ไหนก็ได้
