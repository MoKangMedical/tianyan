"""
中国特色场景模块

针对中国市场独有的商业场景：
- KOL效果预测
- 直播带货预测
- 电商渠道优化
- 下沉市场洞察
- 小红书种草预测
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .population import SyntheticPopulation
from .scenarios import Scenario, ScenarioEngine, SimulationResult
from .products import PredictionResult


# KOL画像（公开数据推断的合成数据）
KOL_PROFILES = {
    "头部美妆博主": {
        "followers": "1000万+",
        "avg_engagement": 0.03,
        "audience": ["18-24女", "25-34女"],
        "platforms": ["抖音", "小红书"],
        "trust_score": 0.65,
    },
    "中腰部科技博主": {
        "followers": "50-100万",
        "avg_engagement": 0.05,
        "audience": ["18-34男"],
        "platforms": ["B站", "抖音"],
        "trust_score": 0.75,
    },
    "垂类健康博主": {
        "followers": "10-50万",
        "avg_engagement": 0.08,
        "audience": ["35-54", "55+"],
        "platforms": ["微信视频号", "抖音"],
        "trust_score": 0.80,
    },
    "素人种草号": {
        "followers": "1-10万",
        "avg_engagement": 0.12,
        "audience": ["全年龄段"],
        "platforms": ["小红书"],
        "trust_score": 0.85,
    },
}

# 电商平台画像
ECOMMERCE_PLATFORMS = {
    "淘宝": {
        "user_base": "8亿",
        "price_sensitivity": 0.6,
        "trust_level": 0.7,
        "categories": ["服饰", "美妆", "家居", "数码"],
        "conversion_rate": 0.03,
    },
    "京东": {
        "user_base": "5亿",
        "price_sensitivity": 0.4,
        "trust_level": 0.85,
        "categories": ["数码", "家电", "母婴", "生鲜"],
        "conversion_rate": 0.04,
    },
    "拼多多": {
        "user_base": "8亿",
        "price_sensitivity": 0.85,
        "trust_level": 0.5,
        "categories": ["农产品", "日用百货", "服饰"],
        "conversion_rate": 0.06,
    },
    "抖音电商": {
        "user_base": "6亿",
        "price_sensitivity": 0.5,
        "trust_level": 0.55,
        "categories": ["服饰", "美妆", "食品", "家居"],
        "conversion_rate": 0.02,
    },
    "小红书": {
        "user_base": "2亿",
        "price_sensitivity": 0.35,
        "trust_level": 0.7,
        "categories": ["美妆", "服饰", "母婴", "家居"],
        "conversion_rate": 0.05,
    },
}


@dataclass
class KOLPredictionResult:
    """KOL效果预测结果。"""
    kol_type: str
    product: str
    predicted_reach: int
    predicted_engagement: float
    predicted_conversion: float
    best_audience: list[str]
    best_platform: str
    roi_estimate: float
    confidence: float


@dataclass
class LivestreamPredictionResult:
    """直播带货预测结果。"""
    product: str
    platform: str
    predicted_viewers: int
    predicted_gmv: float
    predicted_conversion_rate: float
    best_time_slot: str
    price_sensitivity_impact: float
    confidence: float


class ChineseScenarioEngine:
    """
    中国特色场景引擎。

    封装KOL、直播、电商等中国特色场景的模拟能力。
    """

    def __init__(self, population: SyntheticPopulation):
        self.population = population
        self.engine = ScenarioEngine(population)

    def predict_kol_effect(
        self,
        product_name: str,
        product_price: float,
        kol_type: str,
        target_audience: str = "",
    ) -> KOLPredictionResult:
        """
        预测KOL推广效果。

        模拟逻辑：
        1. 匹配KOL受众与合成人群
        2. 根据信任度和互动率计算转化
        3. 考虑社交传播效应
        """
        kol = KOL_PROFILES.get(kol_type, KOL_PROFILES["素人种草号"])

        # 计算受众匹配度
        matching_agents = [
            a for a in self.population.profiles
            if a.social_influence > 0.5
        ]
        reach_ratio = len(matching_agents) / len(self.population.profiles)

        # 基于KOL信任度和产品价格计算转化
        base_conversion = kol["trust_score"] * 0.1
        price_penalty = max(0, (product_price - 100) / 1000) * 0.02
        predicted_conversion = max(0.001, base_conversion - price_penalty)

        # 预估GMV
        predicted_reach = int(len(self.population.profiles) * reach_ratio * 1000)  # 扩展到真实规模
        predicted_engagement = kol["avg_engagement"]

        # 最佳平台
        best_platform = kol["platforms"][0] if kol["platforms"] else "抖音"

        return KOLPredictionResult(
            kol_type=kol_type,
            product=product_name,
            predicted_reach=predicted_reach,
            predicted_engagement=predicted_engagement,
            predicted_conversion=predicted_conversion,
            best_audience=kol["audience"],
            best_platform=best_platform,
            roi_estimate=predicted_reach * predicted_conversion * product_price / 10000,
            confidence=0.6,
        )

    def predict_livestream(
        self,
        product_name: str,
        product_price: float,
        platform: str = "抖音",
        discount_rate: float = 0.2,
    ) -> LivestreamPredictionResult:
        """
        预测直播带货效果。

        模拟逻辑：
        1. 计算折扣对不同价格敏感度人群的影响
        2. 模拟直播间冲动消费效应
        3. 考虑平台转化率差异
        """
        platform_info = ECOMMERCE_PLATFORMS.get(platform, ECOMMERCE_PLATFORMS["抖音"])

        # 价格敏感人群的转化提升
        price_sensitive = [
            a for a in self.population.profiles
            if a.price_sensitivity > 0.6
        ]
        price_sensitive_ratio = len(price_sensitive) / len(self.population.profiles)

        # 折扣吸引力
        discount_attraction = discount_rate * 2  # 20%折扣 → 40%吸引力
        impulse_boost = 0.3  # 直播间冲动消费加成

        # 基础转化率
        base_rate = platform_info["conversion_rate"]
        boosted_rate = base_rate * (1 + discount_attraction + impulse_boost)
        boosted_rate = min(boosted_rate, 0.15)  # 上限15%

        # 预估观众数（基于人群规模推算）
        viewers = int(len(self.population.profiles) * 50)  # 50倍扩展
        gmv = viewers * boosted_rate * product_price * (1 - discount_rate)

        # 最佳时段
        evening_viewers = [
            a for a in self.population.profiles
            if a.digital_literacy > 0.4 and a.age < 50
        ]
        time_slot = "20:00-22:00" if len(evening_viewers) > len(self.population.profiles) * 0.5 else "12:00-14:00"

        return LivestreamPredictionResult(
            product=product_name,
            platform=platform,
            predicted_viewers=viewers,
            predicted_gmv=gmv,
            predicted_conversion_rate=boosted_rate,
            best_time_slot=time_slot,
            price_sensitivity_impact=price_sensitive_ratio * discount_attraction,
            confidence=0.55,
        )

    def optimize_ecommerce_channel(
        self,
        product_name: str,
        product_price: float,
        product_category: str,
    ) -> dict[str, Any]:
        """
        电商渠道优化：找出最佳电商平台。

        基于产品特征匹配平台画像。
        """
        scores = {}

        for platform, info in ECOMMERCE_PLATFORMS.items():
            score = 0.0

            # 品类匹配
            if product_category in info["categories"]:
                score += 0.3

            # 价格匹配
            price_match = 1 - abs(
                (1 - info["price_sensitivity"]) - min(1, product_price / 500)
            )
            score += price_match * 0.3

            # 转化率
            score += info["conversion_rate"] * 5  # 0.03 → 0.15

            # 信任度（高价产品更看重）
            if product_price > 200:
                score += info["trust_level"] * 0.25
            else:
                score += info["trust_level"] * 0.1

            scores[platform] = round(score, 3)

        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "product": product_name,
            "price": product_price,
            "category": product_category,
            "platform_ranking": [
                {"platform": p, "score": s, "recommendation": self._channel_rec(p, s)}
                for p, s in ranked
            ],
            "best_platform": ranked[0][0],
            "confidence": 0.6,
        }

    def _channel_rec(self, platform: str, score: float) -> str:
        if score > 0.7:
            return f"强烈推荐{platform}，匹配度极高"
        elif score > 0.5:
            return f"建议{platform}作为主力渠道"
        elif score > 0.3:
            return f"可考虑{platform}作为辅助渠道"
        else:
            return f"不建议{platform}"

    def predict_xiaohongshu_seeding(
        self,
        product_name: str,
        product_price: float,
        content_style: str = "种草笔记",
        num_notes: int = 100,
    ) -> dict[str, Any]:
        """
        小红书种草效果预测。

        模拟不同内容风格在小红书上的传播效果。
        """
        # 小红书用户画像匹配
        xhs_users = [
            a for a in self.population.profiles
            if "小红书" in a.channels
            and a.age < 40
            and a.gender == "女"
        ]
        reach_ratio = len(xhs_users) / len(self.population.profiles)

        # 内容风格效果系数
        style_multiplier = {
            "种草笔记": 1.0,
            "测评视频": 1.2,
            "合集推荐": 0.8,
            "开箱体验": 1.1,
            "教程攻略": 0.9,
        }
        mult = style_multiplier.get(content_style, 1.0)

        # 互动率预测
        base_engagement = 0.05  # 5%
        price_penalty = max(0, (product_price - 200) / 2000) * 0.02
        engagement = max(0.01, (base_engagement - price_penalty) * mult)

        # 预估数据
        impressions = int(num_notes * 5000 * reach_ratio * mult)
        interactions = int(impressions * engagement)

        return {
            "product": product_name,
            "content_style": content_style,
            "num_notes": num_notes,
            "predicted_impressions": impressions,
            "predicted_interactions": interactions,
            "predicted_engagement_rate": engagement,
            "best_audience": "25-35岁一线城市女性" if reach_ratio > 0.3 else "需扩大目标受众",
            "content_suggestions": [
                "突出使用前后对比",
                "加入真实使用场景",
                "配合限时优惠信息",
            ],
            "confidence": 0.55,
        }
