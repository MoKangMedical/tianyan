# 👁️ 天眼 (Tianyan) — 中国版商业预测平台

**基于多Agent人群模拟的商业预测引擎**

> 天眼观市，洞察先机。
> 用AI合成人群替代传统调研，72小时完成6个月的市场洞察。

---

## 🎯 一句话

天眼 = Aaru的中国版 —— 砍掉政治预测，深耕商业模拟，合规先行。

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     天眼 Tianyan                              │
├──────────────────┬──────────────────┬────────────────────────┤
│   消费眼 Consumer │   政策眼 Policy   │   市场眼 Market        │
│   产品预测        │   政策影响评估     │   行业趋势预测          │
│   广告优化        │   民意温度计       │   竞品动态              │
│   品牌舆情        │   风险预警         │   投资风向              │
├──────────────────┴──────────────────┴────────────────────────┤
│              多Agent人群模拟引擎 (Simulation Engine)           │
│     人口Agent → 行为Agent → 交互Agent → 汇聚Agent             │
├─────────────────────────────────────────────────────────────┤
│              合成人群工厂 (Synthetic Population)               │
│   统计年鉴 + 电商画像 + 社交图谱 + 消费行为（全合规合成数据）    │
├─────────────────────────────────────────────────────────────┤
│              数据合规层 (Compliance Layer)                     │
│   PIPL合规 + 数安法 + 算法备案 + 数据脱敏 + 审计日志           │
├─────────────────────────────────────────────────────────────┤
│              AI推理层 (Model Provider)                        │
│         MIMO API（无限额度） + Ollama本地 + 可插拔             │
└─────────────────────────────────────────────────────────────┘
```

## ⚡ Quick Start

```python
from tianyan import ConsumerEye, SyntheticPopulation

# 创建合成人群（一线城市25-35岁女性）
population = SyntheticPopulation(
    region="一线城市",
    age_range=(25, 35),
    gender="female",
    size=5000,
)

# 创建消费预测引擎
eye = ConsumerEye(model_provider="mimo")

# 模拟新产品上市反应
result = eye.predict(
    scenario="一款定价299元的国产GLP-1减重产品上市",
    population=population,
    metrics=["购买意愿", "价格敏感度", "渠道偏好"],
)

print(f"预测购买率: {result.purchase_intent:.1%}")
print(f"价格接受度: {result.price_acceptance:.1%}")
print(f"最优渠道: {result.best_channel}")
```

## 📦 三眼产品矩阵

### 消费眼 (Consumer Eye)
- 产品上市预测
- 广告创意测试
- 品牌舆情模拟
- 用户流失预测
- 定价策略优化

### 政策眼 (Policy Eye)
- 政策影响评估（如：集采对药企的影响）
- 民意温度计（政策发布后的社会反应）
- 风险预警系统
- ⚠️ 严格去政治化：不预测人事变动，不触碰敏感话题

### 市场眼 (Market Eye)
- 行业趋势预测
- 竞品动态分析
- 投资风向标
- 供应链风险评估

## 🔒 合规设计

### 数据红线（绝不触碰）
- ❌ 不使用真实个人身份信息（PIPL）
- ❌ 不做政治预测/选举模拟
- ❌ 不做社会动荡/群体事件模拟
- ❌ 不跨境传输数据（数安法）

### 合规机制
- ✅ 100%合成数据驱动（不使用原始个人信息）
- ✅ 算法备案（推荐算法合规）
- ✅ 审计日志（所有模拟可追溯）
- ✅ 数据本地化（服务器在国内）
- ✅ 结果脱敏（输出不含任何个人信息）

## 🆚 与Aaru对比

| 特性 | Aaru | 天眼 |
|------|------|------|
| 估值 | $1B | — |
| 政治预测 | ✅ Dynamo | ❌ 不碰 |
| 商业预测 | ✅ Lumen | ✅ 消费眼 |
| 政务模拟 | ✅ Seraph | ✅ 政策眼（去政治化）|
| AI模型 | GPT/Claude | MIMO（无限额度）|
| 数据合规 | 美国标准 | 中国标准（PIPL+数安法）|
| 市场 | 美国/全球 | 中国 |
| 成本结构 | 重资产（API按量付费）| 轻资产（MIMO无限额度）|

## 💰 商业模式

### 目标客户
1. **品牌方**（核心）：快消、美妆、汽车、医药 → 产品上市预测
2. **广告公司**：奥美、蓝标、华扬 → 广告效果预测
3. **咨询公司**：麦肯锡、贝恩 → 市场进入策略
4. **投资机构**：VC/PE → 行业趋势判断
5. **政务部门**（谨慎）：政策影响评估

### 定价
- 单次模拟：¥5,000-20,000
- 月度订阅：¥50,000-200,000
- 年度框架：¥500,000-2,000,000
- OPC模式：边际成本趋零（MIMO无限额度）

## 🆕 v0.3.0 新增能力

| 模块 | 文件 | 功能 |
|------|------|------|
| 📊 报告生成器 | `report_generator.py` | 麦肯锡级结构化报告（产品上市/市场进入/竞争分析）|
| 💾 数据持久化 | `persistence.py` | SQLite存储模拟历史/预测结果/审计日志 |
| 📡 实时数据 | `realtime_feeds.py` | A股行情/行业新闻/政策法规实时推送 |
| 🏭 行业模板 | `industry_templates.py` | 5个预置场景：GLP-1/保健品/护肤/远程医疗/男性健康 |
| 🧠 Agent升级 | `agents.py` | MIMO LLM推理 + 规则引擎降级 + 批量推理 |
| 🕸️ 社交传播 | `scenarios.py` | 基于图论的小世界网络 + SIR信息扩散 + 意见领袖效应 |

## 🌐 REST API

天眼提供完整的REST API，14个端点覆盖全流程。

### 核心端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/population` | POST | 创建合成人群 |
| `/api/simulate` | POST | 运行通用仿真 |
| `/api/kol` | POST | KOL效果预测 |
| `/api/livestream` | POST | 直播带货预测 |
| `/api/channel` | POST | 电商渠道优化 |
| `/api/seeding` | POST | 小红书种草预测 |

### 高级端点（v0.3.0新增）

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/predict/full` | POST | 完整预测（人群→消费眼→KOL→直播→种草→渠道） |
| `/api/v1/report/generate` | POST | 生成麦肯锡级报告 |
| `/api/v1/templates` | GET | 获取所有行业模板 |
| `/api/v1/template/run` | POST | 用行业模板运行预测 |
| `/api/v1/dashboard` | GET | 仪表盘概览 |
| `/api/v1/compare` | POST | 对比两个产品 |

### 快速调用

```bash
# 完整预测（一个请求搞定所有分析）
curl -X POST http://localhost:8000/api/v1/predict/full \
  -H "Content-Type: application/json" \
  -d '{"product_name":"GLP-1减重针","product_price":399}'

# 生成麦肯锡报告
curl -X POST http://localhost:8000/api/v1/report/generate \
  -H "Content-Type: application/json" \
  -d '{"product_name":"GLP-1减重针","product_price":399}'

# 用GLP-1行业模板
curl -X POST http://localhost:8000/api/v1/template/run \
  -H "Content-Type: application/json" \
  -d '{"template_key":"glp1_weight_loss","product_name":"SlimGuard","product_price":399}'

# 对比两个产品
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{"product_a":"产品A","product_b":"产品B","price_a":299,"price_b":399}'

# 仪表盘概览
curl http://localhost:8000/api/v1/dashboard

# Swagger UI
open http://localhost:8000/docs
```

### 启动

```bash
pip install fastapi uvicorn
cd tianyan && python3 demo_server.py
# 访问 http://localhost:8000
```

## 🗺️ Roadmap

- [x] 架构设计
- [x] 合成人群工厂 v1.0
- [x] 消费眼 MVP
- [x] 政策眼 MVP
- [x] 市场眼 MVP
- [x] 中国特色场景（KOL/直播/电商/小红书）
- [x] 合规层（PIPL/数安法）
- [x] MIMO LLM推理集成
- [x] 基于图论的社交传播模型
- [x] 麦肯锡级报告生成器
- [x] 数据持久化层（SQLite）
- [x] 实时数据集成（A股/新闻/政策）
- [x] 5个行业预置模板
- [ ] 算法备案
- [ ] 首个客户POC
- [ ] 商业化上线

## 📄 License

MIT License
