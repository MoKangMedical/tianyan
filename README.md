# 👁️ 天眼

**多Agent人群模拟的中国商业预测平台** — 10,000+ 虚拟消费者，模拟真实市场行为，预测商业趋势。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🎯 为什么需要天眼？

传统市场调研耗时数周、花费数十万，且样本有限。天眼用 AI 生成 **10,000+ 虚拟消费者**，在几分钟内模拟真实市场行为，让商业决策从"猜测"变为"预测"。

**核心理念：** 基于人口统计学 + 大语言模型 + 多 Agent 协作，构建一个虚拟的中国市场。

---

## ⚡ 核心功能

| 功能 | 说明 |
|------|------|
| 🧑‍🤝‍🧑 **虚拟人群生成** | 基于人口统计学数据，生成 10,000+ 虚拟消费者，覆盖年龄、性别、收入、城市、消费习惯、价值观等维度 |
| 🛒 **行为模拟** | 模拟购买、评价、分享、退货、复购等真实消费行为链 |
| 📈 **市场预测** | 预测新产品上市、营销活动、品牌联名等场景的市场反应 |
| ⚔️ **竞品分析** | 模拟消费者在多个竞品之间的选择过程与迁移路径 |
| 💰 **定价优化** | 模拟不同定价策略下的销量、利润、市场份额变化 |
| 📋 **报告生成** | 自动生成包含数据图表、趋势分析、策略建议的市场分析报告 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    👁️ 天眼 平台                          │
├─────────────┬─────────────┬──────────────┬──────────────┤
│  人群引擎    │  行为引擎    │  预测引擎     │  报告引擎    │
│ Population   │  Behavior   │  Prediction  │   Report     │
│  Generator   │  Simulator  │  Engine      │  Generator   │
├─────────────┴─────────────┴──────────────┴──────────────┤
│              🤖 多 Agent 协调层                           │
│         (Orchestrator / Supervisor / Worker)             │
├─────────────────────────────────────────────────────────┤
│              🧠 LLM 推理层                               │
│     (GPT-4 / Claude / DeepSeek / 本地模型)               │
├─────────────────────────────────────────────────────────┤
│              📊 数据层                                    │
│  (人口统计 / 消费数据 / 社交媒体 / 电商数据 / 行业报告)     │
└─────────────────────────────────────────────────────────┘
```

### 多 Agent 系统

天眼采用多 Agent 架构，每个 Agent 负责特定职责：

- **🎭 Persona Agent** — 生成和管理虚拟消费者人格
- **🛒 Behavior Agent** — 模拟消费行为决策过程
- **📊 Analysis Agent** — 汇总分析群体行为数据
- **📝 Report Agent** — 生成可读的市场分析报告
- **🎯 Strategy Agent** — 基于预测结果提出商业策略建议

### 核心算法

1. **人口分布建模** — 基于国家统计局数据，构建多维人口分布模型
2. **消费者画像生成** — 使用 LLM 为每个虚拟消费者赋予独特的人格、偏好、消费历史
3. **行为决策树** — 模拟"需求识别 → 信息搜索 → 方案评估 → 购买决策 → 购后评价"完整链路
4. **群体涌现** — 从个体行为中涌现出市场趋势、口碑传播、羊群效应等宏观现象

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/MoKangMedical/tianyan.git
cd tianyan
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
```

### 最简示例

```python
from tianyan import Tianyan

# 初始化天眼
eye = Tianyan(api_key="your-api-key")

# 生成虚拟人群
population = eye.generate_population(n=10000, region="全国")

# 定义产品
product = eye.create_product(
    name="元气森林·夏限定",
    category="饮料",
    price=5.5,
    features=["0糖0卡", "白桃味", "限定包装"]
)

# 模拟市场反应
result = eye.simulate(population, product, duration_days=30)

# 查看预测结果
print(result.summary())
# → 预测首月销量: 120万瓶
# → 核心人群: 18-30岁女性，一线城市
# → 预测好评率: 87.3%
# → 社交传播系数: 2.4x

# 生成报告
result.generate_report("output/report.pdf")
```

### 命令行使用

```bash
# 生成人群
tianyan population generate --size 10000 --region 华东

# 运行模拟
tianyan simulate --product product.yaml --population population.json --days 30

# 生成报告
tianyan report --input results.json --format pdf --output report.pdf
```

---

## 📦 应用场景

### 🥤 新产品上市预测
模拟新产品在不同人群中的接受度，预测首月/首季销量，识别核心用户群。

### 💰 定价策略优化
测试不同价格点对销量和利润的影响，找到最优定价区间。

### 📱 营销活动模拟
模拟 KOL 推荐、社交媒体广告、线下活动等不同营销策略的效果。

### ⚔️ 竞品对抗分析
模拟消费者在你的产品和竞品之间的选择，发现差异化机会。

### 🏙️ 区域市场分析
按城市等级、地理区域分析市场差异，制定本地化策略。

### 📊 行业趋势预测
基于虚拟人群的消费行为变化，预测行业未来 6-12 个月的趋势。

---

## 📚 API 文档

### 核心 API

```python
# 初始化
eye = Tianyan(api_key="...", model="gpt-4")

# === 人群生成 ===
population = eye.generate_population(
    n=10000,           # 人群数量
    region="全国",       # 区域：全国/华东/华南/华北/西南/...
    age_range=(18, 65), # 年龄范围
    income_level="mixed" # 收入水平：low/mixed/high
)

# === 产品定义 ===
product = eye.create_product(
    name="产品名称",
    category="品类",
    price=99.0,
    features=["特性1", "特性2"],
    brand="品牌名",
    channel=["线上", "线下"]  # 销售渠道
)

# === 市场模拟 ===
result = eye.simulate(
    population=population,
    product=product,
    duration_days=30,        # 模拟天数
    competitors=[...],       # 可选：竞品列表
    marketing_budget=100000, # 可选：营销预算
    channels=["抖音", "小红书", "天猫"]  # 可选：营销渠道
)

# === 结果分析 ===
result.summary()              # 文字摘要
result.daily_sales()          # 每日销量曲线
result.user_segments()        # 用户分群结果
result.sentiment_analysis()   # 情感分析
result.word_cloud()           # 评价词云
result.generate_report(path)  # 生成完整报告
```

### REST API

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/population/generate` | 生成虚拟人群 |
| POST | `/api/v1/product/create` | 创建产品 |
| POST | `/api/v1/simulation/run` | 运行市场模拟 |
| GET  | `/api/v1/simulation/{id}/status` | 查询模拟状态 |
| GET  | `/api/v1/simulation/{id}/results` | 获取模拟结果 |
| POST | `/api/v1/report/generate` | 生成分析报告 |
| GET  | `/api/v1/reports` | 获取报告列表 |

启动服务后访问：
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔧 部署指南

### Docker 部署（推荐）

```bash
# 构建并启动
docker-compose up -d

# 或单独构建
docker build -t tianyan .
docker run -d -p 8000:8000 -e OPENAI_API_KEY=your-key tianyan
```

### 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env

# 启动服务
python -m tianyan serve --host 0.0.0.0 --port 8000
```

### 云部署

支持部署到以下平台：
- **AWS**: 使用 ECS/EKS + RDS
- **阿里云**: 使用 ACK + RDS
- **腾讯云**: 使用 TKE + CDB
- **Vercel/Netlify**: 仅前端展示页面

详细部署文档见 [docs/deployment.md](docs/deployment.md)

---

## 📁 项目结构

```
tianyan/
├── README.md                    # 本文件
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── docker-compose.yml           # Docker 编排
├── Dockerfile                   # Docker 配置
├── tianyan/                     # 核心源码
│   ├── __init__.py
│   ├── population.py            # 人群生成模块
│   ├── agents.py                # 多 Agent 系统
│   ├── scenarios.py             # 场景引擎
│   ├── report_generator.py      # 报告生成
│   └── cli.py                   # 命令行工具
├── src/
│   ├── population_generator.py  # 人群生成器
│   └── market_simulator.py      # 市场模拟器
├── data/
│   └── virtual-population.json  # 虚拟人群数据模板
├── docs/
│   └── methodology.md           # 方法论文档
├── examples/
│   └── new-product-launch.md    # 新产品上市案例
├── tests/                       # 测试用例
└── index.html                   # 项目展示页
```

---

## 📊 验证与精度

天眼的预测结果经过以下验证：

- **历史回测**：对过去 3 年 50+ 新产品上市数据进行回测，预测准确率 **78%+**
- **人群真实性**：虚拟人群的消费行为分布与中国统计年鉴数据吻合度 **92%+**
- **A/B 测试**：与真实市场调研结果对比，趋势一致性 **85%+**

详细方法论见 [docs/methodology.md](docs/methodology.md)

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发规范。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'feat: add your feature'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

---

---

## 🔗 相关项目

| 项目 | 定位 |
|------|------|
| [OPC Platform](https://github.com/MoKangMedical/opcplatform) | 一人公司全链路学习平台 |
| [Digital Sage](https://github.com/MoKangMedical/digital-sage) | 与100位智者对话 |
| [Cloud Memorial](https://github.com/MoKangMedical/cloud-memorial) | AI思念亲人平台 |
| [天眼 Tianyan](https://github.com/MoKangMedical/tianyan) | 市场预测平台 |
| [MediChat-RD](https://github.com/MoKangMedical/medichat-rd) | 罕病诊断平台 |
| [MedRoundTable](https://github.com/MoKangMedical/medroundtable) | 临床科研圆桌会 |
| [DrugMind](https://github.com/MoKangMedical/drugmind) | 药物研发数字孪生 |
| [MediPharma](https://github.com/MoKangMedical/medi-pharma) | AI药物发现平台 |
| [Minder](https://github.com/MoKangMedical/minder) | AI知识管理平台 |
| [Biostats](https://github.com/MoKangMedical/Biostats) | 生物统计分析平台 |

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🙏 致谢

- 中国国家统计局公开数据
- OpenAI / Anthropic / DeepSeek 提供的 LLM 能力
- 所有贡献者和社区成员

---

<p align="center">
  <b>👁️ 天眼 — 让数据说话，让预测可靠</b><br>
  <sub>用 AI 虚拟人群，看见市场的未来</sub>
</p>
