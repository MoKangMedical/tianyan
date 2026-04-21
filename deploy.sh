#!/bin/bash
# Tianyan 一键部署脚本
# 用法: bash deploy.sh [port]

PORT=${1:-8095}
echo "👁️ 天眼 Tianyan 部署中..."
echo "   端口: $PORT"

python3 -c "import fastapi" 2>/dev/null || pip3 install fastapi uvicorn

cd "$(dirname "$0")"
echo "   启动服务..."
python3 -m uvicorn demo_server:app --host 0.0.0.0 --port $PORT &
sleep 2

if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "✅ 天眼 Tianyan 已启动: http://localhost:$PORT"
    echo "   API文档: http://localhost:$PORT/docs"
else
    echo "⚠️ 启动中，请稍候..."
fi
