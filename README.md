<<<<<<< HEAD
# wind-speed-first-half-2026
=======
# 🌬️ Wind Analytics — End-to-End Data Project

> A compact, end-to-end data project on daily wind-speed data: a **medallion ETL pipeline**, **exploratory analysis**, three **machine-learning tasks** (forecasting, classification, clustering), and two **interactive dashboards**.
>
> โปรเจกต์ data แบบครบวงจรบนข้อมูลความเร็วลมรายวัน: **ETL pipeline แบบ medallion**, **การวิเคราะห์เชิงสำรวจ (EDA)**, งาน **machine learning 3 แบบ** (พยากรณ์, จำแนกประเภท, จัดกลุ่ม) และ **dashboard เชิงโต้ตอบ 2 ตัว**

**Stack:** Python · pandas · scikit-learn · statsmodels · Chart.js
**Roles demonstrated / บทบาทที่แสดง:** Data Engineering · Data Analysis · Data Science

---

## 📌 Overview / ภาพรวม

**EN —** The project ingests a daily wind-speed frequency dataset (151 days, Jan–May 2026), cleans and aggregates it through a Bronze→Silver→Gold pipeline, profiles it, and then builds predictive and unsupervised models. Results are presented in two self-contained HTML dashboards: one for a **Data Analyst** (descriptive BI) and one for a **Data Scientist** (predictive ML).

**TH —** โปรเจกต์นี้นำเข้าข้อมูลความถี่ความเร็วลมรายวัน (151 วัน, ม.ค.–พ.ค. 2026) ทำความสะอาดและสรุปผลผ่าน pipeline แบบ Bronze→Silver→Gold สำรวจข้อมูล แล้วสร้างโมเดลทั้งแบบพยากรณ์และแบบไม่มีผู้สอน ผลลัพธ์นำเสนอผ่าน dashboard HTML 2 ตัว: ตัวหนึ่งสำหรับ **Data Analyst** (BI เชิงพรรณนา) อีกตัวสำหรับ **Data Scientist** (ML เชิงพยากรณ์)

---

## 🗂️ Dataset / ชุดข้อมูล

- **Source file:** `data/raw/Daily_Wind_Speed_Frequency_Merged.xlsx` (sheets: `Daily Data`, `Statistics`)
- **Granularity:** one row per day, 1 Jan – 31 May 2026 (151 rows)
- **Columns:** date + 6 wind-speed bands (by knots) as % of the day, plus a `total %` (always = 100, used as a data-quality check)

| Band | Label | knots |
|---|---|---|
| A | calm | < 3.9 |
| B | light | 4.0–7.8 |
| C | gentle | 7.9–11.7 |
| D | moderate | 11.8–15.6 |
| E | fresh | 15.7–19.4 |
| F | strong | > 19.4 |

A day's **quality** is derived from the calm share: `GOOD ≥ 70%`, `FAIR 50–70%`, `POOR < 50%`.
คุณภาพของแต่ละวันคำนวณจากสัดส่วนลมสงบ: `GOOD ≥ 70%`, `FAIR 50–70%`, `POOR < 50%`

---

## 🏗️ Architecture — Medallion Pipeline / สถาปัตยกรรม

```
data/raw/*.xlsx
      │  01_bronze.py   → ingest raw, no transformation
      ▼
data/processed/bronze.csv
      │  02_silver.py   → clean: rename cols, parse dates, derive quality
      ▼
data/processed/silver.csv
      │  03_gold.py     → aggregate: monthly KPIs for reporting
      ▼
data/processed/gold_monthly.csv
```

- **Bronze / บรอนซ์** — raw ingest, kept as-is for reproducibility
- **Silver / ซิลเวอร์** — cleaned & enriched (typed dates, friendly names, `quality` flag)
- **Gold / โกลด์** — business-ready monthly aggregates

---

## 📁 Project Structure / โครงสร้างโปรเจกต์

```
.
├── data/
│   ├── raw/                  # source Excel (input)
│   └── processed/            # bronze / silver / gold CSVs (generated)
├── src/
│   ├── pipeline/             # 01_bronze, 02_silver, 03_gold  (ETL)
│   ├── analysis/             # analyst_data.py   → BI metrics JSON
│   ├── modeling/             # ds_analysis.py    → forecast + classify + cluster
│   └── dashboards/           # build_bi_dashboard.py / build_ds_dashboard.py
├── reports/
│   ├── data/                 # dashboard_data.json / analyst_data.json (generated)
│   ├── wind_bi_dashboard.html   # Data Analyst dashboard
│   └── wind_ds_dashboard.html   # Data Scientist dashboard
├── docs/                     # extra notes (Thai how-to)
├── requirements.txt
└── README.md
```

> Every script resolves paths from the project root, so it runs the same whether launched from the repo root, an IDE "Run" button, or any working directory.
> ทุกสคริปต์อ้างอิง path จาก root ของโปรเจกต์ จึงรันได้เหมือนกันไม่ว่าจะสั่งจากที่ไหน

---

## 🔬 Methods & Key Results / วิธีการและผลลัพธ์สำคัญ

### 1) Exploratory analysis / การสำรวจข้อมูล
- Calm wind dominates: mean **78.8%** (σ 12.0). Strong/fresh winds are near-zero.
- Clear seasonality: calm share falls **Jan 88% → Apr 70%**, partially recovers in May.
- Day-to-day **persistence** is strong (lag-1 autocorrelation **0.65**) — a key signal for forecasting.
- Quality mix: **GOOD 117 / FAIR 32 / POOR 2** days.
- Validation: computed monthly means match the workbook's own `Statistics` sheet (e.g., Jan 88.1 vs 88.2).

### 2) Forecasting — daily calm % / พยากรณ์ % ลมสงบรายวัน
Backtested four models on the last 31 days (lower RMSE = better):

| Model | RMSE | MAE |
|---|---|---|
| **SARIMAX(1,1,1)** ✅ | **14.57** | best |
| Naive (last value) | 19.75 | |
| Holt (linear trend) | 21.95 | |
| SARIMAX(2,0,1)+trend | 23.38 | |

→ **SARIMAX(1,1,1)** wins, ~**26% lower RMSE than naive**. Forecast for June: calm settles around **~76%**.

### 3) Classification — will tomorrow be GOOD? / พรุ่งนี้จะเป็นวัน GOOD ไหม
- Target: next-day `GOOD` vs `NOT` (no leakage — uses *today's* profile to predict *tomorrow*).
- Model: **RandomForest**, evaluated with **TimeSeriesSplit** (5-fold) → CV accuracy **0.736**.
- **Honest finding:** the ML model only **matches a simple "tomorrow = today" persistence rule (0.736)**. Top features are `calm_3d` and `calm`, confirming that wind quality is highly *persistent* rather than driven by complex patterns. Reporting this transparently is part of good data-science practice.

### 4) Clustering — day archetypes / กลุ่มลักษณะวัน
**KMeans (k = 3)** on the standardized 6-band profile:

| Archetype | Days | Avg calm % |
|---|---|---|
| Very Calm | 62 | ~90 |
| Breezy | 85 | ~72 |
| Windy (gusty) | 4 | ~51 |

Silhouette scores across k are weak (0.43–0.49), indicating the data is more of a **continuum** than sharply separated clusters — `k=3` was chosen for interpretability over a degenerate 2-cluster split.

---

## 📊 Dashboards / แดชบอร์ด

Open the HTML files directly in a browser (data is embedded; only Chart.js loads from CDN).
เปิดไฟล์ HTML ในเบราว์เซอร์ได้เลย (ข้อมูลฝังในไฟล์ โหลดเฉพาะ Chart.js จาก CDN)

- `reports/wind_bi_dashboard.html` — **Data Analyst view:** KPIs, daily trend, monthly comparison, distribution, quality donut, day-of-week pattern, month filter.
- `reports/wind_ds_dashboard.html` — **Data Scientist view:** forecast with confidence band, model comparison, feature importance, confusion matrix, cluster archetypes.

---

## ▶️ How to Run / วิธีรัน

**1. Install dependencies / ติดตั้งไลบรารี**
```bash
pip install -r requirements.txt
```

**2. Run the pipeline + analysis + models / รัน pipeline + วิเคราะห์ + โมเดล**
```bash
python src/pipeline/01_bronze.py
python src/pipeline/02_silver.py
python src/pipeline/03_gold.py
python src/analysis/analyst_data.py
python src/modeling/ds_analysis.py
```

**3. Build the dashboards / สร้างแดชบอร์ด**
```bash
python src/dashboards/build_bi_dashboard.py
python src/dashboards/build_ds_dashboard.py
```

Then open the files in `reports/`. / จากนั้นเปิดไฟล์ในโฟลเดอร์ `reports/`

---

## ⚠️ Limitations / ข้อจำกัด

- Only **5 months** of data — cannot capture full-year seasonality; forecasts are indicative, not production-grade.
- The `POOR` class has only **2 days**, so multi-class quality prediction is unreliable (hence the binary GOOD/NOT framing).
- Single location / single source; no external weather covariates.

มีข้อมูลแค่ 5 เดือน จับฤดูกาลทั้งปีไม่ได้ · คลาส POOR มีแค่ 2 วัน · ข้อมูลจากแหล่งเดียว ยังไม่มีตัวแปรภายนอก — ตัวเลขควรมองเป็นเชิงบ่งชี้

---

## 🧰 Tech Stack
`Python 3` · `pandas` · `scikit-learn` · `statsmodels` · `openpyxl` · `Chart.js`
>>>>>>> f875e31 (Initial commit: wind analytics — medallion pipeline, EDA, ML (forecast/classify/cluster), dashboards)
