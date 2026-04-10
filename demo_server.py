#!/usr/bin/env python3
"""
天眼 (Tianyan) Demo Server

基于FastAPI的演示服务，提供REST API接口。
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    PolicyEye,
    MarketEye,
    ChineseScenarioEngine,
    ComplianceChecker,
    ComplianceError,
)

# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class PopulationRequest(BaseModel):
    """创建合成人群请求。"""
    size: int = Field(default=1000, ge=1, le=50000, description="人群规模")
    region: str = Field(default="全国", description="地区/城市等级")
    age_min: int = Field(default=18, ge=0, le=100)
    age_max: int = Field(default=65, ge=0, le=100)
    gender: str = Field(default="all", description="性别筛选: all/male/female")
    seed: Optional[int] = Field(default=None, description="随机种子")


class SimulationRequest(BaseModel):
    """通用仿真请求。"""
    scenario_description: str = Field(..., description="场景描述")
    population_size: int = Field(default=500, ge=1, le=10000)
    rounds: int = Field(default=1, ge=1, le=5)


class KOLRequest(BaseModel):
    """KOL效果预测请求。"""
    product_name: str
    product_price: float = Field(ge=0)
    kol_type: str = Field(default="素人种草号", description="KOL类型")
    population_size: int = Field(default=1000, ge=1, le=10000)


class LivestreamRequest(BaseModel):
    """直播带货预测请求。"""
    product_name: str
    product_price: float = Field(ge=0)
    platform: str = Field(default="抖音", description="直播平台")
    discount_rate: float = Field(default=0.2, ge=0, le=1)
    population_size: int = Field(default=1000, ge=1, le=10000)


class ChannelRequest(BaseModel):
    """电商渠道优化请求。"""
    product_name: str
    product_price: float = Field(ge=0)
    product_category: str
    population_size: int = Field(default=1000, ge=1, le=10000)


class SeedingRequest(BaseModel):
    """小红书种草预测请求。"""
    product_name: str
    product_price: float = Field(ge=0)
    content_style: str = Field(default="种草笔记")
    num_notes: int = Field(default=100, ge=1, le=10000)
    population_size: int = Field(default=1000, ge=1, le=10000)


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="天眼 Tianyan",
    description="中国版商业预测平台 — 基于多Agent人群模拟的商业预测引擎",
    version="0.3.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_prediction(result) -> dict[str, Any]:
    """将PredictionResult序列化为字典。"""
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
# 路由
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Landing Page — 天眼平台介绍。"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>天眼 Tianyan — 中国版商业预测平台</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 50%, #2d1b69 100%);
    color: #e0e0e0;
    min-height: 100vh;
  }
  .hero {
    text-align: center;
    padding: 80px 20px 60px;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 70% 50%, rgba(168, 85, 247, 0.06) 0%, transparent 50%);
    animation: pulse 8s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }
  .hero h1 {
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
    position: relative;
  }
  .hero .subtitle {
    font-size: 1.3rem;
    color: #94a3b8;
    margin-bottom: 12px;
    position: relative;
  }
  .hero .tagline {
    font-size: 1rem;
    color: #64748b;
    position: relative;
  }
  .container { max-width: 1100px; margin: 0 auto; padding: 0 20px; }

  .stats {
    display: flex;
    justify-content: center;
    gap: 48px;
    padding: 40px 0;
    position: relative;
  }
  .stat { text-align: center; }
  .stat .num {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .stat .label { font-size: 0.9rem; color: #94a3b8; margin-top: 4px; }

  .features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
    padding: 40px 0;
  }
  .feature {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 28px;
    transition: all 0.3s;
  }
  .feature:hover {
    background: rgba(255,255,255,0.07);
    border-color: rgba(129, 140, 248, 0.3);
    transform: translateY(-2px);
  }
  .feature .icon { font-size: 2rem; margin-bottom: 12px; }
  .feature h3 { font-size: 1.2rem; color: #c4b5fd; margin-bottom: 8px; }
  .feature p { color: #94a3b8; line-height: 1.6; font-size: 0.95rem; }

  .api-section {
    padding: 40px 0 60px;
  }
  .api-section h2 {
    text-align: center;
    font-size: 1.8rem;
    color: #c4b5fd;
    margin-bottom: 32px;
  }
  .api-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
  }
  .api-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .method {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
    min-width: 50px;
    text-align: center;
  }
  .method.get { background: rgba(34,197,94,0.2); color: #4ade80; }
  .method.post { background: rgba(59,130,246,0.2); color: #60a5fa; }
  .api-item .path { font-family: "Fira Code", monospace; font-size: 0.9rem; color: #e2e8f0; }
  .api-item .desc { font-size: 0.8rem; color: #64748b; margin-left: auto; }

  footer {
    text-align: center;
    padding: 40px 0;
    color: #475569;
    font-size: 0.85rem;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  footer a { color: #818cf8; text-decoration: none; }
</style>
</head>
<body>
<div class="hero">
  <h1>👁️ 天眼 Tianyan</h1>
  <p class="subtitle">中国版商业预测平台 — 基于多Agent人群模拟</p>
  <p class="tagline">用AI合成人群替代传统调研，72小时完成6个月的市场洞察</p>
</div>

<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">100%</div><div class="label">合成数据</div></div>
    <div class="stat"><div class="num">72h</div><div class="label">预测周期</div></div>
    <div class="stat"><div class="num">3</div><div class="label">核心产品</div></div>
    <div class="stat"><div class="num">∞</div><div class="label">MIMO调用</div></div>
  </div>

  <div class="features">
    <div class="feature">
      <div class="icon">🛒</div>
      <h3>消费眼 ConsumerEye</h3>
      <p>产品上市预测、广告创意测试、定价策略优化、品牌舆情模拟。覆盖KOL种草、直播带货、电商渠道全链路。</p>
    </div>
    <div class="feature">
      <div class="icon">🏛️</div>
      <h3>政策眼 PolicyEye</h3>
      <p>经济民生政策影响评估、民意温度计。严格去政治化，仅做合规的政策模拟分析。</p>
    </div>
    <div class="feature">
      <div class="icon">📊</div>
      <h3>市场眼 MarketEye</h3>
      <p>行业趋势预测、竞品动态分析、投资风向标。用数据驱动市场洞察。</p>
    </div>
    <div class="feature">
      <div class="icon">🔥</div>
      <h3>KOL效果预测</h3>
      <p>头部博主、中腰部达人、素人种草号，精准预测推广效果与ROI。</p>
    </div>
    <div class="feature">
      <div class="icon">📺</div>
      <h3>直播带货预测</h3>
      <p>抖音、快手、淘宝直播，模拟直播间冲动消费效应，预测GMV。</p>
    </div>
    <div class="feature">
      <div class="icon">📕</div>
      <h3>小红书种草</h3>
      <p>种草笔记、测评视频、合集推荐，预测内容传播效果与互动率。</p>
    </div>
  </div>

  <div class="api-section">
    <h2>📡 API 接口</h2>
    <div class="api-list">
      <div class="api-item">
        <span class="method get">GET</span>
        <span class="path">/</span>
        <span class="desc">当前页面</span>
      </div>
      <div class="api-item">
        <span class="method get">GET</span>
        <span class="path">/api/health</span>
        <span class="desc">健康检查</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/population</span>
        <span class="desc">创建合成人群</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/simulate</span>
        <span class="desc">运行仿真</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/kol</span>
        <span class="desc">KOL效果预测</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/livestream</span>
        <span class="desc">直播带货预测</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/channel</span>
        <span class="desc">电商渠道优化</span>
      </div>
      <div class="api-item">
        <span class="method post">POST</span>
        <span class="path">/api/seeding</span>
        <span class="desc">小红书种草预测</span>
      </div>
    </div>
  </div>
</div>

<footer>
  <p>天眼 Tianyan v0.3.0 · <a href="https://github.com/MoKangMedical/tianyan">GitHub</a> · 100% 合成数据 · 零隐私风险</p>
</footer>
</body>
</html>"""


@app.get("/api/health")
async def health_check():
    """健康检查。"""
    return {
        "status": "healthy",
        "service": "tianyan",
        "version": "0.3.0",
        "timestamp": time.time(),
    }


@app.post("/api/population")
async def create_population(req: PopulationRequest):
    """创建合成人群。"""
    try:
        pop = SyntheticPopulation(
            size=req.size,
            region=req.region,
            age_range=(req.age_min, req.age_max),
            gender=req.gender,
            seed=req.seed,
        )
        summary = pop.summary()
        # 返回前5个样本画像（脱敏）
        samples = [
            {
                "agent_id": p.agent_id,
                "age": p.age,
                "gender": p.gender,
                "city": p.city,
                "city_tier": p.city_tier,
                "income": p.monthly_income,
                "archetype": p.consumer_archetype,
                "digital_literacy": round(p.digital_literacy, 2),
                "channels": p.channels,
            }
            for p in pop.profiles[:5]
        ]
        return {
            "success": True,
            "summary": summary,
            "samples": samples,
        }
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {traceback.format_exc()}")


@app.post("/api/simulate")
async def run_simulation(req: SimulationRequest):
    """运行通用仿真。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        from tianyan import Scenario, ScenarioEngine
        scenario = Scenario(
            name="通用仿真",
            description=req.scenario_description,
            category="general",
        )
        engine = ScenarioEngine(pop)
        result = engine.run(scenario, rounds=req.rounds)
        return {
            "success": True,
            "scenario": req.scenario_description,
            "population_size": req.population_size,
            "purchase_intent": result.purchase_intent,
            "aggregate": result.aggregate,
            "segments": result.segments,
        }
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kol")
async def kol_prediction(req: KOLRequest):
    """KOL效果预测。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        engine = ChineseScenarioEngine(pop)
        result = engine.predict_kol_effect(
            product_name=req.product_name,
            product_price=req.product_price,
            kol_type=req.kol_type,
        )
        return {
            "success": True,
            "kol_type": result.kol_type,
            "product": result.product,
            "predicted_reach": result.predicted_reach,
            "predicted_engagement": result.predicted_engagement,
            "predicted_conversion": result.predicted_conversion,
            "best_audience": result.best_audience,
            "best_platform": result.best_platform,
            "roi_estimate": round(result.roi_estimate, 2),
            "confidence": result.confidence,
        }
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/livestream")
async def livestream_prediction(req: LivestreamRequest):
    """直播带货预测。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        engine = ChineseScenarioEngine(pop)
        result = engine.predict_livestream(
            product_name=req.product_name,
            product_price=req.product_price,
            platform=req.platform,
            discount_rate=req.discount_rate,
        )
        return {
            "success": True,
            "product": result.product,
            "platform": result.platform,
            "predicted_viewers": result.predicted_viewers,
            "predicted_gmv": round(result.predicted_gmv, 2),
            "predicted_conversion_rate": round(result.predicted_conversion_rate, 4),
            "best_time_slot": result.best_time_slot,
            "price_sensitivity_impact": round(result.price_sensitivity_impact, 3),
            "confidence": result.confidence,
        }
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/channel")
async def channel_optimization(req: ChannelRequest):
    """电商渠道优化。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        engine = ChineseScenarioEngine(pop)
        result = engine.optimize_ecommerce_channel(
            product_name=req.product_name,
            product_price=req.product_price,
            product_category=req.product_category,
        )
        return {"success": True, **result}
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seeding")
async def seeding_prediction(req: SeedingRequest):
    """小红书种草预测。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        engine = ChineseScenarioEngine(pop)
        result = engine.predict_xiaohongshu_seeding(
            product_name=req.product_name,
            product_price=req.product_price,
            content_style=req.content_style,
            num_notes=req.num_notes,
        )
        return {"success": True, **result}
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 高级端点
# ============================================================


class FullPredictionRequest(BaseModel):
    """完整预测流程请求。"""
    product_name: str
    product_price: float = Field(ge=0)
    category: str = Field(default="消费医疗")
    selling_point: str = Field(default="")
    channels: list[str] = Field(default=["抖音", "小红书"])
    population_size: int = Field(default=1000, ge=1, le=50000)
    age_min: int = Field(default=25, ge=0, le=100)
    age_max: int = Field(default=45, ge=0, le=100)
    region: str = Field(default="一线城市")
    include_kol: bool = Field(default=True)
    include_livestream: bool = Field(default=True)
    include_seeding: bool = Field(default=True)


@app.post("/api/v1/predict/full")
async def full_prediction(req: FullPredictionRequest):
    """完整预测流程：人群→消费眼→KOL→直播→种草→渠道。"""
    try:
        pop = SyntheticPopulation(
            size=req.population_size, region=req.region,
            age_range=(req.age_min, req.age_max), seed=42,
        )
        eye = ConsumerEye()
        launch = eye.predict_product_launch(
            product_name=req.product_name, price=req.product_price,
            category=req.category,
            selling_point=req.selling_point or f"{req.product_name}核心卖点",
            channels=req.channels, target_population=pop,
        )
        pricing = eye.optimize_pricing(
            product_name=req.product_name,
            price_low=max(1, req.product_price * 0.5),
            price_high=req.product_price * 2, target_population=pop,
        )
        result = {
            "success": True, "product": req.product_name,
            "population": pop.summary(),
            "product_launch": _serialize_prediction(launch),
            "pricing": _serialize_prediction(pricing),
        }
        if req.include_kol:
            engine = ChineseScenarioEngine(pop)
            kol_results = []
            for kt in ["头部美妆博主", "垂类健康博主", "素人种草号"]:
                kr = engine.predict_kol_effect(req.product_name, req.product_price, kt)
                kol_results.append({
                    "type": kt, "reach": kr.predicted_reach,
                    "engagement": kr.predicted_engagement,
                    "conversion": kr.predicted_conversion,
                    "platform": kr.best_platform,
                    "roi": round(kr.roi_estimate, 2),
                })
            result["kol"] = kol_results
        if req.include_livestream:
            engine = ChineseScenarioEngine(pop)
            ls = engine.predict_livestream(req.product_name, req.product_price, "抖音", 0.15)
            result["livestream"] = {
                "platform": ls.platform, "viewers": ls.predicted_viewers,
                "gmv": round(ls.predicted_gmv, 2),
                "conversion_rate": round(ls.predicted_conversion_rate, 4),
                "best_time_slot": ls.best_time_slot,
            }
        if req.include_seeding:
            engine = ChineseScenarioEngine(pop)
            seeding = engine.predict_xiaohongshu_seeding(req.product_name, req.product_price, "种草笔记", 200)
            result["seeding"] = {
                "impressions": seeding["predicted_impressions"],
                "interactions": seeding["predicted_interactions"],
                "engagement_rate": round(seeding["predicted_engagement_rate"], 4),
                "suggestions": seeding["content_suggestions"][:5],
            }
        ce = ChineseScenarioEngine(pop)
        result["channels"] = ce.optimize_ecommerce_channel(req.product_name, req.product_price, req.category)
        return result
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/report/generate")
async def generate_report(req: FullPredictionRequest):
    """生成麦肯锡级报告。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, region=req.region, age_range=(req.age_min, req.age_max), seed=42)
        se = ScenarioEngine(pop)
        scenario = Scenario(name=f"{req.product_name}上市", description=f"{req.product_name}，定价{req.product_price}元", category="general")
        sim_result = se.run(scenario, rounds=3, social_propagation=True)
        gen = McKinseyReportGenerator()
        report = gen.generate_product_launch_report(product_name=req.product_name, simulation_result=sim_result)
        return {"success": True, "title": report.title, "sections": [s.to_dict() for s in report.sections], "markdown": report.to_markdown()}
    except ComplianceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/templates")
async def api_list_templates():
    """获取所有行业模板。"""
    from tianyan import list_templates as _lt
    templates = _lt()
    return {"success": True, "count": len(templates), "templates": [{"name": t.name, "industry": t.industry, "description": t.description, "key_metrics": t.key_metrics} for t in templates]}


class TemplateRunRequest(BaseModel):
    template_key: str
    product_name: str
    product_price: float = Field(ge=0)
    population_size: int = Field(default=1000, ge=1, le=50000)


@app.post("/api/v1/template/run")
async def run_template(req: TemplateRunRequest):
    """用指定行业模板运行预测。"""
    try:
        tpl = get_template(req.template_key)
        rec = tpl.recommended_population
        pop = SyntheticPopulation(size=req.population_size, age_range=rec.get("age_range", (25, 45)), gender=rec.get("gender", "all"), seed=42)
        eye = ConsumerEye()
        result = eye.predict_product_launch(
            product_name=req.product_name, price=req.product_price,
            category=tpl.industry, selling_point=tpl.description,
            channels=tpl.default_params.get("channels", ["抖音"]), target_population=pop,
        )
        return {"success": True, "template": tpl.name, "industry": tpl.industry, "prediction": _serialize_prediction(result), "reference_data": tpl.reference_data, "competitor_hints": tpl.competitor_hints}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"模板 '{req.template_key}' 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/dashboard")
async def dashboard():
    """仪表盘概览。"""
    keys = get_all_template_keys()
    return {
        "success": True, "platform": "天眼 Tianyan", "version": "0.3.0",
        "stats": {"synthetic_population": "1-50000人", "industry_templates": len(keys), "compliance": "PIPL+数安法", "ai_engine": "MIMO API"},
        "products": [{"name": "消费眼", "status": "active"}, {"name": "政策眼", "status": "active"}, {"name": "市场眼", "status": "active"}],
        "industry_templates": keys, "total_endpoints": 14,
    }


class CompareRequest(BaseModel):
    product_a: str
    product_b: str
    price_a: float = Field(ge=0)
    price_b: float = Field(ge=0)
    category: str = Field(default="消费医疗")
    population_size: int = Field(default=1000, ge=1, le=50000)


@app.post("/api/v1/compare")
async def compare_products(req: CompareRequest):
    """对比两个产品。"""
    try:
        pop = SyntheticPopulation(size=req.population_size, seed=42)
        eye = ConsumerEye()
        ra = eye.predict_product_launch(product_name=req.product_a, price=req.price_a, category=req.category, selling_point="A", channels=["抖音"], target_population=pop)
        rb = eye.predict_product_launch(product_name=req.product_b, price=req.price_b, category=req.category, selling_point="B", channels=["抖音"], target_population=pop)
        am = {k: round(v, 4) if isinstance(v, float) else v for k, v in ra.key_metrics.items()}
        bm = {k: round(v, 4) if isinstance(v, float) else v for k, v in rb.key_metrics.items()}
        winner = req.product_a if am.get("purchase_intent", 0) >= bm.get("purchase_intent", 0) else req.product_b
        return {"success": True, "product_a": {"name": req.product_a, "metrics": am}, "product_b": {"name": req.product_b, "metrics": bm}, "winner": winner}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
