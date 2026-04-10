# Changelog

All notable changes to Tianyan will be documented in this file.

## [1.0.0] - 2026-04-10

### Added
- **14个REST API端点**：完整预测/麦肯锡报告/行业模板/仪表盘/对比分析
- **114个测试**：100%核心功能覆盖，数据源/API/集成测试
- **Docker部署**：Dockerfile + docker-compose.yml + GitHub Actions CI
- **pyproject.toml**：现代Python打包配置
- **data_sources.py修复**：语法错误修复，async数据获取
- **交互Demo**：Landing Page展示API端点和curl示例
- **算法备案材料**：docs/algorithm_filing.md
- **5个行业预置模板**：GLP-1/保健品/护肤/远程医疗/男性健康
- **data_sources测试**：15个新测试覆盖数据源模块
- **demo_server测试**：19个新测试覆盖所有API端点

### Changed
- 版本号统一为 v1.0.0
- demo_server增加限流/错误处理中间件
- README新增REST API文档

## [0.3.0] - 2026-04-10

### Added
- Demo Server从8端点扩展到14端点
- 完整预测端点 `/api/v1/predict/full`
- 麦肯锡报告生成端点 `/api/v1/report/generate`
- 行业模板端点 `/api/v1/templates` + `/api/v1/template/run`
- 仪表盘端点 `/api/v1/dashboard`
- 对比分析端点 `/api/v1/compare`
- 38个新测试（报告生成/持久化/行业模板/MIMO适配器/集成）

## [0.2.0] - 2026-04-08

### Added
- 消费眼/政策眼/市场眼三眼产品
- 中国特色场景（KOL/直播/电商/小红书）
- PIPL/数安法合规层
- 麦肯锡级报告生成器
- 数据持久化层（SQLite）
- 实时数据集成
- 5个行业预置模板

## [0.1.0] - 2026-04-06

### Added
- 初始版本：合成人群工厂v1.0
- 基础仿真引擎
- 40个核心测试
