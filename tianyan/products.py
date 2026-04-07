"""
三眼产品矩阵

ConsumerEye (消费眼): 产品预测、广告测试、品牌舆情
PolicyEye (政策眼): 政策影响评估、民意温度计（严格去政治化）
MarketEye (市场眼): 行业趋势、竞品动态、投资风向
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .population import SyntheticPopulation
from .scenarios import Scenario, ScenarioEngine, SimulationResult
from .compliance import ComplianceChecker


@dataclass
class PredictionResult:
    """预测结果（统一格式）。"""
    scenario_name: str
    product: str  # "consumer_eye" / "policy_eye" / "market_eye"
    population_summary: dict[str, Any]
    key_metrics: dict[str, float]
    segments: dict[str, dict[str, float]]
    recommendations: list[str]
    confidence: float
    raw_result: SimulationResult | None = None


class ConsumerEye:
    """
    消�眼 (Consumer Eye) — 商业预测核心产品。

    能力：
    - 产品上市预测：模拟目标人群对新产品的反应
    - 广告创意测试：评估不同广告创意的吸引力
    - 定价策略优化：找到最优价格点
    - 用户流失预测：识别高流失风险用户画像
    - 品牌舆情模拟：模拟品牌事件的传播效应
    """

    def __init__(self, model_provider: str = "mimo"):
        self.model_provider = model_provider
        self.compliance = ComplianceChecker()

    def predict_product_launch(
        self,
        product_name: str,
        price: float,
        category: str,
        selling_point: str,
        channels: list[str],
        target_population: SyntheticPopulation,
        social_propagation: bool = True,
    ) -> PredictionResult:
        """预测产品上市反应。"""
        # 合规检查
        self.compliance.check_scenario("product_launch", {
            "product_name": product_name,
            "category": category,
        })

        scenario = Scenario(
            name=f"产品上市：{product_name}",
            description=f"{product_name}上市预测",
            category="product_launch",
            parameters={
                "product_name": product_name,
                "price": price,
                "category": category,
                "selling_point": selling_point,
                "channels": channels,
            },
            metrics=["购买意愿", "价格接受度", "渠道偏好"],
        )

        engine = ScenarioEngine(target_population)
        result = engine.run(scenario, rounds=2 if social_propagation else 1)

        return PredictionResult(
            scenario_name=scenario.name,
            product="consumer_eye",
            population_summary=target_population.summary(),
            key_metrics={
                "purchase_intent": result.purchase_intent,
                "avg_confidence": result.aggregate.get("avg_confidence", 0),
                "social_influence_rate": result.aggregate.get("social_influence_rate", 0),
            },
            segments=result.segments,
            recommendations=self._generate_recommendations(result),
            confidence=result.aggregate.get("avg_confidence", 0),
            raw_result=result,
        )

    def test_ad_creative(
        self,
        ad_theme: str,
        channel: str,
        style: str,
        target_population: SyntheticPopulation,
    ) -> PredictionResult:
        """测试广告创意效果。"""
        scenario = Scenario(
            name=f"广告测试：{ad_theme}",
            description=f"广告创意测试",
            category="advertising",
            parameters={
                "ad_theme": ad_theme,
                "channel": channel,
                "style": style,
            },
            metrics=["点击率预测", "渠道匹配度"],
        )

        engine = ScenarioEngine(target_population)
        result = engine.run(scenario, rounds=1)

        return PredictionResult(
            scenario_name=scenario.name,
            product="consumer_eye",
            population_summary=target_population.summary(),
            key_metrics={
                "click_intent": result.purchase_intent,  # reuse
                "avg_confidence": result.aggregate.get("avg_confidence", 0),
            },
            segments=result.segments,
            recommendations=[],
            confidence=result.aggregate.get("avg_confidence", 0),
            raw_result=result,
        )

    def optimize_pricing(
        self,
        product_name: str,
        price_low: float,
        price_high: float,
        target_population: SyntheticPopulation,
    ) -> PredictionResult:
        """定价策略优化。"""
        scenario = Scenario(
            name=f"定价优化：{product_name}",
            description=f"定价策略优化",
            category="pricing",
            parameters={
                "product_name": product_name,
                "price_low": price_low,
                "price_high": price_high,
            },
            metrics=["最优价格点", "价格敏感度分布"],
        )

        engine = ScenarioEngine(target_population)
        result = engine.run(scenario, rounds=1)

        return PredictionResult(
            scenario_name=scenario.name,
            product="consumer_eye",
            population_summary=target_population.summary(),
            key_metrics={
                "avg_confidence": result.aggregate.get("avg_confidence", 0),
            },
            segments=result.segments,
            recommendations=[
                f"建议定价区间：¥{price_low:.0f} - ¥{(price_low + price_high) / 2:.0f}",
                "一线城市可接受更高价格",
                "三线城市对价格更敏感",
            ],
            confidence=result.aggregate.get("avg_confidence", 0),
            raw_result=result,
        )

    def _generate_recommendations(self, result: SimulationResult) -> list[str]:
        """根据结果生成建议。"""
        recs = []
        if result.purchase_intent > 0.6:
            recs.append("购买意愿强烈，建议快速推进上市")
        elif result.purchase_intent > 0.4:
            recs.append("购买意愿中等，建议先做小规模测试")
        else:
            recs.append("购买意愿偏低，建议重新审视产品定位或定价")

        # 分群建议
        for segment, metrics in result.segments.items():
            if metrics.get("purchase_intent", 0) > 0.7:
                recs.append(f"核心目标人群：{segment}（购买意愿{metrics['purchase_intent']:.0%}）")

        return recs


class PolicyEye:
    """
    政策眼 (Policy Eye) — 政策影响评估。

    ⚠️ 严格去政治化红线：
    - ❌ 不预测人事变动
    - ❌ 不模拟社会动荡/群体事件
    - ❌ 不评价政治体制
    - ✅ 仅做经济/民生政策的影响评估
    """

    # 禁止的政策类别
    FORBIDDEN_CATEGORIES = [
        "人事变动", "选举", "政治体制", "意识形态",
        "群体事件", "社会动荡", "外交政策", "军事",
    ]

    def __init__(self, model_provider: str = "mimo"):
        self.model_provider = model_provider
        self.compliance = ComplianceChecker()

    def assess_policy_impact(
        self,
        policy_name: str,
        scope: str,
        changes: str,
        target_population: SyntheticPopulation,
        policy_category: str = "economic",
    ) -> PredictionResult:
        """
        评估政策影响。

        仅限经济/民生类政策：
        - 医保政策
        - 税收政策
        - 产业政策
        - 教育政策
        - 环保政策
        """
        # 合规检查
        self.compliance.check_policy_scenario(policy_name, policy_category)

        scenario = Scenario(
            name=f"政策评估：{policy_name}",
            description=f"政策影响评估",
            category="policy",
            parameters={
                "policy_name": policy_name,
                "scope": scope,
                "changes": changes,
            },
            metrics=["支持率", "影响人群比例"],
        )

        engine = ScenarioEngine(target_population)
        result = engine.run(scenario, rounds=2, social_propagation=True)

        return PredictionResult(
            scenario_name=scenario.name,
            product="policy_eye",
            population_summary=target_population.summary(),
            key_metrics={
                "approval_rate": result.approval_rate,
                "avg_confidence": result.aggregate.get("avg_confidence", 0),
                "social_influence_rate": result.aggregate.get("social_influence_rate", 0),
            },
            segments=result.segments,
            recommendations=[],
            confidence=result.aggregate.get("avg_confidence", 0),
            raw_result=result,
        )


class MarketEye:
    """
    市场眼 (Market Eye) — 行业趋势预测。

    能力：
    - 行业趋势预测
    - 竞品动态分析
    - 投资风向标
    """

    def __init__(self, model_provider: str = "mimo"):
        self.model_provider = model_provider

    def predict_trend(
        self,
        industry: str,
        trend_description: str,
        target_population: SyntheticPopulation,
    ) -> PredictionResult:
        """预测行业趋势。"""
        scenario = Scenario(
            name=f"行业趋势：{industry}",
            description=trend_description,
            category="market_trend",
            parameters={"industry": industry, "trend": trend_description},
            metrics=["采纳率", "增长预期"],
        )

        engine = ScenarioEngine(target_population)
        result = engine.run(scenario, rounds=1)

        return PredictionResult(
            scenario_name=scenario.name,
            product="market_eye",
            population_summary=target_population.summary(),
            key_metrics={
                "adoption_rate": result.purchase_intent,
                "avg_confidence": result.aggregate.get("avg_confidence", 0),
            },
            segments=result.segments,
            recommendations=[],
            confidence=result.aggregate.get("avg_confidence", 0),
            raw_result=result,
        )
