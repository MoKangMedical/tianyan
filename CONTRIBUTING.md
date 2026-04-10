# Contributing to Tianyan

感谢你对天眼平台的兴趣！

## 开发环境

```bash
git clone https://github.com/MoKangMedical/tianyan.git
cd tianyan
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## 代码规范

- Python 3.11+，使用类型注解
- 所有新功能必须有测试
- 测试覆盖率达到80%以上
- 遵循PEP 8代码风格

## 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
test: 测试相关
refactor: 重构
```

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_demo_server.py -v

# 带覆盖率
python -m pytest tests/ --cov=tianyan --cov-report=html
```

## 部署

```bash
# Docker
docker-compose up -d

# 手动
python demo_server.py
```

## 许可证

MIT License
