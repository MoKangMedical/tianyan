"""
天眼生产级服务器 — 完整闭环API

功能:
- 用户认证 (API Key)
- 异步任务队列
- 结果持久化
- 实时状态查询
- Webhook回调
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    PolicyEye,
    MarketEye,
    ChineseScenarioEngine,
    ComplianceChecker,
    get_llm,
    reset_llm,
)
from tianyan.persistence import PersistenceLayer
from tianyan.conversation import ConversationEngine
from tianyan.opc_integration import OPCIntegration

# ============================================================
# 配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tianyan.production")

DB_PATH = os.environ.get("TIANYAN_DB_PATH", "tianyan_production.db")
API_KEYS_PATH = Path("api_keys.json")

# ============================================================
# 用户系统
# ============================================================

class UserRole(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

def load_api_keys() -> dict[str, dict]:
    if API_KEYS_PATH.exists():
        return json.loads(API_KEYS_PATH.read_text())
    return {}

def save_api_keys(keys: dict[str, dict]):
    API_KEYS_PATH.write_text(json.dumps(keys, indent=2, ensure_ascii=False))

def generate_api_key() -> str:
    return f"ty_{secrets.token_hex(24)}"

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> dict:
    """验证API Key，返回用户信息。"""
    if not x_api_key:
        # 免费用户限制
        return {"role": "anonymous", "name": "anonymous", "daily_limit": 10}

    keys = load_api_keys()
    if x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    user = keys[x_api_key]
    # 检查每日限额
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get("last_date") != today:
        user["last_date"] = today
        user["daily_count"] = 0
        save_api_keys(keys)

    limits = {"free": 50, "pro": 500, "enterprise": 10000}
    daily_limit = limits.get(user.get("role", "free"), 50)

    if user.get("daily_count", 0) >= daily_limit:
        raise HTTPException(status_code=429, detail="Daily limit exceeded")

    user["daily_limit"] = daily_limit
    return user

def increment_usage(api_key: str):
    keys = load_api_keys()
    if api_key in keys:
        keys[api_key]["daily_count"] = keys[api_key].get("daily_count", 0) + 1
        save_api_keys(keys)

# ============================================================
# 任务系统
# ============================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# 内存任务存储 (生产环境用Redis)
_tasks: dict[str, dict] = {}

def create_task(task_type: str, params: dict) -> str:
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        "id": task_id,
        "type": task_type,
        "status": TaskStatus.PENDING,
        "params": params,
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    return task_id

def update_task(task_id: str, status: TaskStatus, result: Any = None, error: str = None):
    if task_id in _tasks:
        _tasks[task_id]["status"] = status
        _tasks[task_id]["result"] = result
        _tasks[task_id]["error"] = error
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            _tasks[task_id]["completed_at"] = datetime.now().isoformat()

def get_task(task_id: str) -> Optional[dict]:
    return _tasks.get(task_id)

# ============================================================
# 请求模型
# ============================================================

class RegisterRequest(BaseModel):
    name: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    role: str = Field(default="free", description="角色: free/pro/enterprise")

class PopulationRequest(BaseModel):
    size: int = Field(default=1000, ge=10, le=50000)
    region: str = Field(default="全国")
    age_min: int = Field(default=18)
    age_max: int = Field(default=65)

class PredictRequest(BaseModel):
    product_name: str = Field(..., description="产品名称")
    price: float = Field(..., ge=0, description="价格")
    category: str = Field(..., description="品类")
    selling_point: str = Field(default="", description="卖点")
    channels: list[str] = Field(default=["线上"], description="渠道")
    population_size: int = Field(default=1000, ge=100, le=10000)
    async_mode: bool = Field(default=False, description="异步执行")

class ConversationRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: str = Field(default="", description="会话ID")

class KOLRequest(BaseModel):
    product_name: str
    product_price: float
    kol_type: str = Field(default="头部主播")
    population_size: int = Field(default=1000)

class CompareRequest(BaseModel):
    product_a: dict = Field(..., description="产品A参数")
    product_b: dict = Field(..., description="产品B参数")
    population_size: int = Field(default=1000)

# ============================================================
# 全局实例
# ============================================================

_persistence: Optional[PersistenceLayer] = None
_conversations: dict[str, ConversationEngine] = {}
_opc: Optional[OPCIntegration] = None

def get_persistence() -> PersistenceLayer:
    global _persistence
    if _persistence is None:
        _persistence = PersistenceLayer(DB_PATH)
    return _persistence

def get_conversation(session_id: str) -> ConversationEngine:
    if session_id not in _conversations:
        _conversations[session_id] = ConversationEngine()
    return _conversations[session_id]

def get_opc() -> OPCIntegration:
    global _opc
    if _opc is None:
        _opc = OPCIntegration()
    return _opc

# ============================================================
# 应用
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("天眼生产服务器启动")
    db = get_persistence()
    logger.info(f"数据库: {DB_PATH}")
    yield
    logger.info("天眼生产服务器关闭")

app = FastAPI(
    title="天眼 Tianyan Production API",
    description="多Agent人群模拟的中国商业预测平台",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API 端点
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """API文档首页。"""
    return """<!DOCTYPE html>
<html><head><title>天眼 Tianyan API v2.0</title>
<style>body{font-family:system-ui;max-width:800px;margin:40px auto;padding:20px;background:#0a0a1a;color:#e0e0e0;}
h1{color:#818cf8;}a{color:#a78bfa;}code{background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;}
.endpoint{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:16px;margin:12px 0;}</style>
</head><body>
<h1>👁️ 天眼 Tianyan API v2.0</h1>
<p>多Agent人群模拟的中国商业预测平台</p>
<h2>核心端点</h2>
<div class="endpoint"><code>POST /api/v2/predict</code> — 产品上市预测</div>
<div class="endpoint"><code>POST /api/v2/predict/async</code> — 异步预测(大人群)</div>
<div class="endpoint"><code>POST /api/v2/conversation</code> — 多轮对话预测</div>
<div class="endpoint"><code>POST /api/v2/kol</code> — KOL效果预测</div>
<div class="endpoint"><code>POST /api/v2/compare</code> — AB产品对比</div>
<div class="endpoint"><code>POST /api/v2/population</code> — 生成合成人群</div>
<div class="endpoint"><code>GET /api/v2/task/{id}</code> — 查询任务状态</div>
<div class="endpoint"><code>GET /api/v2/stats</code> — 平台统计</div>
<h2>认证</h2>
<p>免费用户: 每日50次 | Pro: 500次 | Enterprise: 10000次</p>
<p>通过 <code>X-API-Key</code> Header 传递API Key</p>
<p><a href="/docs">Swagger文档</a> | <a href="/redoc">ReDoc</a></p>
</body></html>"""

@app.get("/api/v2/health")
async def health_check():
    """健康检查。"""
    db = get_persistence()
    stats = db.get_stats()
    llm = get_llm()
    return {
        "status": "healthy",
        "service": "tianyan",
        "version": "2.0.0",
        "timestamp": time.time(),
        "llm": llm.get_stats(),
        "database": stats,
    }

@app.post("/api/v2/register")
async def register_user(req: RegisterRequest):
    """注册用户，获取API Key。"""
    api_key = generate_api_key()
    keys = load_api_keys()
    keys[api_key] = {
        "name": req.name,
        "email": req.email,
        "role": req.role,
        "created_at": datetime.now().isoformat(),
        "daily_count": 0,
        "last_date": datetime.now().strftime("%Y-%m-%d"),
    }
    save_api_keys(keys)
    return {
        "api_key": api_key,
        "name": req.name,
        "role": req.role,
        "daily_limit": {"free": 50, "pro": 500, "enterprise": 10000}.get(req.role, 50),
        "message": "请保存好你的API Key，它不会再次显示。",
    }

@app.post("/api/v2/predict")
async def predict(req: PredictRequest, user: dict = Depends(verify_api_key)):
    """产品上市预测。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, region="全国")
        eye = ConsumerEye()
        result = eye.predict_product_launch(
            product_name=req.product_name,
            price=req.price,
            category=req.category,
            selling_point=req.selling_point,
            channels=req.channels,
            target_population=pop,
        )

        # 保存到数据库
        db = get_persistence()
        try:
            sim_id = db.save_simulation(
                scenario_name=f"产品上市：{req.product_name}",
                scenario_type="product_launch",
                population_size=req.population_size,
                population_params={"region": "全国"},
                parameters={"product_name": req.product_name, "price": req.price, "category": req.category},
                result_summary=result.key_metrics,
                confidence=result.confidence,
                execution_time_ms=0,
            )
            db.save_prediction(
                simulation_id=sim_id,
                product=req.product_name,
                scenario_name=f"产品上市：{req.product_name}",
                key_metrics=result.key_metrics,
                segments=result.segments,
                recommendations=result.recommendations,
                confidence=result.confidence,
            )
        except Exception as e:
            logger.warning(f"Failed to save to DB: {e}")

        return {
            "success": True,
            "product": req.product_name,
            "confidence": result.confidence,
            "metrics": result.key_metrics,
            "segments": result.segments,
            "recommendations": result.recommendations,
            "population_size": req.population_size,
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/predict/async")
async def predict_async(
    req: PredictRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_api_key),
):
    """异步预测(大人群规模)。"""
    task_id = create_task("predict", req.model_dump())
    update_task(task_id, TaskStatus.RUNNING)

    def run_prediction():
        try:
            pop = SyntheticPopulation(size=req.population_size, region="全国")
            eye = ConsumerEye()
            result = eye.predict_product_launch(
                product_name=req.product_name,
                price=req.price,
                category=req.category,
                selling_point=req.selling_point,
                channels=req.channels,
                target_population=pop,
            )
            update_task(task_id, TaskStatus.COMPLETED, {
                "confidence": result.confidence,
                "metrics": result.key_metrics,
                "recommendations": result.recommendations,
            })
        except Exception as e:
            update_task(task_id, TaskStatus.FAILED, error=str(e))

    background_tasks.add_task(run_prediction)
    return {"task_id": task_id, "status": "pending", "message": "任务已提交，使用 GET /api/v2/task/{id} 查询状态"}

@app.get("/api/v2/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态。"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/v2/conversation")
async def conversation(req: ConversationRequest, user: dict = Depends(verify_api_key)):
    """多轮对话预测。"""
    session_id = req.session_id or str(uuid.uuid4())[:8]
    engine = get_conversation(session_id)

    if not engine.state:
        response = engine.start(req.message)
    else:
        response = engine.continue_(req.message)

    return {
        "session_id": session_id,
        "stage": response.stage,
        "message": response.message,
        "suggestions": response.suggestions,
        "data": response.data,
        "is_complete": response.is_complete,
    }

@app.post("/api/v2/kol")
async def kol_prediction(req: KOLRequest, user: dict = Depends(verify_api_key)):
    """KOL效果预测。"""
    pop = SyntheticPopulation(size=req.population_size, region="全国")
    engine = ChineseScenarioEngine(pop)
    result = engine.predict_kol_effect(req.product_name, req.product_price, req.kol_type)
    return {
        "success": True,
        "product": req.product_name,
        "kol_type": req.kol_type,
        "confidence": result.confidence,
        "metrics": {
            "reach": getattr(result, 'estimated_reach', 0),
            "conversion": getattr(result, 'estimated_conversion', 0),
            "roi": getattr(result, 'estimated_roi', 0),
        },
    }

@app.post("/api/v2/compare")
async def compare_products(req: CompareRequest, user: dict = Depends(verify_api_key)):
    """AB产品对比。"""
    pop = SyntheticPopulation(size=req.population_size, region="全国")
    eye = ConsumerEye()

    result_a = eye.predict_product_launch(
        product_name=req.product_a.get("name", "Product A"),
        price=req.product_a.get("price", 99),
        category=req.product_a.get("category", "消费品"),
        selling_point=req.product_a.get("selling_point", ""),
        channels=req.product_a.get("channels", ["线上"]),
        target_population=pop,
    )

    result_b = eye.predict_product_launch(
        product_name=req.product_b.get("name", "Product B"),
        price=req.product_b.get("price", 99),
        category=req.product_b.get("category", "消费品"),
        selling_point=req.product_b.get("selling_point", ""),
        channels=req.product_b.get("channels", ["线上"]),
        target_population=pop,
    )

    winner = "A" if result_a.confidence > result_b.confidence else "B"
    return {
        "product_a": {
            "name": req.product_a.get("name"),
            "confidence": result_a.confidence,
            "metrics": result_a.key_metrics,
        },
        "product_b": {
            "name": req.product_b.get("name"),
            "confidence": result_b.confidence,
            "metrics": result_b.key_metrics,
        },
        "winner": winner,
        "recommendation": f"推荐{winner}产品，置信度更高",
    }

@app.post("/api/v2/population")
async def create_population(req: PopulationRequest, user: dict = Depends(verify_api_key)):
    """生成合成人群。"""
    pop = SyntheticPopulation(size=req.size, region=req.region, age_range=(req.age_min, req.age_max))
    profiles = pop.profiles
    summary = pop.summary()
    return {
        "success": True,
        "size": len(profiles),
        "summary": summary,
            "sample": [
                {
                    "age": p.age,
                    "gender": p.gender,
                    "city_tier": p.city_tier,
                    "monthly_income": p.monthly_income,
                    "consumer_archetype": p.consumer_archetype,
                }
                for p in profiles[:5]
            ],
    }

@app.get("/api/v2/stats")
async def get_stats():
    """平台统计。"""
    db = get_persistence()
    stats = db.get_stats()
    llm = get_llm()
    return {
        "platform": "天眼 Tianyan",
        "version": "2.0.0",
        "llm": llm.get_stats(),
        "database": stats,
        "active_sessions": len(_conversations),
        "total_tasks": len(_tasks),
    }

@app.get("/api/v2/predictions")
async def list_predictions(
    product: str = "",
    limit: int = 20,
    user: dict = Depends(verify_api_key),
):
    """查询历史预测。"""
    db = get_persistence()
    predictions = db.list_predictions(product=product, limit=limit)
    return {"predictions": predictions, "count": len(predictions)}

# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=os.environ.get("TIANYAN_HOST", "0.0.0.0"),
        port=int(os.environ.get("TIANYAN_PORT", "8000")),
        reload=os.environ.get("DEBUG", "false").lower() == "true",
    )
