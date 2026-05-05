#!/usr/bin/env python3
"""
天眼 (Tianyan) v2.0 生产级 API 服务器

完整的FastAPI应用，集成DeepSeek LLM推理、SQLite持久化、
批量仿真、历史查询、报告导出。
"""

from __future__ import annotations

import logging
import time
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tianyan.server")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    PolicyEye,
    MarketEye,
    ChineseScenarioEngine,
    ComplianceChecker,
    ComplianceError,
    McKinseyReportGenerator,
    PersistenceLayer,
    get_all_template_keys,
    get_template,
    list_templates,
    Scenario,
    ScenarioEngine,
    validate_population_params,
    validate_prediction_params,
    dry_run_population,
    dry_run_prediction,
    OperationAudit,
    audit_log,
    get_shared_adapter,
    MockDeepSeekAdapter,
    DeepSeekAdapter,
)

# ============================================================
# Pydantic 模型
# ============================================================

class PopulationRequest(BaseModel):
    size: int = Field(default=1000, ge=1, le=50000)
    region: str = Field(default="全国")
    age_min: int = Field(default=18, ge=0, le=100)
    age_max: int = Field(default=65, ge=0, le=100)
    gender: str = Field(default="all")
    seed: Optional[int] = None
    dry_run: bool = False


class SimulationRequest(BaseModel):
    scenario_description: str = Field(...)
    population_size: int = Field(default=500, ge=1, le=10000)
    rounds: int = Field(default=1, ge=1, le=5)
    dry_run: bool = False


class LLMSimulationRequest(BaseModel):
    product_name: str = Field(..., description="产品名称")
    price: float = Field(..., ge=0, description="产品价格")
    category: str = Field(default="消费医疗")
    channels: list[str] = Field(default_factory=lambda: ["抖音", "小红书"])
    selling_point: str = Field(default="")
    population_size: int = Field(default=100, ge=10, le=5000, description="人群规模(LLM模式下建议100-500)")
    rounds: int = Field(default=1, ge=1, le=3)
    social_propagation: bool = True
    use_llm: bool = True
    llm_batch_size: int = Field(default=10, ge=1, le=50)


class BatchSimulationRequest(BaseModel):
    products: list[dict] = Field(..., description="产品列表 [{name, price, category}]")
    population_size: int = Field(default=500, ge=1, le=10000)
    channels: list[str] = Field(default_factory=lambda: ["抖音", "小红书"])
    compare_metrics: list[str] = Field(default_factory=lambda: ["purchase_intent", "avg_confidence"])


class KOLRequest(BaseModel):
    product_name: str
    product_price: float = Field(ge=0)
    kol_type: str = "素人种草号"
    population_size: int = Field(default=1000, ge=1, le=10000)
    dry_run: bool = False


class LivestreamRequest(BaseModel):
    product_name: str
    product_price: float = Field(ge=0)
    platform: str = "抖音"
    discount_rate: float = Field(default=0.2, ge=0, le=1)
    population_size: int = Field(default=1000, ge=1, le=10000)
    dry_run: bool = False


class ChannelRequest(BaseModel):
    product_name: str
    product_price: float = Field(ge=0)
    product_category: str
    population_size: int = Field(default=1000, ge=1, le=10000)
    dry_run: bool = False


class SeedingRequest(BaseModel):
    product_name: str
    product_price: float = Field(ge=0)
    content_style: str = "种草笔记"
    num_notes: int = Field(default=100, ge=1, le=10000)
    population_size: int = Field(default=1000, ge=1, le=10000)
    dry_run: bool = False


class CompareRequest(BaseModel):
    product_a: str
    product_b: str
    price_a: float = Field(ge=0)
    price_b: float = Field(ge=0)
    category: str = "消费医疗"
    population_size: int = Field(default=1000, ge=1, le=50000)
    dry_run: bool = False


class ExportRequest(BaseModel):
    run_id: int = Field(..., description="仿真运行ID")
    format: str = Field(default="markdown", description="导出格式: markdown/html/json")


class MarketSnapshotRequest(BaseModel):
    industry: str = Field(default="消费医疗")
    population_size: int = Field(default=500, ge=1, le=5000)


# ============================================================
# 应用初始化
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("天眼 Tianyan v2.0.0 启动 — DeepSeek V4 Pro + SQLite + 交互仪表盘")
    # 检查DeepSeek状态
    adapter = get_shared_adapter()
    if isinstance(adapter, DeepSeekAdapter) and adapter.is_available:
        logger.info("🚀 DeepSeek API 可用 — LLM增强仿真已就绪")
    else:
        logger.warning("⚠️ DeepSeek 不可用 — 使用规则引擎降级模式")
    yield
    logger.info("天眼 Tianyan 已关闭")

app = FastAPI(
    title="天眼 Tianyan v2.0",
    description="中国版商业预测平台 — DeepSeek V4 Pro驱动的多Agent人群模拟引擎",
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

# 静态文件（Dashboard）
os.makedirs("/root/tianyan/dashboard", exist_ok=True)

# ============================================================
# 中间件
# ============================================================

_rate_limit_store: dict[str, list[float]] = {}

@app.middleware("http")
async def middleware(request, call_next):
    from starlette.responses import JSONResponse as JR
    import time as _time
    client_ip = request.client.host if request.client else "unknown"
    now = _time.time()
    window, max_req = 60, 120
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < window]
    if len(_rate_limit_store[client_ip]) >= max_req:
        return JR(status_code=429, content={"success": False, "detail": "请求过于频繁"})
    _rate_limit_store[client_ip].append(now)
    start = _time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("请求异常: %s %s", request.method, request.url.path)
        raise
    duration = _time.time() - start
    log_fn = logger.warning if response.status_code >= 400 else logger.info
    log_fn("%s %s → %s (%.3fs)", request.method, request.url.path, response.status_code, duration)
    return response


def _serialize_prediction(result) -> dict:
    return {
        "scenario_name": result.scenario_name,
        "product": result.product,
        "population_summary": result.population_summary,
        "key_metrics": result.key_metrics,
        "segments": result.segments,
        "recommendations": result.recommendations,
        "confidence": result.confidence,
    }


# ============================================================
# 持久化层
# ============================================================

_persistence: Optional[PersistenceLayer] = None

def get_persistence() -> PersistenceLayer:
    global _persistence
    if _persistence is None:
        _persistence = PersistenceLayer()
    return _persistence


# ============================================================
# 路由 — Landing & 健康检查
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def landing():
    return open("/root/tianyan/index.html").read()


@app.get("/api/health")
async def health():
    adapter = get_shared_adapter()
    llm_available = isinstance(adapter, DeepSeekAdapter) and adapter.is_available
    return {
        "success": True,
        "status": "healthy",
        "service": "tianyan",
        "version": "2.0.0",
        "llm_available": llm_available,
        "timestamp": time.time(),
    }


@app.get("/api/status")
async def status():
    """系统状态（含LLM状态）。"""
    adapter = get_shared_adapter()
    llm_info = {
        "available": isinstance(adapter, DeepSeekAdapter) and adapter.is_available,
        "model": adapter.config.model if isinstance(adapter, DeepSeekAdapter) else "mock",
        "mode": "DeepSeek V4 Pro" if (isinstance(adapter, DeepSeekAdapter) and adapter.is_available) else "规则引擎降级",
    }
    try:
        p = get_persistence()
        stats = p.stats() if hasattr(p, 'stats') else {}
    except Exception:
        stats = {}
    return {
        "success": True,
        "version": "2.0.0",
        "llm": llm_info,
        "persistence": stats,
        "templates": len(get_all_template_keys()),
        "timestamp": time.time(),
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return open("/root/tianyan/dashboard/index.html").read()


@app.get("/dashboard/history", response_class=HTMLResponse)
async def dashboard_history():
    return open("/root/tianyan/dashboard/history.html").read()


@app.get("/api/v2/info")
async def api_info():
    """API信息。"""
    endpoints = [
        {"method": "GET", "path": "/api/health", "desc": "健康检查"},
        {"method": "GET", "path": "/api/status", "desc": "系统状态"},
        {"method": "POST", "path": "/api/population", "desc": "创建合成人群"},
        {"method": "POST", "path": "/api/simulate", "desc": "运行仿真"},
        {"method": "POST", "path": "/api/v2/simulate/llm", "desc": "LLM增强仿真"},
        {"method": "POST", "path": "/api/v2/batch", "desc": "批量产品对比"},
        {"method": "GET", "path": "/api/v2/history", "desc": "仿真历史"},
        {"method": "GET", "path": "/api/v2/history/{id}", "desc": "仿真详情"},
        {"method": "POST", "path": "/api/v2/export", "desc": "导出报告"},
        {"method": "POST", "path": "/api/kol", "desc": "KOL预测"},
        {"method": "POST", "path": "/api/livestream", "desc": "直播预测"},
        {"method": "POST", "path": "/api/channel", "desc": "渠道优化"},
        {"method": "POST", "path": "/api/seeding", "desc": "小红书种草"},
        {"method": "POST", "path": "/api/v1/compare", "desc": "产品对比"},
        {"method": "GET", "path": "/api/templates", "desc": "行业模板"},
        {"method": "GET", "path": "/api/v1/checkpoints/audit", "desc": "审计日志"},
        {"method": "POST", "path": "/api/v1/checkpoints/preview", "desc": "Dry-run预览"},
        {"method": "GET", "path": "/api/v2/market/snapshot", "desc": "市场快照"},
    ]
    return {
        "success": True,
        "version": "2.0.0",
        "endpoints": endpoints,
        "total": len(endpoints),
        "industry_templates": get_all_template_keys(),
    }


# ============================================================
# 路由 — 核心API
# ============================================================

@app.post("/api/population")
async def create_population(req: PopulationRequest):
    checkpoint = validate_population_params(
        size=req.size, region=req.region,
        age_range=(req.age_min, req.age_max),
    )
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_population(req.size)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(
        region=req.region, size=req.size,
        age_range=(req.age_min, req.age_max), gender=req.gender, seed=req.seed,
    )
    return {"success": True, "population": pop.summary()}


@app.post("/api/simulate")
async def simulate(req: SimulationRequest):
    checkpoint = validate_prediction_params("仿真测试", 100, req.population_size, ["通用仿真"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_prediction("仿真测试", 100, req.population_size)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    scenario = Scenario(
        name="自定义仿真", description=req.scenario_description,
        category="custom", parameters={}, metrics=["购买意愿"],
    )
    engine = ScenarioEngine(pop)
    result = engine.run(scenario, rounds=req.rounds)
    return {
        "success": True,
        "scenario": req.scenario_description,
        "population_size": req.population_size,
        "purchase_intent": result.purchase_intent,
        "approval_rate": result.approval_rate,
        "decision_distribution": result.aggregate.get("decision_distribution", {}),
        "segments": result.segments,
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/v2/simulate/llm")
async def simulate_llm(req: LLMSimulationRequest):
    """LLM增强仿真 — DeepSeek V4 Pro驱动的深度推理。"""
    checkpoint = validate_prediction_params(req.product_name, req.price, req.population_size, ["LLM增强仿真"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})

    pop = SyntheticPopulation(size=req.population_size, seed=42)
    selling_point = req.selling_point or f"{req.product_name}核心卖点"
    scenario = Scenario(
        name=f"LLM仿真：{req.product_name}",
        description=f"新产品上市预测",
        category="product_launch",
        parameters={
            "product_name": req.product_name,
            "price": req.price,
            "category": req.category,
            "selling_point": selling_point,
            "channels": req.channels,
        },
        metrics=["购买意愿", "价格接受度", "渠道偏好"],
    )

    engine = ScenarioEngine(pop)
    result = engine.run(
        scenario, rounds=req.rounds,
        social_propagation=req.social_propagation,
        use_llm=req.use_llm, llm_batch_size=req.llm_batch_size,
    )

    # KOL预测
    cse = ChineseScenarioEngine(pop)
    kol_result = cse.predict_kol_effect(req.product_name, req.price, "素人种草号")
    livestream_result = cse.predict_livestream(req.product_name, req.price)

    # 渠道优化
    channel_result = cse.optimize_ecommerce_channel(req.product_name, req.price, req.category)

    # 持久化
    try:
        p = get_persistence()
        run_id = p.save_simulation(
            scenario_name=scenario.name, scenario_type="llm",
            population_size=req.population_size,
            population_params={"region": "全国", "size": req.population_size},
            parameters=req.model_dump(),
            result_summary={
                "purchase_intent": result.purchase_intent,
                "approval_rate": result.approval_rate,
                "decision_distribution": result.aggregate.get("decision_distribution", {}),
                "segments": {k: {mk: round(mv, 4) if isinstance(mv, float) else mv for mk, mv in v.items()} for k, v in result.segments.items()},
                "kol_roi": kol_result.roi_estimate,
                "livestream_gmv": livestream_result.predicted_gmv,
                "best_channel": channel_result.get("best_platform", ""),
            },
            confidence=result.aggregate.get("avg_confidence", 0),
            execution_time_ms=result.execution_time_ms,
            report_md=result.to_report(),
        )
    except Exception as e:
        logger.warning("持久化失败: %s", e)
        run_id = None

    return {
        "success": True,
        "run_id": run_id,
        "product": req.product_name,
        "price": req.price,
        "population_size": req.population_size,
        "use_llm": req.use_llm,
        "key_metrics": {
            "purchase_intent": result.purchase_intent,
            "approval_rate": result.approval_rate,
            "avg_confidence": result.aggregate.get("avg_confidence", 0),
            "social_influence_rate": result.aggregate.get("social_influence_rate", 0),
        },
        "decision_distribution": result.aggregate.get("decision_distribution", {}),
        "segments": {k: {mk: round(v, 4) if isinstance(v, float) else v for mk, v in v.items()} for k, v in result.segments.items()},
        "kol_prediction": {
            "predicted_reach": kol_result.predicted_reach,
            "predicted_conversion": kol_result.predicted_conversion,
            "best_platform": kol_result.best_platform,
            "roi_estimate": kol_result.roi_estimate,
        },
        "livestream_prediction": {
            "predicted_viewers": livestream_result.predicted_viewers,
            "predicted_gmv": livestream_result.predicted_gmv,
        },
        "channel_optimization": channel_result,
        "recommendations": _generate_recommendations(result),
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/v2/batch")
async def batch_simulate(req: BatchSimulationRequest):
    """批量产品对比 — 运行多个产品的仿真并比较。"""
    results = []
    pop = SyntheticPopulation(size=req.population_size, seed=42)

    for prod in req.products:
        name = prod.get("name", "未知产品")
        price = float(prod.get("price", 100))
        category = prod.get("category", "消费医疗")

        cp = validate_prediction_params(name, price, req.population_size, ["批量对比"])
        if not cp.approved:
            results.append({"product": name, "success": False, "error": "; ".join(cp.errors)})
            continue

        eye = ConsumerEye()
        try:
            result = eye.predict_product_launch(
                product_name=name, price=price, category=category,
                selling_point=prod.get("selling_point", f"{name}核心卖点"),
                channels=req.channels, target_population=pop,
            )
            results.append({
                "product": name,
                "price": price,
                "success": True,
                "metrics": {k: round(v, 4) if isinstance(v, float) else v for k, v in result.key_metrics.items()},
                "confidence": result.confidence,
            })
        except Exception as e:
            results.append({"product": name, "success": False, "error": str(e)})

    # 排序：按购买意愿降序
    results.sort(key=lambda x: x.get("metrics", {}).get("purchase_intent", 0) if x.get("success") else 0, reverse=True)

    return {"success": True, "population_size": req.population_size, "total": len(results), "results": results}


@app.get("/api/v2/history")
async def simulation_history(limit: int = Query(50, ge=1, le=200)):
    """仿真历史查询。"""
    try:
        p = get_persistence()
        runs = p.list_runs(limit=limit)
        return {"success": True, "total": len(runs), "runs": runs}
    except Exception as e:
        return {"success": False, "error": str(e), "runs": []}


@app.get("/api/v2/history/{run_id}")
async def simulation_detail(run_id: int):
    """单次仿真详情。"""
    try:
        p = get_persistence()
        run = p.get_run(run_id)
        if run is None:
            raise HTTPException(404, detail={"success": False, "detail": "仿真记录不存在"})
        return {"success": True, "run": run.to_dict() if hasattr(run, 'to_dict') else str(run)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"success": False, "detail": str(e)})


@app.post("/api/v2/export")
async def export_report(req: ExportRequest):
    """导出仿真报告。"""
    try:
        p = get_persistence()
        run = p.get_run(req.run_id)
        if run is None:
            raise HTTPException(404, detail={"success": False, "detail": "仿真记录不存在"})

        if req.format == "json":
            return {"success": True, "format": "json", "data": run.to_dict() if hasattr(run, 'to_dict') else str(run)}
        elif req.format == "html":
            report_md = run.report_md if hasattr(run, 'report_md') and run.report_md else str(run)
            html = f"<html><body><pre>{report_md}</pre></body></html>"
            return HTMLResponse(content=html)
        else:  # markdown
            report_md = run.report_md if hasattr(run, 'report_md') and run.report_md else str(run)
            return {"success": True, "format": "markdown", "report": report_md}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"success": False, "detail": str(e)})


@app.get("/api/v2/market/snapshot")
async def market_snapshot(industry: str = "消费医疗", size: int = 500):
    """市场实时快照 — 快速行业趋势洞察。"""
    pop = SyntheticPopulation(size=size, seed=42)
    eye = MarketEye()
    trend_result = eye.predict_trend(industry, f"{industry}行业趋势分析", pop)

    cse = ChineseScenarioEngine(pop)
    templates = [t for t in list_templates() if industry in t.get("industry", "") or industry in t.get("name", "")]

    return {
        "success": True,
        "industry": industry,
        "population_sample": size,
        "trend": {
            "adoption_rate": trend_result.key_metrics.get("adoption_rate", 0),
            "confidence": trend_result.confidence,
        },
        "population_summary": pop.summary(),
        "related_templates": [t.get("key") or t.get("name") for t in templates[:5]],
        "timestamp": time.time(),
    }


# ============================================================
# 路由 — 三眼产品 & 中国特色场景
# ============================================================

@app.post("/api/kol")
async def predict_kol(req: KOLRequest):
    checkpoint = validate_prediction_params(req.product_name, req.product_price, req.population_size, ["KOL预测"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_prediction(req.product_name, req.product_price, req.population_size, include_kol=True)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    cse = ChineseScenarioEngine(pop)
    result = cse.predict_kol_effect(req.product_name, req.product_price, req.kol_type)
    return {"success": True, **result.__dict__}


@app.post("/api/livestream")
async def predict_livestream(req: LivestreamRequest):
    checkpoint = validate_prediction_params(req.product_name, req.product_price, req.population_size, ["直播预测"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_prediction(req.product_name, req.product_price, req.population_size, include_livestream=True)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    cse = ChineseScenarioEngine(pop)
    result = cse.predict_livestream(req.product_name, req.product_price, req.platform, req.discount_rate)
    return {"success": True, **result.__dict__}


@app.post("/api/channel")
async def optimize_channel(req: ChannelRequest):
    checkpoint = validate_prediction_params(req.product_name, req.product_price, req.population_size, ["渠道优化"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_prediction(req.product_name, req.product_price, req.population_size)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    cse = ChineseScenarioEngine(pop)
    result = cse.optimize_ecommerce_channel(req.product_name, req.product_price, req.product_category)
    return {"success": True, **result}


@app.post("/api/seeding")
async def predict_seeding(req: SeedingRequest):
    checkpoint = validate_prediction_params(req.product_name, req.product_price, req.population_size, ["小红书种草"])
    if not checkpoint.approved:
        raise HTTPException(400, detail={"success": False, "errors": checkpoint.errors})
    if req.dry_run:
        preview = dry_run_prediction(req.product_name, req.product_price, req.population_size, include_seeding=True)
        return {"success": True, "mode": "dry_run", **preview}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    cse = ChineseScenarioEngine(pop)
    result = cse.predict_xiaohongshu_seeding(req.product_name, req.product_price, req.content_style, req.num_notes)
    return {"success": True, **result}


@app.post("/api/v1/compare")
async def compare_products(req: CompareRequest):
    cp_a = validate_prediction_params(req.product_a, req.price_a, req.population_size, ["产品A对比"])
    cp_b = validate_prediction_params(req.product_b, req.price_b, req.population_size, ["产品B对比"])
    if not (cp_a.approved and cp_b.approved):
        raise HTTPException(400, detail={"success": False, "errors": cp_a.errors + cp_b.errors})
    if req.dry_run:
        return {"success": True, "mode": "dry_run",
                "checkpoint": {"product_a": cp_a.to_dict(), "product_b": cp_b.to_dict()}}
    pop = SyntheticPopulation(size=req.population_size, seed=42)
    eye = ConsumerEye()
    ra = eye.predict_product_launch(req.product_a, req.price_a, req.category, "A", ["抖音"], pop)
    rb = eye.predict_product_launch(req.product_b, req.price_b, req.category, "B", ["抖音"], pop)
    am = {k: round(v, 4) if isinstance(v, float) else v for k, v in ra.key_metrics.items()}
    bm = {k: round(v, 4) if isinstance(v, float) else v for k, v in rb.key_metrics.items()}
    winner = req.product_a if am.get("purchase_intent", 0) >= bm.get("purchase_intent", 0) else req.product_b
    return {"success": True, "product_a": {"name": req.product_a, "metrics": am},
            "product_b": {"name": req.product_b, "metrics": bm}, "winner": winner}


@app.get("/api/templates")
async def templates_list():
    keys = get_all_template_keys()
    templates = list_templates()
    return {"success": True, "total": len(keys), "keys": keys, "templates": templates}


# ============================================================
# 审计 & 预览
# ============================================================

@app.get("/api/v1/checkpoints/audit")
async def get_audit(n: int = 20):
    return {"success": True, "stats": audit_log.stats(), "recent": audit_log.recent(n)}


class DryRunRequest(BaseModel):
    operation: str
    product_name: str = ""
    product_price: float = 0
    population_size: int = Field(default=1000, ge=1, le=50000)
    include_kol: bool = False
    include_livestream: bool = False
    include_seeding: bool = False


@app.post("/api/v1/checkpoints/preview")
async def preview(req: DryRunRequest):
    if req.operation == "population":
        result = dry_run_population(req.population_size)
    elif req.operation == "full_prediction":
        result = dry_run_prediction(req.product_name, req.product_price, req.population_size,
                                     req.include_kol, req.include_livestream, req.include_seeding)
    else:
        result = {"mode": "dry_run", "operation": req.operation, "message": f"预览暂未实现", "will_execute": False}
    return {"success": True, **result}


# ============================================================
# 辅助方法
# ============================================================

def _generate_recommendations(result) -> list:
    recs = []
    pi = result.purchase_intent
    if pi > 0.6:
        recs.append("购买意愿强烈，建议快速推进上市")
    elif pi > 0.4:
        recs.append("购买意愿中等，建议先做小规模测试")
    else:
        recs.append("购买意愿偏低，重新审视产品定位或定价")
    for seg, m in result.segments.items():
        if m.get("purchase_intent", 0) > 0.7:
            recs.append(f"核心目标人群：{seg}（购买意愿{m['purchase_intent']:.0%}）")
    return recs


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
