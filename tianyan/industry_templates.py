"""
行业场景模板 — 预置常见商业场景

每个模板包含：
- 默认参数
- 推荐人群画像
- 关键指标
- 参考数据
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IndustryTemplate:
    """行业场景模板。"""
    name: str
    industry: str
    description: str
    default_params: dict[str, Any]
    recommended_population: dict[str, Any]
    key_metrics: list[str]
    reference_data: dict[str, Any]
    competitor_hints: list[dict[str, Any]] = field(default_factory=list)


# ================================================================
# 预置模板
# ================================================================

GLP1_WEIGHT_LOSS = IndustryTemplate(
    name="GLP-1减重产品上市",
    industry="消费医疗",
    description="GLP-1受体激动剂（司美格鲁肽/替尔泊肽）减重产品上市预测",
    default_params={
        "price_range": (299, 599),
        "channels": ["抖音", "小红书", "微信"],
        "selling_points": ["科学减重", "医生指导", "居家注射"],
        "category": "处方药",
    },
    recommended_population={
        "age_range": (25, 55),
        "gender": "female",
        "income_filter": "中等收入",
        "size": 5000,
    },
    key_metrics=["购买意愿", "价格敏感度", "渠道偏好", "复购意愿", "社交传播力"],
    reference_data={
        "market_size_rmb": 100_000_000_000,  # 1000亿（2030预测）
        "cagr": 0.19,
        "key_players": ["诺和诺德", "礼来", "信达生物", "恒瑞医药", "华东医药"],
        "patent_expiry": 2026,
        "policy_risk": "中",
    },
    competitor_hints=[
        {"name": "诺和诺德(司美格鲁肽)", "position": "市场领导者", "capability": "原研药+品牌", "threat": "高"},
        {"name": "礼来(替尔泊肽)", "position": "强力挑战者", "capability": "双靶点优势", "threat": "高"},
        {"name": "信达生物", "position": "国产先驱", "capability": "生物仿制药", "threat": "中"},
        {"name": "京东健康", "position": "渠道霸主", "capability": "流量+供应链", "threat": "中"},
    ],
)

HEALTH_SUPPLEMENT = IndustryTemplate(
    name="保健品上市",
    industry="健康消费品",
    description="营养补充剂/保健食品上市预测",
    default_params={
        "price_range": (98, 298),
        "channels": ["抖音", "小红书", "淘宝", "京东"],
        "selling_points": ["科学配方", "天然成分", "便捷服用"],
        "category": "保健食品",
    },
    recommended_population={
        "age_range": (25, 65),
        "gender": "all",
        "income_filter": "",
        "size": 5000,
    },
    key_metrics=["购买意愿", "品牌认知度", "价格接受度", "渠道偏好", "复购率"],
    reference_data={
        "market_size_rmb": 500_000_000_000,  # 5000亿
        "growth_rate": 0.12,
        "key_players": ["汤臣倍健", "Swisse", "康宝莱", "无限极"],
    },
    competitor_hints=[
        {"name": "汤臣倍健", "position": "行业龙头", "capability": "品牌+渠道", "threat": "高"},
        {"name": "Swisse", "position": "外资品牌", "capability": "品牌溢价", "threat": "中"},
    ],
)

SKINCARE_LAUNCH = IndustryTemplate(
    name="护肤品上市",
    industry="美妆护肤",
    description="功能性护肤品/美妆产品上市预测",
    default_params={
        "price_range": (68, 398),
        "channels": ["小红书", "抖音", "淘宝"],
        "selling_points": ["功效验证", "成分安全", "性价比"],
        "category": "化妆品",
    },
    recommended_population={
        "age_range": (18, 45),
        "gender": "female",
        "income_filter": "",
        "size": 5000,
    },
    key_metrics=["购买意愿", "种草转化率", "KOL效果", "价格敏感度"],
    reference_data={
        "market_size_rmb": 400_000_000_000,
        "growth_rate": 0.08,
        "key_players": ["珀莱雅", "薇诺娜", "华熙生物", "贝泰妮"],
    },
)

TELEHEALTH_PLATFORM = IndustryTemplate(
    name="远程医疗平台",
    industry="数字健康",
    description="互联网医疗/远程问诊平台商业预测",
    default_params={
        "price_range": (0, 99),
        "channels": ["微信", "抖音", "应用商店"],
        "selling_points": ["便捷就医", "AI辅助", "7x24在线"],
        "category": "互联网医疗",
    },
    recommended_population={
        "age_range": (20, 60),
        "gender": "all",
        "income_filter": "",
        "size": 8000,
    },
    key_metrics=["注册意愿", "付费转化率", "使用频率", "推荐意愿"],
    reference_data={
        "market_size_rmb": 300_000_000_000,
        "growth_rate": 0.25,
        "key_players": ["京东健康", "阿里健康", "微医", "好大夫"],
        "policy_trend": "利好",
    },
    competitor_hints=[
        {"name": "京东健康", "position": "平台巨头", "capability": "供应链+流量", "threat": "高"},
        {"name": "阿里健康", "position": "平台巨头", "capability": "电商生态", "threat": "高"},
        {"name": "微医", "position": "垂直深耕", "capability": "医院资源", "threat": "中"},
    ],
)

MALE_HEALTH = IndustryTemplate(
    name="男性健康管理",
    industry="消费医疗",
    description="男性健康/精力管理产品上市预测",
    default_params={
        "price_range": (199, 599),
        "channels": ["抖音", "微信", "知乎"],
        "selling_points": ["隐私保护", "科学方案", "便捷获取"],
        "category": "处方药/保健品",
    },
    recommended_population={
        "age_range": (25, 55),
        "gender": "male",
        "income_filter": "中等收入",
        "size": 5000,
    },
    key_metrics=["购买意愿", "隐私顾虑度", "渠道偏好", "价格接受度"],
    reference_data={
        "market_size_rmb": 150_000_000_000,
        "growth_rate": 0.15,
        "key_players": ["白云山", "常山药业", "广生堂"],
    },
)


# ================================================================
# 模板注册表
# ================================================================

TEMPLATES = {
    "glp1_weight_loss": GLP1_WEIGHT_LOSS,
    "health_supplement": HEALTH_SUPPLEMENT,
    "skincare_launch": SKINCARE_LAUNCH,
    "telehealth_platform": TELEHEALTH_PLATFORM,
    "male_health": MALE_HEALTH,
}


def get_template(name: str) -> IndustryTemplate | None:
    """获取行业模板。"""
    return TEMPLATES.get(name)


def list_templates() -> list[dict[str, str]]:
    """列出所有可用模板。"""
    return [
        {"key": k, "name": v.name, "industry": v.industry, "description": v.description}
        for k, v in TEMPLATES.items()
    ]


def get_all_template_keys() -> list[str]:
    """获取所有模板key。"""
    return list(TEMPLATES.keys())
