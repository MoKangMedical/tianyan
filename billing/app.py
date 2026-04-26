"""天眼 Tianyan — 商业洞察报告付费服务"""
from flask import Flask, render_template_string, jsonify, request
import json, os, time
from datetime import datetime

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(__file__), "reports.json")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f: return json.load(f)
    return {"orders": [], "subscribers": {}, "revenue": 0}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, ensure_ascii=False, indent=2)

@app.before_request
def ensure_db():
    if not hasattr(app, '_db'): app._db = load_db()
def get_db(): return app._db
def commit(): save_db(app._db)

REPORT_TYPES = [
    {"id": "market-entry", "name": "市场进入分析", "icon": "🚀", "price": 3000, "desc": "新市场/新品类的进入可行性分析，包含市场规模/竞争格局/进入策略"},
    {"id": "competitor", "name": "竞品深度分析", "icon": "⚔️", "price": 2000, "desc": "指定竞品的商业模式/产品策略/定价/渠道/优劣势全景"},
    {"id": "consumer-insight", "name": "消费者洞察", "icon": "👥", "price": 2500, "desc": "目标人群画像/需求分析/购买决策/渠道偏好/价格敏感度"},
    {"id": "product-launch", "name": "新品上市预测", "icon": "📦", "price": 3500, "desc": "新产品上市后的市场接受度/销量预测/定价优化/渠道策略"},
    {"id": "industry-trend", "name": "行业趋势报告", "icon": "📈", "price": 2000, "desc": "行业发展方向/技术趋势/政策影响/投资机会"},
    {"id": "pricing-optimization", "name": "定价策略优化", "icon": "💰", "price": 2500, "desc": "基于需求弹性和竞品分析的最优定价方案"},
]

SUBSCRIPTION_PLANS = [
    {"name": "单次报告", "price": "¥2,000-3,500", "desc": "按需购买，即买即出"},
    {"name": "月度订阅", "price": "¥10,000/月", "desc": "每月4份报告，节省50%"},
    {"name": "年度会员", "price": "¥80,000/年", "desc": "不限量报告 + 专属分析师"},
]

@app.route("/")
def index():
    return render_template_string("""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>天眼 Tianyan — AI商业洞察</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,sans-serif;background:#f5f7fa;color:#333;max-width:800px;margin:0 auto;padding:20px}
.hdr{background:linear-gradient(135deg,#1565c0,#0d47a1);color:#fff;padding:24px;border-radius:14px;text-align:center;margin-bottom:20px}
.hdr h1{font-size:22px}.hdr p{font-size:13px;opacity:.8;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:20px}
.card{background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.card h3{font-size:14px;color:#1565c0;margin-bottom:4px}
.card .price{font-size:22px;font-weight:800;color:#e65100;margin:6px 0}
.card .desc{font-size:12px;color:#666;line-height:1.6}
.card .btn{display:block;width:100%;padding:10px;background:#1565c0;color:#fff;border:none;border-radius:8px;cursor:pointer;margin-top:10px;font-size:13px}
.section{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.05);margin-bottom:20px}
.section h2{font-size:15px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #eee}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;font-size:13px;border-bottom:1px solid #f0f0f0}
th{background:#fafafa}
.sub-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.sub-card{background:#e3f2fd;border-radius:10px;padding:14px;text-align:center}
.sub-card .name{font-weight:700;font-size:14px}.sub-card .price{font-size:18px;font-weight:800;color:#1565c0;margin:6px 0}
.sub-card .desc{font-size:11px;color:#666}
select,input{width:100%;padding:8px;border:1px solid #ddd;border-radius:8px;margin:4px 0 8px}
.btn-main{padding:10px 20px;background:#1565c0;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px}
.compare{font-size:13px;line-height:2;color:#555}
</style></head><body>
<div class="hdr">
  <h1>👁️ 天眼 Tianyan</h1>
  <p>AI商业洞察平台 · 72小时完成6个月市场洞察 · 按报告付费</p>
</div>

<div class="section">
  <h2>🆚 传统调研 vs 天眼AI</h2>
  <div class="compare">
    传统方式：请咨询公司 → 6-8周 → ¥50-100万/份<br>
    <strong>天眼AI：在线提交需求 → 72小时 → ¥2,000-3,500/份</strong><br>
    成本降低99%，速度提升20倍，质量可比肩麦肯锡
  </div>
</div>

<div class="grid">
{% for r in reports %}
<div class="card">
  <h3>{{ r.icon }} {{ r.name }}</h3>
  <div class="price">¥{{ r.price }}</div>
  <div class="desc">{{ r.desc }}</div>
  <button class="btn" onclick="orderReport('{{ r.id }}')">立即购买</button>
</div>
{% endfor %}
</div>

<div class="section">
  <h2>📋 订阅方案</h2>
  <div class="sub-grid">
  {% for s in subs %}
  <div class="sub-card">
    <div class="name">{{ s.name }}</div>
    <div class="price">{{ s.price }}</div>
    <div class="desc">{{ s.desc }}</div>
  </div>
  {% endfor %}
  </div>
</div>

<div class="section">
  <h2>🎯 目标客户</h2>
  <table>
    <tr><th>客户类型</th><th>典型需求</th><th>付费能力</th></tr>
    <tr><td>品牌方市场部</td><td>竞品分析/消费者洞察</td><td>¥2-5K/份</td></tr>
    <tr><td>咨询公司</td><td>数据支撑/快速验证</td><td>月度订阅¥1万</td></tr>
    <tr><td>投资机构</td><td>行业研究/尽调辅助</td><td>年度¥8万</td></tr>
    <tr><td>创业公司</td><td>市场验证/BP数据</td><td>单次¥2-3K</td></tr>
  </table>
</div>

<div class="section">
  <h2>📊 下单</h2>
  <label>公司名称</label>
  <input id="company" placeholder="输入公司名称">
  <label>报告类型</label>
  <select id="reportType">
    {% for r in reports %}<option value="{{ r.id }}">{{ r.icon }} {{ r.name }} — ¥{{ r.price }}</option>{% endfor %}
  </select>
  <label>分析对象</label>
  <input id="target" placeholder="如：GLP-1减重市场 / 某竞品公司">
  <button class="btn-main" onclick="order()">提交需求</button>
  <div id="result" style="display:none;margin-top:12px;padding:12px;background:#e3f2fd;border-radius:8px;font-size:13px"></div>
</div>

<script>
function orderReport(id){document.getElementById('reportType').value=id;document.getElementById('company').focus()}
async function order(){
  const company=document.getElementById('company').value;
  const type=document.getElementById('reportType').value;
  const target=document.getElementById('target').value;
  if(!company||!target){alert('请填写完整信息');return;}
  const res=await fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({company,type,target})});
  const data=await res.json();
  document.getElementById('result').style.display='block';
  document.getElementById('result').innerHTML=`✅ 订单已提交！<br>订单号：${data.order_id}<br>报告：${data.report_name}<br>价格：¥${data.price}<br>预计72小时内交付`;
}
</script>
</body></html>""", reports=REPORT_TYPES, subs=SUBSCRIPTION_PLANS)

@app.route("/api/order", methods=["POST"])
def api_order():
    data = request.json
    report_type = data.get("type", "market-entry")
    report = next((r for r in REPORT_TYPES if r["id"] == report_type), REPORT_TYPES[0])
    db = get_db()
    order_id = f"TY{int(time.time())}"
    db["orders"].append({"id": order_id, "company": data.get("company"), "type": report_type, "target": data.get("target"), "price": report["price"], "created": datetime.now().isoformat()})
    db["revenue"] = db.get("revenue", 0) + report["price"]
    commit()
    return jsonify({"order_id": order_id, "report_name": report["name"], "price": report["price"]})

@app.route("/api/reports")
def api_reports(): return jsonify(REPORT_TYPES)

@app.route("/api/stats")
def api_stats():
    db = get_db()
    return jsonify({"orders": len(db["orders"]), "total_revenue": db.get("revenue", 0)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
