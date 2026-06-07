# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root
_os.makedirs('reports/data', exist_ok=True)  # รันได้จากทุกที่ใน VS Code
"""
Data Science pipeline บนข้อมูลลมรายวัน:
  1) Forecast  : พยากรณ์ % ลมสงบ (calm) ล่วงหน้า 30 วัน + backtest
  2) Classify  : ทำนายคุณภาพลม "พรุ่งนี้" (GOOD vs NOT) จากโปรไฟล์ลมวันนี้
  3) Cluster   : จัดกลุ่มวันเป็น archetype ตามสัดส่วนลม 6 ช่วง
ผลทั้งหมด export เป็น dashboard_data.json
"""
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             roc_auc_score, silhouette_score)

BANDS = ["calm","light","gentle","moderate","fresh","strong"]
SRC = "data/raw/Daily_Wind_Speed_Frequency_Merged.xlsx"

df = pd.read_excel(SRC, sheet_name="Daily Data")
df["date"] = pd.to_datetime(df["Date"], format="%Y.%m.%d")
df = df.rename(columns={"A - 3.9knot":"calm","B 4.0 - 7.8knot":"light",
    "C 7.9 - 11.7knot":"gentle","D 11.8 - 15.6knot":"moderate",
    "E 15.7 - 19.4knot":"fresh","F > 19.4knot":"strong","total %":"total"})
df = df.sort_values("date").reset_index(drop=True)
df["month"] = df["date"].dt.strftime("%b")
df["month_num"] = df["date"].dt.month
df["quality"] = df["calm"].apply(lambda x:"GOOD" if x>=70 else "FAIR" if x>=50 else "POOR")

out = {"meta":{
    "n_days": int(len(df)),
    "date_min": df.date.min().strftime("%Y-%m-%d"),
    "date_max": df.date.max().strftime("%Y-%m-%d"),
    "calm_mean": round(float(df.calm.mean()),2),
    "calm_std": round(float(df.calm.std()),2),
    "good_days": int((df.quality=="GOOD").sum()),
    "fair_days": int((df.quality=="FAIR").sum()),
    "poor_days": int((df.quality=="POOR").sum()),
}}
out["history"] = {"dates": df.date.dt.strftime("%Y-%m-%d").tolist(),
                  "calm": df.calm.round(2).tolist()}
out["monthly"] = {
    "months": df.groupby("month_num")["month"].first().tolist(),
    **{b: df.groupby("month_num")[b].mean().round(2).tolist() for b in BANDS},
    "good_pct": (df.groupby("month_num")["quality"]
                 .apply(lambda s:(s=="GOOD").mean()*100).round(1).tolist()),
}

# ===== 1) FORECAST =====
y = df.set_index("date")["calm"].asfreq("D")
H, test_n = 30, 31
train, test = y.iloc[:-test_n], y.iloc[-test_n:]
clamp = lambda a: np.clip(a,0,100)
rmse = lambda a,b: float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
mae  = lambda a,b: float(np.mean(np.abs(np.asarray(a)-np.asarray(b))))
cands = {}
cands["Naive"] = np.repeat(train.iloc[-1], test_n)
try:
    m = ExponentialSmoothing(train, trend="add", seasonal=None,
                             initialization_method="estimated").fit()
    cands["Holt"] = clamp(m.forecast(test_n).values)
except Exception as e: print("Holt fail",e)
try:
    m = SARIMAX(train, order=(1,1,1), enforce_stationarity=False,
                enforce_invertibility=False).fit(disp=False)
    cands["SARIMAX(1,1,1)"] = clamp(m.forecast(test_n).values)
except Exception as e: print("sarimax fail",e)
try:
    m = SARIMAX(train, order=(2,0,1), trend="t", enforce_stationarity=False,
                enforce_invertibility=False).fit(disp=False)
    cands["SARIMAX(2,0,1)+trend"] = clamp(m.forecast(test_n).values)
except Exception as e: print("sarimax2 fail",e)
scores = {k:{"RMSE":round(rmse(test.values,v),2),"MAE":round(mae(test.values,v),2)}
          for k,v in cands.items()}
best = min(scores, key=lambda k: scores[k]["RMSE"])

def fit_full(name, series, h):
    if name=="Naive": return np.repeat(series.iloc[-1],h),None,None
    if name=="Holt":
        mm = ExponentialSmoothing(series, trend="add", seasonal=None,
                                  initialization_method="estimated").fit()
        return clamp(mm.forecast(h).values),None,None
    order = (1,1,1) if "1,1,1" in name else (2,0,1)
    trend = "t" if "trend" in name else "n"
    mm = SARIMAX(series, order=order, trend=trend, enforce_stationarity=False,
                 enforce_invertibility=False).fit(disp=False)
    fc = mm.get_forecast(h); mean = clamp(fc.predicted_mean.values)
    ci = fc.conf_int(alpha=0.2).values
    return mean, clamp(ci[:,0]), clamp(ci[:,1])

fmean,flo,fhi = fit_full(best,y,H)
fdates = pd.date_range(y.index[-1]+pd.Timedelta(days=1), periods=H, freq="D")
out["forecast"] = {
    "model": best, "scores": scores,
    "backtest": {"dates": test.index.strftime("%Y-%m-%d").tolist(),
                 "actual": test.round(2).tolist(),
                 "pred": [round(float(x),2) for x in cands[best]]},
    "future": {"dates": fdates.strftime("%Y-%m-%d").tolist(),
               "mean": [round(float(x),2) for x in fmean],
               "lo": None if flo is None else [round(float(x),2) for x in flo],
               "hi": None if fhi is None else [round(float(x),2) for x in fhi]},
}

# ===== 2) CLASSIFY next-day quality =====
d = df.copy()
d["calm_3d"] = d["calm"].rolling(3, min_periods=1).mean()
d["good_next"] = (d["calm"].shift(-1) >= 70).astype(int)
d = d.iloc[:-1]
feat = ["calm","calm_3d","light","gentle","moderate","month_num"]
X, yb = d[feat].values, d["good_next"].values
clf = RandomForestClassifier(n_estimators=300, max_depth=5,
                             class_weight="balanced", random_state=42)
tscv = TimeSeriesSplit(n_splits=5)
cv_acc, cv_persist = [], []
for tr,te in tscv.split(X):
    clf.fit(X[tr],yb[tr])
    cv_acc.append(accuracy_score(yb[te], clf.predict(X[te])))
    cv_persist.append(accuracy_score(yb[te], (d["calm"].values[te]>=70).astype(int)))
cut = int(len(d)*0.75)
clf.fit(X[:cut], yb[:cut])
pred = clf.predict(X[cut:]); prob = clf.predict_proba(X[cut:])[:,1]; yte = yb[cut:]
persist_pred = (d["calm"].values[cut:]>=70).astype(int)
base_major = np.repeat(int(round(yb[:cut].mean())), len(yte))
out["classify"] = {
    "target":"พรุ่งนี้เป็นวัน GOOD (calm>=70%) หรือไม่",
    "features": feat, "n_train": int(cut), "n_test": int(len(yte)),
    "pos_rate": round(float(yb.mean()),3),
    "model": {"name":"RandomForest",
        "cv_accuracy": round(float(np.mean(cv_acc)),3),
        "accuracy": round(accuracy_score(yte,pred),3),
        "f1": round(f1_score(yte,pred),3),
        "auc": round(roc_auc_score(yte,prob),3) if len(set(yte))>1 else None,
        "cm": confusion_matrix(yte,pred,labels=[1,0]).tolist()},
    "baselines": {"majority_acc": round(accuracy_score(yte,base_major),3),
        "persistence_acc": round(accuracy_score(yte,persist_pred),3),
        "persistence_cv": round(float(np.mean(cv_persist)),3)},
    "importance": {f:round(float(i),3) for f,i in
                   sorted(zip(feat,clf.feature_importances_),key=lambda x:-x[1])},
}

# ===== 3) CLUSTER =====
Z = StandardScaler().fit_transform(df[BANDS].values)
sil = {}
for k in range(2,6):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Z)
    sil[k] = round(float(silhouette_score(Z, km.labels_)),3)
# silhouette อ่อน (0.43-0.49) = ไม่มีโครงสร้างกลุ่มชัด เป็น continuum;
# เลือก k=3 เพราะตีความได้สะอาดสุด (Very Calm / Breezy / Windy) ไม่มี singleton
bestk = 3
km = KMeans(n_clusters=bestk, n_init=10, random_state=42).fit(Z)
df["cluster"] = km.labels_
cent = df.groupby("cluster")[BANDS].mean().round(2)
sizes = df["cluster"].value_counts().sort_index()
def name_arch(row):
    c = row["calm"]
    if c>=85: return "Very Calm"
    if c>=75: return "Calm"
    if c>=65: return "Breezy"
    return "Windy"
labels = {i: name_arch(cent.loc[i]) for i in cent.index}
months_sorted = sorted(df.month_num.unique())
comp = (df.groupby(["cluster","month_num"]).size().unstack(fill_value=0)
        .reindex(columns=months_sorted, fill_value=0))
items = []
for i in cent.index:
    items.append({"id":int(i),"label":labels[i],"size":int(sizes[i]),
        "calm":float(cent.loc[i,"calm"]),"light":float(cent.loc[i,"light"]),
        "gentle":float(cent.loc[i,"gentle"]),"moderate":float(cent.loc[i,"moderate"]),
        "by_month":[int(comp.loc[i,m]) for m in months_sorted]})
out["cluster"] = {"k":int(bestk),"silhouette":sil,
    "months": df.groupby("month_num")["month"].first().tolist(), "items":items}

with open("reports/data/dashboard_data.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

print("FORECAST RMSE:", {k:v["RMSE"] for k,v in scores.items()}, "-> best:", best)
print("June calm mean:", round(float(np.mean(fmean)),1),
      "range", round(float(np.min(fmean)),1),"-",round(float(np.max(fmean)),1))
c=out["classify"]
print("CLASSIFY cv_acc:",c["model"]["cv_accuracy"],"holdout acc:",c["model"]["accuracy"],
      "f1:",c["model"]["f1"],"auc:",c["model"]["auc"],
      "| persistence_cv:",c["baselines"]["persistence_cv"],
      "majority:",c["baselines"]["majority_acc"])
print("importance:", c["importance"])
print("CLUSTER k:", bestk, "silhouette:", sil)
for it in items: print(f"  C{it['id']} {it['label']:10s} n={it['size']:3d} calm={it['calm']}")
print("saved dashboard_data.json")
