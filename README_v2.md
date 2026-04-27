# 👁️ 天眼 Tianyan v2.0

**多Agent人群模拟的中国商业预测平台** — 10,000+ 虚拟消费者，模拟真实市场行为，预测商业趋势。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-152%20passed-brightgreen.svg)](tests/)
[![API](https://img.shields.io/badge/API-20%20endpoints-purple.svg)](docs/)

---

## 🚀 快速开始

### 方式一：命令行直接使用

```bash
# 安装依赖
pip install -r requirements.txt

# 产品预测
python cli_v2.py predict --product "元气森林" --price 5.5 --category 饮料

# 对话式预测
python cli_v2.py conversation --interactive

# 查看系统状态
python cli_v2.py status
```

### 方式二：启动 API 服务器

```bash
# 注册用户
python cli_v2.py register --name "张三" --email "zhangsan@example.com" --role free

# 启动服务器
python cli_v2.py server --port 8000

# 访问 API 文档
open http://localhost:8000/docs
```

### 方式三：Docker 部署

```bash
# 构建并启动
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

---

## 📊 核心功能

| 功能 | 说明 | API |
|------|------|-----|
| 🧑‍🤝‍🧑 合成人群 | 基于人口统计学生成虚拟消费者 | `POST /api/v2/population` |
| 🛒 产品预测 | 模拟产品上市的市场反应 | `POST /api/v2/predict` |
| 💬 对话式预测 | 多轮对话收集信息并预测 | `POST /api/v2/conversation` |
| 📈 KOL效果 | 预测不同KOL的带货效果 | `POST /api/v2/kol` |
| ⚔️ AB对比 | 两个产品的市场竞争力对比 | `POST /api/v2/compare` |
| 📊 历史查询 | 查看历史预测记录 | `GET /api/v2/predictions` |

---

## 🔑 API 认证

### 获取 API Key

```bash
# 命令行注册
python cli_v2.py register --name "你的名字" --email "your@email.com"

# 或调用 API
curl -X POST http://localhost:8000/api/v2/register \
  -H "Content-Type: application/json" \
  -d '{"name": "你的名字", "email": "your@email.com"}'
```

### 使用 API Key

```bash
curl -X POST http://localhost:8000/api/v2/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ty_your_api_key_here" \
  -d '{
    "product_name": "元气森林",
    "price": 5.5,
    "category": "饮料",
    "channels": ["天猫", "抖音"],
    "population_size": 2000
  }'
```

### 配额限制

| 角色 | 每日限额 | 适用场景 |
|------|---------|---------|
| 免费 | 50次 | 个人测试 |
| Pro | 500次 | 小团队 |
| Enterprise | 10,000次 | 企业客户 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    天眼 v2.0 架构                         │
├─────────────────────┬───────────────────────────────────┤
│  CLI工具             │  REST API服务器                    │
│  cli_v2.py          │  server.py                        │
├─────────────────────┴───────────────────────────────────┤
│  核心引擎层                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 人群引擎  │ │ 行为引擎  │ │ 预测引擎  │ │ 报告引擎  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│  LLM适配层                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ DeepSeek │ │   MIMO   │ │  OpenAI  │ │   Mock   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│  数据集成层                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 国家统计局│ │ A股数据   │ │ 新闻RSS  │ │ 政策数据  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│  持久化层                                                │
│  SQLite + JSON + 文件系统                                │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
tianyan/
├── server.py              # 生产级API服务器
├── cli_v2.py              # 命令行工具
├── demo_server.py         # 演示服务器
├── docker-compose.prod.yml # Docker部署
├── Dockerfile.prod        # 生产环境镜像
├── tianyan/               # 核心源码
│   ├── __init__.py
│   ├── population.py      # 人群生成
│   ├── agents.py          # 多Agent系统
│   ├── scenarios.py       # 场景引擎
│   ├── products.py        # 三眼产品矩阵
│   ├── llm_adapter.py     # LLM统一适配器
│   ├── data_integration.py # 数据集成层
│   ├── conversation.py    # 对话式预测
│   ├── opc_integration.py # OPC平台集成
│   ├── report_generator.py # 报告生成
│   ├── data_sources.py    # 数据源适配器
│   ├── realtime_feeds.py  # 实时数据
│   ├── persistence.py     # 持久化层
│   └── compliance.py      # 合规检查
├── tests/                 # 测试用例 (152个)
├── cases/                 # 案例报告 (3个)
│   ├── medislim/
│   ├── lumiglow/
│   └── clouddoc/
├── index.html             # GitHub Pages
├── assets/                # 前端资源
└── docs/                  # 文档
```

---

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_llm_adapter.py -v

# 查看测试覆盖率
python -m pytest tests/ --tb=short
```

---

## 🔧 配置

### 环境变量

```bash
# LLM配置
export TIANYAN_LLM_PROVIDER=deepseek  # deepseek/mimo/openai/mock
export DEEPSEEK_API_KEY=sk-your-key

# 服务器配置
export TIANYAN_HOST=0.0.0.0
export TIANYAN_PORT=8000
export DEBUG=false

# 数据库
export TIANYAN_DB_PATH=tianyan.db
```

### 配置文件

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

---

## 📈 使用示例

### Python SDK

```python
from tianyan import ConsumerEye, SyntheticPopulation

# 生成人群
pop = SyntheticPopulation(size=5000, region="全国")

# 预测产品
eye = ConsumerEye()
result = eye.predict_product_launch(
    product_name="元气森林·夏限定",
    price=5.5,
    category="饮料",
    selling_point="0糖0卡",
    channels=["天猫", "抖音"],
    target_population=pop,
)

print(f"置信度: {result.confidence:.1%}")
print(f"建议: {result.recommendations}")
```

### 命令行

```bash
# 快速预测
python cli_v2.py predict \
  --product "元气森林" \
  --price 5.5 \
  --category 饮料 \
  --channels 天猫 抖音 \
  --population 2000

# 对话式预测
python cli_v2.py conversation --interactive
```

### REST API

```bash
# 预测
curl -X POST http://localhost:8000/api/v2/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ty_your_key" \
  -d '{"product_name": "元气森林", "price": 5.5, "category": "饮料"}'

# 查询历史
curl http://localhost:8000/api/v2/predictions \
  -H "X-API-Key: ty_your_key"
```

---

## 🌐 部署

### 本地部署

```bash
python cli_v2.py server --port 8000
```

### Docker 部署

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 云部署

支持部署到：
- AWS ECS/EKS
- 阿里云 ACK
- 腾讯云 TKE
- Render / Railway

---

## 📚 文档

- [API文档](http://localhost:8000/docs) - Swagger UI
- [方法论文档](docs/methodology.md)
- [商业计划](docs/business_plan.md)
- [部署指南](docs/deployment.md)

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License

---

<p align="center">
  <b>👁️ 天眼 — 让数据说话，让预测可靠</b><br>
  <sub>用 AI 虚拟人群，看见市场的未来</sub>
</p>
