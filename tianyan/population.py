"""
合成人群工厂 (Synthetic Population Factory)

根据中国统计数据生成合成人群画像。
核心原则：100%合成数据，不使用任何真实个人信息。

数据来源（公开统计）：
- 国家统计局年鉴
- 公开消费行为报告
- 公开社交媒体画像统计（脱敏聚合数据）
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional


# 中国城市分级（公开数据）
CITY_TIERS = {
    "一线城市": ["北京", "上海", "广州", "深圳"],
    "新一线城市": ["成都", "杭州", "重庆", "武汉", "西安", "苏州", "南京", "天津", "长沙", "郑州", "东莞", "青岛", "沈阳", "宁波", "昆明"],
    "二线城市": ["大连", "厦门", "合肥", "佛山", "福州", "哈尔滨", "济南", "温州", "南宁", "长春", "石家庄", "太原", "贵阳", "南昌", "金华", "常州", "珠海", "惠州", "嘉兴", "南通", "徐州"],
    "三线及以下": ["其他地级市", "县级市", "县城", "乡镇"],
}

# 年龄段分布（基于第七次人口普查，近似）
AGE_DISTRIBUTION = {
    "18-24": 0.12,
    "25-34": 0.18,
    "35-44": 0.17,
    "45-54": 0.19,
    "55-64": 0.17,
    "65+": 0.17,
}

# 收入分层（基于统计局数据，近似）
INCOME_BRACKETS = {
    "低收入": {"range": (2000, 5000), "pct": 0.35},
    "中等收入": {"range": (5000, 15000), "pct": 0.40},
    "中高收入": {"range": (15000, 30000), "pct": 0.15},
    "高收入": {"range": (30000, 100000), "pct": 0.08},
    "超高收入": {"range": (100000, 500000), "pct": 0.02},
}

# 消费行为画像维度
CONSUMER_ARCHETYPES = [
    "精打细算型",     # 价格敏感，追求性价比
    "品质追求型",     # 愿意为品质付溢价
    "跟风种草型",     # 容易被KOL/社交平台影响
    "理性决策型",     # 深度研究后才购买
    "冲动消费型",     # 容易被促销/限时折扣打动
    "品牌忠诚型",     # 固定购买特定品牌
    "尝鲜探索型",     # 喜欢尝试新品/新品牌
    "社交驱动型",     # 购买决策受社交圈影响大
]


@dataclass
class PopulationProfile:
    """单个合成人口画像。"""
    agent_id: str
    age: int
    gender: str
    city_tier: str
    city: str
    monthly_income: int
    education: str
    occupation: str
    consumer_archetype: str
    digital_literacy: float  # 0-1, 数字素养
    price_sensitivity: float  # 0-1
    brand_loyalty: float  # 0-1
    social_influence: float  # 0-1, 受社交影响程度
    health_consciousness: float  # 0-1
    risk_tolerance: float  # 0-1
    channels: list[str] = field(default_factory=list)  # 常用渠道
    interests: list[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """转换为LLM可理解的画像描述。"""
        return f"""你是一位{self.age}岁{self.gender}性，住在{self.city}（{self.city_tier}）。
学历：{self.education}，职业：{self.occupation}，月收入约{self.monthly_income}元。
消费风格：{self.consumer_archetype}
价格敏感度：{self.price_sensitivity:.0%}，品牌忠诚度：{self.brand_loyalty:.0%}
受社交影响程度：{self.social_influence:.0%}，健康意识：{self.health_consciousness:.0%}
常用渠道：{', '.join(self.channels)}
兴趣爱好：{', '.join(self.interests)}"""


class SyntheticPopulation:
    """
    合成人群工厂。

    基于中国公开统计数据，生成具有统计代表性的合成人群。
    所有数据均为合成生成，不含任何真实个人信息。
    """

    def __init__(
        self,
        region: str = "全国",
        age_range: tuple[int, int] = (18, 65),
        gender: str = "all",
        size: int = 1000,
        income_filter: str = "",
        city_tier_filter: str = "",
        seed: int | None = None,
    ):
        self.region = region
        self.age_range = age_range
        self.gender = gender
        self.size = size
        self.income_filter = income_filter
        self.city_tier_filter = city_tier_filter

        if seed is not None:
            random.seed(seed)

        self.profiles: list[PopulationProfile] = self._generate()

    def _generate(self) -> list[PopulationProfile]:
        """生成合成人群。"""
        profiles = []
        for i in range(self.size):
            profile = self._generate_single(i)
            if profile:
                profiles.append(profile)
        return profiles

    def _generate_single(self, idx: int) -> Optional[PopulationProfile]:
        """生成单个合成人口画像。"""
        # 年龄
        age = random.randint(self.age_range[0], self.age_range[1])

        # 性别
        if self.gender == "all":
            gender = random.choice(["男", "女"])
        else:
            gender = "女" if self.gender == "female" else "男"

        # 城市
        if self.city_tier_filter:
            tier = self.city_tier_filter
        elif self.region != "全国":
            tier = self.region
        else:
            tier = random.choices(
                list(CITY_TIERS.keys()),
                weights=[0.15, 0.20, 0.25, 0.40],
            )[0]

        city = random.choice(CITY_TIERS.get(tier, ["未知"]))

        # 收入
        income_bracket = random.choices(
            list(INCOME_BRACKETS.keys()),
            weights=[b["pct"] for b in INCOME_BRACKETS.values()],
        )[0]
        if self.income_filter:
            income_bracket = self.income_filter
        income_range = INCOME_BRACKETS[income_bracket]["range"]
        monthly_income = random.randint(income_range[0], income_range[1])

        # 根据城市等级调整收入
        tier_multiplier = {"一线城市": 1.5, "新一线城市": 1.2, "二线城市": 1.0, "三线及以下": 0.7}
        monthly_income = int(monthly_income * tier_multiplier.get(tier, 1.0))

        # 学历（与年龄和城市相关）
        education = self._random_education(age, tier)

        # 职业
        occupation = self._random_occupation(age, education)

        # 消费画像
        archetype = random.choice(CONSUMER_ARCHETYPES)

        # 行为指标
        digital_literacy = self._calc_digital_literacy(age, tier, education)
        price_sensitivity = self._calc_price_sensitivity(income_bracket, archetype)
        brand_loyalty = self._calc_brand_loyalty(archetype, income_bracket)
        social_influence = self._calc_social_influence(age, archetype)
        health_consciousness = self._calc_health_consciousness(age, income_bracket)
        risk_tolerance = self._calc_risk_tolerance(age, income_bracket)

        # 渠道
        channels = self._random_channels(age, tier, digital_literacy)

        # 兴趣
        interests = self._random_interests(age, gender)

        return PopulationProfile(
            agent_id=f"tianyan_{idx:06d}",
            age=age,
            gender=gender,
            city_tier=tier,
            city=city,
            monthly_income=monthly_income,
            education=education,
            occupation=occupation,
            consumer_archetype=archetype,
            digital_literacy=digital_literacy,
            price_sensitivity=price_sensitivity,
            brand_loyalty=brand_loyalty,
            social_influence=social_influence,
            health_consciousness=health_consciousness,
            risk_tolerance=risk_tolerance,
            channels=channels,
            interests=interests,
        )

    def _random_education(self, age: int, city_tier: str) -> str:
        base_weights = {"初中及以下": 0.2, "高中/中专": 0.25, "大专": 0.2, "本科": 0.25, "硕士及以上": 0.1}
        if city_tier == "一线城市":
            base_weights["本科"] += 0.15
            base_weights["硕士及以上"] += 0.1
            base_weights["初中及以下"] -= 0.1
        if age > 50:
            base_weights["初中及以下"] += 0.15
            base_weights["硕士及以上"] -= 0.05
        return random.choices(list(base_weights.keys()), weights=list(base_weights.values()))[0]

    def _random_occupation(self, age: int, education: str) -> str:
        occupations = {
            "学生": (18, 25, 0.3),
            "互联网/IT": (22, 40, 0.12),
            "金融": (23, 45, 0.08),
            "医疗健康": (23, 55, 0.06),
            "教育": (23, 55, 0.08),
            "制造业": (20, 55, 0.12),
            "服务业": (18, 55, 0.15),
            "公务员/事业单位": (23, 55, 0.08),
            "自由职业": (22, 50, 0.06),
            "退休": (55, 80, 0.1),
            "个体经营": (22, 60, 0.08),
        }
        valid = {k: v[2] for k, v in occupations.items() if v[0] <= age <= v[1]}
        if not valid:
            return "其他"
        total = sum(valid.values())
        return random.choices(list(valid.keys()), weights=[v/total for v in valid.values()])[0]

    def _calc_digital_literacy(self, age: int, tier: str, education: str) -> float:
        base = 0.5
        base -= max(0, (age - 30)) * 0.01
        if tier in ("一线城市", "新一线城市"):
            base += 0.15
        if education in ("本科", "硕士及以上"):
            base += 0.1
        return max(0.1, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _calc_price_sensitivity(self, income_bracket: str, archetype: str) -> float:
        base = {"低收入": 0.85, "中等收入": 0.6, "中高收入": 0.4, "高收入": 0.2, "超高收入": 0.1}
        val = base.get(income_bracket, 0.5)
        if "精打细算" in archetype:
            val += 0.15
        elif "品质追求" in archetype:
            val -= 0.15
        return max(0.0, min(1.0, val + random.uniform(-0.05, 0.05)))

    def _calc_brand_loyalty(self, archetype: str, income_bracket: str) -> float:
        base = 0.4
        if "品牌忠诚" in archetype:
            base += 0.35
        elif "尝鲜探索" in archetype:
            base -= 0.2
        if income_bracket in ("高收入", "超高收入"):
            base += 0.1
        return max(0.0, min(1.0, base + random.uniform(-0.05, 0.05)))

    def _calc_social_influence(self, age: int, archetype: str) -> float:
        base = 0.5
        if age < 30:
            base += 0.15
        if "跟风种草" in archetype or "社交驱动" in archetype:
            base += 0.25
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _calc_health_consciousness(self, age: int, income_bracket: str) -> float:
        base = 0.4
        if age > 40:
            base += 0.2
        if income_bracket in ("中高收入", "高收入", "超高收入"):
            base += 0.15
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _calc_risk_tolerance(self, age: int, income_bracket: str) -> float:
        base = 0.5
        if age < 35:
            base += 0.15
        if income_bracket in ("高收入", "超高收入"):
            base += 0.1
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _random_channels(self, age: int, tier: str, digital: float) -> list[str]:
        all_channels = ["微信", "抖音", "小红书", "淘宝", "京东", "拼多多", "微博", "B站", "知乎", "线下门店"]
        weights = {
            "微信": 0.9, "抖音": 0.7 if age < 45 else 0.4, "小红书": 0.6 if age < 35 else 0.2,
            "淘宝": 0.8, "京东": 0.6, "拼多多": 0.5 if tier in ("三线及以下", "二线城市") else 0.3,
            "微博": 0.3, "B站": 0.4 if age < 30 else 0.1, "知乎": 0.3 if age < 40 else 0.1,
            "线下门店": 0.5 if age > 40 or digital < 0.4 else 0.3,
        }
        return [ch for ch, w in weights.items() if random.random() < w]

    def _random_interests(self, age: int, gender: str) -> list[str]:
        interests_pool = {
            "young_female": ["美妆", "穿搭", "美食", "旅行", "健身", "追剧", "宠物", "摄影"],
            "young_male": ["数码", "游戏", "运动", "汽车", "科技", "健身", "电影", "音乐"],
            "mid_female": ["育儿", "健康", "理财", "美食", "家居", "旅行", "读书"],
            "mid_male": ["投资", "汽车", "科技", "健身", "摄影", "钓鱼", "户外"],
            "senior": ["健康养生", "广场舞", "书法", "旅游", "种花", "带孙子"],
        }
        if age < 35:
            pool = interests_pool["young_female" if gender == "女" else "young_male"]
        elif age < 55:
            pool = interests_pool["mid_female" if gender == "女" else "mid_male"]
        else:
            pool = interests_pool["senior"]
        return random.sample(pool, min(random.randint(2, 4), len(pool)))

    def summary(self) -> dict[str, Any]:
        """人群摘要统计。"""
        if not self.profiles:
            return {}
        return {
            "size": len(self.profiles),
            "avg_age": sum(p.age for p in self.profiles) / len(self.profiles),
            "gender_dist": {
                "男": sum(1 for p in self.profiles if p.gender == "男") / len(self.profiles),
                "女": sum(1 for p in self.profiles if p.gender == "女") / len(self.profiles),
            },
            "avg_income": sum(p.monthly_income for p in self.profiles) / len(self.profiles),
            "top_archetypes": self._top_archetypes(),
            "avg_digital_literacy": sum(p.digital_literacy for p in self.profiles) / len(self.profiles),
        }

    def _top_archetypes(self) -> dict[str, int]:
        from collections import Counter
        counts = Counter(p.consumer_archetype for p in self.profiles)
        return dict(counts.most_common(5))
