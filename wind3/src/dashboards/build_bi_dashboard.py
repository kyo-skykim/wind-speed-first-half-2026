# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))  # cd to project root
_os.makedirs('reports', exist_ok=True)  # รันได้จากทุกที่ใน VS Code
import json
D=json.load(open("reports/data/analyst_data.json",encoding="utf-8"))
DATA=json.dumps(D,ensure_ascii=False)
HTML=r"""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Wind BI Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#0e1726;--card:#16202f;--line:#27374a;--txt:#e7eef6;--mut:#8aa0b6;
--good:#37d39b;--fair:#ffb454;--poor:#ff6b6b;--acc:#4ea3ff;--vio:#b18cff;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font-family:'Segoe UI',Tahoma,sans-serif;line-height:1.5}
.wrap{max-width:1200px;margin:0 auto;padding:26px 20px 60px}
h1{font-size:23px;margin:0} .sub{color:var(--mut);font-size:13px}
.bar-top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:18px}
select{background:var(--card);color:var(--txt);border:1px solid var(--line);
border-radius:8px;padding:8px 12px;font-size:14px}
h2{font-size:16px;margin:30px 0 12px;border-left:4px solid var(--acc);padding-left:10px}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi .v{font-size:24px;font-weight:700}.kpi .l{color:var(--mut);font-size:12px;margin-top:3px}
.kpi .b{font-size:11px;color:var(--mut);margin-top:2px}
.two{grid-template-columns:1.5fr 1fr}.half{grid-template-columns:1fr 1fr}
@media(max-width:820px){.two,.half{grid-template-columns:1fr}}
canvas{max-height:300px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
th{color:var(--mut);font-weight:600}
.pill{padding:1px 8px;border-radius:20px;font-size:11px;font-weight:600}
.foot{color:var(--mut);font-size:12px;margin-top:28px;text-align:center}
tr:hover td{background:#1b2737}
</style></head><body><div class="wrap">
<div class="bar-top">
  <div><h1>📊 Wind BI Dashboard <span class="sub">— Data Analyst view</span></h1>
  <div class="sub" id="period"></div></div>
  <div>เลือกเดือน:&nbsp;<select id="mfilter"></select></div>
</div>
<div class="grid kpis" id="kpis"></div>

<h2>แนวโน้มลมสงบรายวัน (Daily calm % + ค่าเฉลี่ยเคลื่อนที่ 7 วัน)</h2>
<div class="card"><canvas id="trend"></canvas></div>

<h2>เปรียบเทียบรายเดือน</h2>
<div class="grid two">
  <div class="card"><canvas id="mBands"></canvas></div>
  <div class="card"><canvas id="mGood"></canvas></div>
</div>

<h2>การกระจายตัว & สัดส่วนคุณภาพ</h2>
<div class="grid half">
  <div class="card"><canvas id="hist"></canvas></div>
  <div class="card"><canvas id="donut"></canvas></div>
</div>

<h2>รูปแบบรายวันของสัปดาห์ & วันเด่น</h2>
<div class="grid two">
  <div class="card"><canvas id="dow"></canvas></div>
  <div class="card"><div class="sub" style="margin-bottom:6px">5 วันลมสงบสุด / ลมแรงสุด</div>
    <table id="topTbl"></table></div>
</div>

<h2>ตารางสรุปรายเดือน</h2>
<div class="card" style="overflow-x:auto"><table id="mTable"></table></div>

<div class="foot" id="foot"></div>
</div>
<script>
const D=__DATA__;
const C={good:'#37d39b',fair:'#ffb454',poor:'#ff6b6b',acc:'#4ea3ff',vio:'#b18cff',mut:'#8aa0b6',grid:'#27374a'};
Chart.defaults.color=C.mut;Chart.defaults.font.family="'Segoe UI',Tahoma,sans-serif";
Chart.defaults.plugins.legend.labels.boxWidth=12;
const $=id=>document.getElementById(id);
const qcol=q=>q==='GOOD'?C.good:q==='FAIR'?C.fair:C.poor;
$('period').textContent=`${D.meta.n_days} วัน • ${D.meta.date_min} → ${D.meta.date_max}`;

// month filter options
const months=D.monthly.map(m=>m.m);
$('mfilter').innerHTML='<option value="ALL">ทั้งหมด</option>'+months.map(m=>`<option value="${m}">${m}</option>`).join('');

function kpiCards(sel){
  let rows=D.daily, scope='ทั้งช่วง';
  if(sel!=='ALL'){rows=D.daily.filter(d=>d.m===sel);scope=sel;}
  const n=rows.length, avg=(rows.reduce((a,b)=>a+b.calm,0)/n).toFixed(1);
  const good=rows.filter(d=>d.q==='GOOD').length;
  const gpct=(good/n*100).toFixed(1);
  const cards=[
   ['ช่วงข้อมูล',scope==='ทั้งช่วง'?D.meta.n_days+' วัน':scope,scope==='ทั้งช่วง'?'':n+' วัน'],
   ['ลมสงบเฉลี่ย',avg+'%','median รวม '+D.meta.median_calm+'%'],
   ['วัน GOOD',gpct+'%',good+' / '+n+' วัน'],
   ['เดือนดีสุด',D.meta.best_month.m,D.meta.best_month.good_pct+'% GOOD'],
   ['เดือนแย่สุด',D.meta.worst_month.m,D.meta.worst_month.good_pct+'% GOOD'],
   ['วันลมแรงสุด',D.meta.windiest.calm+'%',D.meta.windiest.date],
  ];
  $('kpis').innerHTML=cards.map(c=>`<div class="card kpi"><div class="v">${c[1]}</div><div class="l">${c[0]}</div><div class="b">${c[2]}</div></div>`).join('');
}

let trendChart;
function drawTrend(sel){
  let rows=D.daily; if(sel!=='ALL')rows=D.daily.filter(d=>d.m===sel);
  const lab=rows.map(d=>d.date), calm=rows.map(d=>d.calm), roll=rows.map(d=>d.roll7);
  const pts=rows.map(d=>qcol(d.q));
  const cfg={type:'line',data:{labels:lab,datasets:[
    {label:'calm %',data:calm,borderColor:C.acc,backgroundColor:'transparent',
     pointRadius:sel==='ALL'?0:3,pointBackgroundColor:pts,tension:.2,borderWidth:1.5},
    {label:'เฉลี่ย 7 วัน',data:roll,borderColor:C.vio,backgroundColor:'transparent',
     pointRadius:0,borderWidth:2.5,tension:.3}
  ]},options:{plugins:{legend:{}},scales:{
    y:{suggestedMin:30,suggestedMax:100,title:{display:true,text:'% ลมสงบ'},grid:{color:C.grid}},
    x:{ticks:{maxTicksLimit:10},grid:{display:false}}}}};
  if(trendChart)trendChart.destroy(); trendChart=new Chart($('trend'),cfg);
}

// monthly bands stacked
new Chart($('mBands'),{type:'bar',data:{labels:months,datasets:[
 {label:'calm',data:D.monthly.map(m=>m.calm),backgroundColor:C.good},
 {label:'light',data:D.monthly.map(m=>m.light),backgroundColor:C.acc},
 {label:'gentle',data:D.monthly.map(m=>m.gentle),backgroundColor:C.fair},
 {label:'moderate',data:D.monthly.map(m=>m.moderate),backgroundColor:C.poor},
]},options:{plugins:{title:{display:true,text:'สัดส่วนช่วงลมเฉลี่ย/เดือน (%)'}},
 scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:C.grid}}}}});
// monthly good%
new Chart($('mGood'),{type:'bar',data:{labels:months,datasets:[
 {label:'% วัน GOOD',data:D.monthly.map(m=>m.good_pct),
  backgroundColor:D.monthly.map(m=>m.good_pct>=80?C.good:m.good_pct>=60?C.fair:C.poor)}
]},options:{plugins:{legend:{display:false},title:{display:true,text:'% วันลมดี (GOOD) ต่อเดือน'}},
 scales:{y:{suggestedMax:100,grid:{color:C.grid}},x:{grid:{display:false}}}}});
// histogram
new Chart($('hist'),{type:'bar',data:{labels:D.hist.labels,datasets:[
 {label:'จำนวนวัน',data:D.hist.counts,backgroundColor:C.acc}]},
 options:{plugins:{legend:{display:false},title:{display:true,text:'การกระจายของ % ลมสงบ (จำนวนวัน)'}},
 scales:{y:{grid:{color:C.grid}},x:{grid:{display:false}}}}});
// donut
new Chart($('donut'),{type:'doughnut',data:{labels:['GOOD','FAIR','POOR'],datasets:[
 {data:[D.quality.GOOD,D.quality.FAIR,D.quality.POOR],backgroundColor:[C.good,C.fair,C.poor]}]},
 options:{plugins:{title:{display:true,text:'สัดส่วนคุณภาพลม'}},cutout:'58%'}});
// day of week
new Chart($('dow'),{type:'bar',data:{labels:D.dow.labels,datasets:[
 {label:'calm % เฉลี่ย',data:D.dow.avg_calm,backgroundColor:C.vio}]},
 options:{plugins:{legend:{display:false},title:{display:true,text:'ลมสงบเฉลี่ยตามวันในสัปดาห์'}},
 scales:{y:{suggestedMin:70,suggestedMax:82,grid:{color:C.grid}},x:{grid:{display:false}}}}});
// top table
$('topTbl').innerHTML='<tr><th>ลมสงบสุด</th><th>%</th><th>ลมแรงสุด</th><th>%</th></tr>'+
 D.top_calm.map((c,i)=>{const w=D.top_wind[i];
 return `<tr><td>${c.date}</td><td>${c.calm}</td><td>${w.date}</td><td>${w.calm}</td></tr>`;}).join('');
// monthly table
const cols=[['m','เดือน'],['days','วัน'],['avg_calm','calm เฉลี่ย'],['min_calm','calm ต่ำสุด'],
 ['max_calm','calm สูงสุด'],['good','GOOD'],['fair','FAIR'],['poor','POOR'],['good_pct','% GOOD']];
let th='<tr>'+cols.map(c=>`<th>${c[1]}</th>`).join('')+'</tr>';
let tb=D.monthly.map(m=>'<tr>'+cols.map(c=>{
  let v=m[c[0]]; if(c[0]==='good_pct'){const col=v>=80?C.good:v>=60?C.fair:C.poor;
   v=`<span class="pill" style="background:${col}22;color:${col}">${v}%</span>`;}
  return `<td>${v}</td>`;}).join('')+'</tr>').join('');
$('mTable').innerHTML=th+tb;
$('foot').textContent='ที่มา: Daily_Wind_Speed_Frequency_Merged.xlsx • BI dashboard เชิงพรรณนา (descriptive)';

// init + filter handler
function render(sel){kpiCards(sel);drawTrend(sel);}
$('mfilter').addEventListener('change',e=>render(e.target.value));
render('ALL');
</script></body></html>"""
HTML=HTML.replace("__DATA__",DATA)
open("reports/wind_bi_dashboard.html","w",encoding="utf-8").write(HTML)
print("wrote reports/wind_bi_dashboard.html", len(HTML), "bytes")
