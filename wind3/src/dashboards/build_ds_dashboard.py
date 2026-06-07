# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root
_os.makedirs('reports', exist_ok=True)  # รันได้จากทุกที่ใน VS Code
import json
d = json.load(open("reports/data/dashboard_data.json", encoding="utf-8"))
DATA = json.dumps(d, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Wind DS Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root{--bg:#0f1620;--card:#18222e;--line:#283848;--txt:#e6edf3;--mut:#8a9bad;
        --accent:#4ea3ff;--good:#37d39b;--warn:#ffb454;--bad:#ff6b6b;--violet:#b18cff;}
  *{box-sizing:border-box} 
  body{margin:0;background:var(--bg);color:var(--txt);
       font-family:'Segoe UI',Tahoma,sans-serif;line-height:1.5}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:24px;margin:0 0 4px} h2{font-size:18px;margin:34px 0 14px;
     border-left:4px solid var(--accent);padding-left:10px}
  .sub{color:var(--mut);font-size:13px;margin-bottom:8px}
  .grid{display:grid;gap:14px}
  .kpis{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
  .kpi .v{font-size:26px;font-weight:700} .kpi .l{color:var(--mut);font-size:12px;margin-top:2px}
  .two{grid-template-columns:1.6fr 1fr} .three{grid-template-columns:repeat(3,1fr)}
  @media(max-width:820px){.two,.three{grid-template-columns:1fr}}
  canvas{max-height:300px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right}
  th:first-child,td:first-child{text-align:left}
  .pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:600}
  .note{background:#1d2735;border:1px dashed var(--line);border-radius:10px;
        padding:12px 14px;font-size:13px;color:var(--mut);margin-top:10px}
  .note b{color:var(--txt)}
  .cm{display:grid;grid-template-columns:auto 1fr 1fr;gap:6px;font-size:13px;margin-top:6px}
  .cm div{padding:10px;border-radius:8px;text-align:center;background:#1d2735}
  .cm .hd{background:transparent;color:var(--mut);font-weight:600}
  .badge{font-size:11px;color:var(--mut)}
  .arch{display:flex;flex-direction:column;gap:6px}
  .bar{height:8px;border-radius:4px;background:#22303f;overflow:hidden}
  .bar>i{display:block;height:100%}
  .foot{color:var(--mut);font-size:12px;margin-top:30px;text-align:center}
</style>
</head>
<body><div class="wrap">
  <h1>🌬️ Wind Data Science Dashboard</h1>
  <div class="sub" id="period"></div>

  <div class="grid kpis" id="kpis"></div>

  <h2>1 · พยากรณ์ % ลมสงบ ล่วงหน้า 30 วัน (Forecast)</h2>
  <div class="grid two">
    <div class="card"><canvas id="fcChart"></canvas></div>
    <div class="card">
      <div class="sub">เปรียบเทียบโมเดล (backtest เดือนสุดท้าย)</div>
      <table id="fcTable"></table>
      <div class="note" id="fcNote"></div>
    </div>
  </div>

  <h2>2 · แนวโน้มรายเดือน (Seasonality)</h2>
  <div class="grid two">
    <div class="card"><canvas id="monthBands"></canvas></div>
    <div class="card"><canvas id="monthGood"></canvas></div>
  </div>

  <h2>3 · ทำนายคุณภาพลม "พรุ่งนี้" (Classification)</h2>
  <div class="grid three" id="clsKpis"></div>
  <div class="grid two" style="margin-top:14px">
    <div class="card"><canvas id="impChart"></canvas></div>
    <div class="card">
      <div class="sub">Confusion matrix (holdout • แถว=จริง, คอลัมน์=ทำนาย)</div>
      <div class="cm" id="cm"></div>
      <div class="note" id="clsNote"></div>
    </div>
  </div>

  <h2>4 · กลุ่มลักษณะวัน (Clustering archetypes)</h2>
  <div class="grid two">
    <div class="card" id="archCards"></div>
    <div class="card"><canvas id="clChart"></canvas></div>
  </div>

  <div class="foot" id="foot"></div>
</div>
<script>
const D = __DATA__;
const C={accent:'#4ea3ff',good:'#37d39b',warn:'#ffb454',bad:'#ff6b6b',violet:'#b18cff',mut:'#8a9bad',grid:'#283848'};
Chart.defaults.color='#8a9bad'; Chart.defaults.font.family="'Segoe UI',Tahoma,sans-serif";
Chart.defaults.plugins.legend.labels.boxWidth=12;
const $=id=>document.getElementById(id);

// period + KPIs
$('period').textContent=`ข้อมูล ${D.meta.n_days} วัน • ${D.meta.date_min} → ${D.meta.date_max}`;
const kp=[
 ['วันทั้งหมด',D.meta.n_days,''],
 ['% ลมสงบเฉลี่ย',D.meta.calm_mean+'%','σ='+D.meta.calm_std],
 ['วัน GOOD',D.meta.good_days,(100*D.meta.good_days/D.meta.n_days).toFixed(0)+'% ของวัน'],
 ['โมเดล forecast',D.forecast.model,'RMSE '+D.forecast.scores[D.forecast.model].RMSE],
 ['คาดการณ์ มิ.ย.', (D.forecast.future.mean.reduce((a,b)=>a+b,0)/D.forecast.future.mean.length).toFixed(1)+'%','calm เฉลี่ย'],
];
$('kpis').innerHTML=kp.map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div><div class="badge">${k[2]}</div></div>`).join('');

// ---- forecast chart ----
const hN=60, hist=D.history;
const hd=hist.dates.slice(-hN), hc=hist.calm.slice(-hN);
const fd=D.forecast.future.dates, fm=D.forecast.future.mean, flo=D.forecast.future.lo, fhi=D.forecast.future.hi;
const labels=[...hd,...fd];
const pad=arr=>[...Array(hd.length).fill(null),...arr];
const ds=[
 {label:'จริง (calm %)',data:[...hc,...Array(fd.length).fill(null)],borderColor:C.accent,backgroundColor:'transparent',pointRadius:0,tension:.25,borderWidth:2},
 {label:'พยากรณ์',data:pad(fm),borderColor:C.warn,backgroundColor:'transparent',pointRadius:0,borderDash:[5,4],tension:.25,borderWidth:2},
];
if(fhi){ds.push({label:'ช่วงเชื่อมั่น 80%',data:pad(fhi),borderColor:'transparent',backgroundColor:'rgba(255,180,84,.15)',pointRadius:0,fill:'+1'});
        ds.push({label:'_lo',data:pad(flo),borderColor:'transparent',backgroundColor:'rgba(255,180,84,.15)',pointRadius:0,fill:false});}
new Chart($('fcChart'),{type:'line',data:{labels,datasets:ds},
 options:{plugins:{legend:{labels:{filter:i=>!i.text.startsWith('_')}}},
 scales:{y:{title:{display:true,text:'% ลมสงบ'},grid:{color:C.grid}},
         x:{ticks:{maxTicksLimit:8},grid:{display:false}}}}});

// forecast table
let tb='<tr><th>โมเดล</th><th>RMSE</th><th>MAE</th></tr>';
Object.entries(D.forecast.scores).sort((a,b)=>a[1].RMSE-b[1].RMSE).forEach(([k,v])=>{
 const win=k===D.forecast.model?` <span class="pill" style="background:${C.good}22;color:${C.good}">best</span>`:'';
 tb+=`<tr><td>${k}${win}</td><td>${v.RMSE}</td><td>${v.MAE}</td></tr>`;});
$('fcTable').innerHTML=tb;
const naive=D.forecast.scores['Naive'].RMSE, bestr=D.forecast.scores[D.forecast.model].RMSE;
$('fcNote').innerHTML=`<b>${D.forecast.model}</b> ดีกว่าการเดาแบบ Naive ราว <b>${(100*(naive-bestr)/naive).toFixed(0)}%</b> (RMSE ${bestr} vs ${naive}). มิ.ย. คาดว่าลมสงบจะทรงตัวแถว ~76%.`;

// ---- monthly ----
const M=D.monthly;
new Chart($('monthBands'),{type:'bar',data:{labels:M.months,datasets:[
 {label:'calm',data:M.calm,backgroundColor:C.good},
 {label:'light',data:M.light,backgroundColor:C.accent},
 {label:'gentle',data:M.gentle,backgroundColor:C.warn},
 {label:'moderate',data:M.moderate,backgroundColor:C.bad},
]},options:{plugins:{title:{display:true,text:'สัดส่วนช่วงลมเฉลี่ย/เดือน (%)'}},
 scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:C.grid}}}}});
new Chart($('monthGood'),{type:'line',data:{labels:M.months,datasets:[
 {label:'% วัน GOOD',data:M.good_pct,borderColor:C.violet,backgroundColor:'rgba(177,140,255,.15)',fill:true,tension:.3,borderWidth:2,pointRadius:4}
]},options:{plugins:{title:{display:true,text:'% วันลมดี (GOOD) ต่อเดือน'}},
 scales:{y:{suggestedMin:50,suggestedMax:100,grid:{color:C.grid}},x:{grid:{display:false}}}}});

// ---- classification ----
const cl=D.classify, mo=cl.model, bl=cl.baselines;
const ck=[
 ['Model CV accuracy',(mo.cv_accuracy*100).toFixed(1)+'%','RandomForest (5-fold time CV)'],
 ['Persistence baseline',(bl.persistence_cv*100).toFixed(1)+'%','กฎ "พรุ่งนี้=วันนี้"'],
 ['ROC-AUC',mo.auc??'—','holdout'],
];
$('clsKpis').innerHTML=ck.map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div><div class="badge">${k[2]}</div></div>`).join('');
// importance
const imp=cl.importance, ik=Object.keys(imp), iv=Object.values(imp);
new Chart($('impChart'),{type:'bar',data:{labels:ik,datasets:[{label:'Feature importance',data:iv,backgroundColor:C.accent}]},
 options:{indexAxis:'y',plugins:{title:{display:true,text:'ความสำคัญของฟีเจอร์'},legend:{display:false}},
 scales:{x:{grid:{color:C.grid}},y:{grid:{display:false}}}}});
// confusion matrix [[TP,FN],[FP,TN]] rows=actual GOOD/NOT
const cm=mo.cm;
$('cm').innerHTML=`<div class="hd"></div><div class="hd">ทาย GOOD</div><div class="hd">ทาย NOT</div>
 <div class="hd">จริง GOOD</div><div style="background:${C.good}33">${cm[0][0]}</div><div>${cm[0][1]}</div>
 <div class="hd">จริง NOT</div><div>${cm[1][0]}</div><div style="background:${C.good}33">${cm[1][1]}</div>`;
$('clsNote').innerHTML=`<b>ข้อค้นพบสำคัญ:</b> โมเดล ML ทำได้ ~เท่ากับกฎง่าย ๆ "พรุ่งนี้เหมือนวันนี้" (ทั้งคู่ ~74%). 
 ฟีเจอร์ที่สำคัญสุดคือ <b>calm_3d / calm</b> ของวันนี้ → คุณภาพลมมี <b>ความต่อเนื่องสูง (persistent)</b> นี่คือสัญญาณพยากรณ์ที่แท้จริง ไม่ใช่ pattern ซับซ้อน`;

// ---- clustering ----
const cu=D.cluster, pal={'Very Calm':C.good,'Calm':'#7fd3ff','Breezy':C.warn,'Windy':C.bad};
$('archCards').innerHTML='<div class="sub">3 กลุ่มลักษณะวัน (KMeans, k=3)</div>'+cu.items.map(it=>{
 const col=pal[it.label]||C.accent;
 return `<div class="arch" style="margin-bottom:12px">
   <div><span class="pill" style="background:${col}22;color:${col}">${it.label}</span>
   <span class="badge"> ${it.size} วัน • calm ${it.calm}% / light ${it.light}% / gentle ${it.gentle}%</span></div>
   <div class="bar"><i style="width:${it.calm}%;background:${col}"></i></div></div>`;}).join('');
// stacked bar: cluster composition by month
new Chart($('clChart'),{type:'bar',data:{labels:cu.months,datasets:cu.items.map(it=>({
   label:it.label,data:it.by_month,backgroundColor:pal[it.label]||C.accent}))},
 options:{plugins:{title:{display:true,text:'จำนวนวันแต่ละกลุ่ม ต่อเดือน'}},
 scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:C.grid}}}}});

$('foot').textContent='สร้างจาก Daily_Wind_Speed_Frequency_Merged.xlsx • Forecast: SARIMAX • Classify: RandomForest • Cluster: KMeans';
</script>
</body></html>"""

HTML = HTML.replace("__DATA__", DATA)
open("reports/wind_ds_dashboard.html","w",encoding="utf-8").write(HTML)
print("wrote reports/wind_ds_dashboard.html", len(HTML), "bytes")
