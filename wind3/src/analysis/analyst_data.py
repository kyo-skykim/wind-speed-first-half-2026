# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root
_os.makedirs('reports/data', exist_ok=True)  # รันได้จากทุกที่ใน VS Code
"""สร้าง metrics เชิง BI สำหรับ Data Analyst dashboard -> analyst_data.json"""
import json
import numpy as np, pandas as pd
BANDS=["calm","light","gentle","moderate","fresh","strong"]
df=pd.read_excel("data/raw/Daily_Wind_Speed_Frequency_Merged.xlsx",sheet_name="Daily Data")
df["date"]=pd.to_datetime(df["Date"],format="%Y.%m.%d")
df=df.rename(columns={"A - 3.9knot":"calm","B 4.0 - 7.8knot":"light","C 7.9 - 11.7knot":"gentle",
    "D 11.8 - 15.6knot":"moderate","E 15.7 - 19.4knot":"fresh","F > 19.4knot":"strong","total %":"total"})
df=df.sort_values("date").reset_index(drop=True)
df["month"]=df.date.dt.strftime("%b"); df["mnum"]=df.date.dt.month
df["dow"]=df.date.dt.dayofweek   # 0=Mon
df["quality"]=df.calm.apply(lambda x:"GOOD" if x>=70 else "FAIR" if x>=50 else "POOR")
df["roll7"]=df.calm.rolling(7,min_periods=1).mean().round(2)

def q(s): return df[df.quality==s].shape[0]
calmest=df.loc[df.calm.idxmax()]; windiest=df.loc[df.calm.idxmin()]
mq=df.groupby("mnum").apply(lambda g:(g.quality=="GOOD").mean()*100)
best_m=int(mq.idxmax()); worst_m=int(mq.idxmin())
mname={m:df[df.mnum==m]["month"].iloc[0] for m in df.mnum.unique()}

out={"meta":{
  "n_days":int(len(df)),"date_min":df.date.min().strftime("%Y-%m-%d"),
  "date_max":df.date.max().strftime("%Y-%m-%d"),
  "avg_calm":round(float(df.calm.mean()),1),"median_calm":round(float(df.calm.median()),1),
  "good":q("GOOD"),"fair":q("FAIR"),"poor":q("POOR"),
  "good_pct":round(q("GOOD")/len(df)*100,1),
  "calmest":{"date":calmest.date.strftime("%Y-%m-%d"),"calm":float(calmest.calm)},
  "windiest":{"date":windiest.date.strftime("%Y-%m-%d"),"calm":float(windiest.calm)},
  "best_month":{"m":mname[best_m],"good_pct":round(float(mq[best_m]),1)},
  "worst_month":{"m":mname[worst_m],"good_pct":round(float(mq[worst_m]),1)},
}}
# daily (สำหรับ trend + filter + calendar)
out["daily"]=[{"date":r.date.strftime("%Y-%m-%d"),"m":r.month,"mnum":int(r.mnum),
  "calm":round(float(r.calm),1),"roll7":float(r.roll7),"q":r.quality,
  "light":round(float(r.light),1),"gentle":round(float(r.gentle),1)} for r in df.itertuples()]
# monthly table
g=df.groupby("mnum")
out["monthly"]=[{"m":mname[m],"mnum":int(m),"days":int(len(gg)),
  "avg_calm":round(float(gg.calm.mean()),1),"min_calm":round(float(gg.calm.min()),1),
  "max_calm":round(float(gg.calm.max()),1),
  **{b:round(float(gg[b].mean()),2) for b in BANDS},
  "good":int((gg.quality=="GOOD").sum()),"fair":int((gg.quality=="FAIR").sum()),
  "poor":int((gg.quality=="POOR").sum()),
  "good_pct":round((gg.quality=="GOOD").mean()*100,1)} for m,gg in g]
# distribution histogram of calm
counts,edges=np.histogram(df.calm,bins=[30,40,50,60,70,80,90,100])
out["hist"]={"labels":[f"{int(edges[i])}-{int(edges[i+1])}" for i in range(len(counts))],
             "counts":counts.tolist()}
# quality donut
out["quality"]={"GOOD":q("GOOD"),"FAIR":q("FAIR"),"POOR":q("POOR")}
# day of week avg calm
dows=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
dw=df.groupby("dow").calm.mean().reindex(range(7))
out["dow"]={"labels":dows,"avg_calm":[round(float(x),1) for x in dw.values]}
# top calmest / windiest
out["top_calm"]=[{"date":r.date.strftime("%Y-%m-%d"),"calm":round(float(r.calm),1)}
                 for r in df.nlargest(5,"calm").itertuples()]
out["top_wind"]=[{"date":r.date.strftime("%Y-%m-%d"),"calm":round(float(r.calm),1)}
                 for r in df.nsmallest(5,"calm").itertuples()]
json.dump(out,open("reports/data/analyst_data.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("days",out["meta"]["n_days"],"good%",out["meta"]["good_pct"],
      "best",out["meta"]["best_month"],"worst",out["meta"]["worst_month"])
print("monthly rows",len(out["monthly"]),"hist",out["hist"]["counts"],
      "dow",out["dow"]["avg_calm"])
print("calmest",out["meta"]["calmest"],"windiest",out["meta"]["windiest"])
