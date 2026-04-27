"""
天眼 — 虚拟人群生成器
Population Generator for Tianyan Platform

基于人口统计学数据和大语言模型，生成具有真实行为模式的虚拟消费者群体。
"""

import json
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Demographics:
    """人口统计学属性"""
    age: int
    gender: str  # "male" / "female"
    city: str
    city_tier: int  # 1, 2, 3
    monthly_income: float
    education: str
    marital_status: str
    occupation: str


@dataclass
class ConsumptionProfile:
    """消费画像"""
    monthly_spending: float
    top_categories: List[str]
    preferred_channels: List[str]
    brand_loyalty: float  # 0-1
    price_sensitivity: float  # 0-1
    impulse_buying: float  # 0-1
    research_before_buy: float  # 0-1


@dataclass
class Personality:
    """人格特征（大五人格 + 消费人格）"""
    openness: float  # 开放性
    conscientiousness: float  # 尽责性
    extraversion: float  # 外向性
    agreeableness: float  # 宜人性
    neuroticism: float  # 神经质
    # 消费人格
    trend_follower: float  # 潮流追随度
    risk_averse: float  # 风险规避度
    social_buyer: float  # 社交购买倾向


@dataclass
class PurchaseRecord:
    """购买记录"""
    date: str
    category: str
    product: str
    price: float
    channel: str
    satisfaction: float  # 1-5
    review: Optional[str] = None


@dataclass
class VirtualConsumer:
    """虚拟消费者"""
    id: str
    demographics: Demographics
    consumption: ConsumptionProfile
    personality: Personality
    values: List[str]
    purchase_history: List[PurchaseRecord] = field(default_factory=list)
    social_network_size: int = 150
    profile_narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "demographics": self.demographics.__dict__,
            "consumption": self.consumption.__dict__,
            "personality": self.personality.__dict__,
            "values": self.values,
            "purchase_history": [r.__dict__ for r in self.purchase_history],
            "social_network_size": self.social_network_size,
            "profile_narrative": self.profile_narrative,
        }


# ============================================================
# 配置数据
# ============================================================

CITY_TIERS = {
    1: ["上海", "北京", "深圳", "广州"],
    2: ["杭州", "成都", "南京", "武汉", "重庆", "苏州", "西安", "长沙",
        "天津", "郑州", "东莞", "青岛", "昆明", "合肥", "佛山"],
    3: ["洛阳", "潍坊", "遵义", "赣州", "湛江", "绵阳", "曲靖", "桂林",
        "连云港", "秦皇岛", "岳阳", "常德", "咸阳", "荆州", "承德"],
}

EDUCATION_POOL = ["初中", "高中", "中专", "大专", "本科", "硕士", "博士"]
EDUCATION_WEIGHTS = [0.05, 0.15, 0.08, 0.22, 0.35, 0.12, 0.03]

OCCUPATION_POOL = [
    "互联网/IT", "金融", "教育", "医疗", "制造业", "零售/服务业",
    "公务员", "自由职业", "学生", "退休", "全职妈妈", "建筑/工程",
    "传媒/文化", "农林牧渔", "物流/运输"
]

MARITAL_STATUS_POOL = ["未婚", "已婚未育", "已婚已育", "离异", "丧偶"]
MARITAL_WEIGHTS_BY_AGE = {
    (18, 25): [0.8, 0.1, 0.05, 0.05, 0.0],
    (26, 35): [0.3, 0.25, 0.35, 0.1, 0.0],
    (36, 50): [0.05, 0.05, 0.7, 0.15, 0.05],
    (51, 75): [0.02, 0.02, 0.65, 0.15, 0.16],
}

CONSUMPTION_CATEGORIES = {
    "美妆护肤": ["口红", "面膜", "精华液", "防晒霜", "粉底液"],
    "服饰鞋包": ["T恤", "牛仔裤", "运动鞋", "连衣裙", "羽绒服"],
    "餐饮外卖": ["奶茶", "外卖午餐", "火锅", "烧烤", "快餐"],
    "数码3C": ["手机", "耳机", "平板", "笔记本", "智能手表"],
    "家居家装": ["床上用品", "收纳", "装饰画", "灯具", "小家电"],
    "母婴用品": ["奶粉", "纸尿裤", "童装", "玩具", "辅食"],
    "保健品": ["维生素", "钙片", "鱼油", "益生菌", "蛋白粉"],
    "教育培训": ["网课", "线下培训", "教材", "考试报名"],
    "游戏娱乐": ["游戏充值", "视频会员", "电影票", "KTV"],
    "运动健身": ["健身卡", "运动装备", "瑜伽垫", "跑步机"],
    "生鲜食品": ["水果", "蔬菜", "肉类", "海鲜", "粮油"],
    "旅游度假": ["机票", "酒店", "景点门票", "旅行团"],
    "烟酒": ["香烟", "白酒", "啤酒", "红酒"],
    "宠物": ["猫粮", "狗粮", "宠物医疗", "宠物用品"],
}

CHANNELS = ["天猫", "京东", "拼多多", "淘宝", "抖音", "快手", "小红书",
            "线下商超", "便利店", "专卖店", "社区团购", "微信小程序"]


# ============================================================
# 生成器核心逻辑
# ============================================================

class PopulationGenerator:
    """
    虚拟人群生成器

    使用方式：
        generator = PopulationGenerator()
        population = generator.generate(n=10000, region="全国")
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> List[dict]:
        """加载人群画像模板"""
        profile_path = Path(__file__).parent.parent / "data" / "virtual-population.json"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("population_profiles", [])
        return []

    def generate(self, n: int = 10000, region: str = "全国",
                 age_range: Tuple[int, int] = (18, 65),
                 income_level: str = "mixed") -> List[VirtualConsumer]:
        """
        生成 n 个虚拟消费者

        Args:
            n: 生成数量
            region: 区域（全国/华东/华南/华北/西南/西北/东北）
            age_range: 年龄范围
            income_level: 收入水平（low/mixed/high）

        Returns:
            List[VirtualConsumer] 虚拟消费者列表
        """
        print(f"👁️ 天眼：正在生成 {n:,} 位虚拟消费者...")
        consumers = []

        # 确定各画像的分配比例
        allocations = self._allocate_by_profile(n)

        for profile, count in allocations.items():
            for i in range(count):
                consumer = self._generate_single_consumer(
                    profile_id=profile,
                    region=region,
                    age_range=age_range,
                    income_level=income_level,
                )
                consumers.append(consumer)

        self.rng.shuffle(consumers)

        # 重新分配ID
        for idx, consumer in enumerate(consumers):
            consumer.id = f"TC-{idx:06d}"

        print(f"✅ 生成完成：{len(consumers):,} 位虚拟消费者")
        return consumers

    def _allocate_by_profile(self, n: int) -> Dict[str, int]:
        """按画像比例分配人数"""
        allocations = {}
        remaining = n

        for profile in self.profiles:
            pid = profile["id"]
            share = profile.get("population_share", 0.1)
            count = int(n * share)
            allocations[pid] = count
            remaining -= count

        # 将余数分配给最大群体
        if remaining > 0 and allocations:
            max_pid = max(allocations, key=allocations.get)
            allocations[max_pid] += remaining

        return allocations

    def _generate_single_consumer(self, profile_id: str, region: str,
                                   age_range: Tuple[int, int],
                                   income_level: str) -> VirtualConsumer:
        """生成单个虚拟消费者"""
        profile = self._get_profile(profile_id)

        # 1. 人口统计学属性
        demographics = self._generate_demographics(profile, region, age_range, income_level)

        # 2. 消费画像
        consumption = self._generate_consumption(profile, demographics)

        # 3. 人格特征
        personality = self._generate_personality(profile, demographics)

        # 4. 价值观
        values = profile.get("values", ["品质生活"])

        # 5. 购买历史
        purchase_history = self._generate_purchase_history(demographics, consumption)

        # 6. 构造虚拟消费者
        consumer_id = hashlib.md5(
            f"{profile_id}-{demographics.age}-{demographics.city}-{self.rng.random()}"
            .encode()
        ).hexdigest()[:12]

        return VirtualConsumer(
            id=f"TC-{consumer_id}",
            demographics=demographics,
            consumption=consumption,
            personality=personality,
            values=values,
            purchase_history=purchase_history,
            social_network_size=self.rng.randint(50, 500),
        )

    def _get_profile(self, profile_id: str) -> dict:
        """获取指定画像模板"""
        for p in self.profiles:
            if p["id"] == profile_id:
                return p
        return self.profiles[0] if self.profiles else {}

    def _generate_demographics(self, profile: dict, region: str,
                                age_range: Tuple[int, int],
                                income_level: str) -> Demographics:
        """生成人口统计学属性"""
        # 年龄
        p_age_min = max(profile.get("age_range", [18, 65])[0], age_range[0])
        p_age_max = min(profile.get("age_range", [18, 65])[1], age_range[1])
        age = self.rng.randint(p_age_min, p_age_max)

        # 性别
        gender_ratio = profile.get("gender_ratio", {"female": 0.5, "male": 0.5})
        gender = "female" if self.rng.random() < gender_ratio.get("female", 0.5) else "male"

        # 城市等级和城市
        tier = self._pick_city_tier(profile)
        city = self._pick_city(tier, region)

        # 收入
        income_range = profile.get("monthly_income", {"min": 5000, "max": 15000, "avg": 8000})
        base_income = self.rng.gauss(income_range["avg"], (income_range["max"] - income_range["min"]) / 4)
        income = max(income_range["min"], min(income_range["max"], base_income))

        if income_level == "high":
            income *= 1.5
        elif income_level == "low":
            income *= 0.7

        # 教育
        education_weights = EDUCATION_WEIGHTS.copy()
        if income > 15000:
            education_weights = [0.02, 0.08, 0.05, 0.15, 0.4, 0.2, 0.1]
        education = self.rng.choices(EDUCATION_POOL, weights=education_weights, k=1)[0]

        # 婚姻状态
        marital_weights = [0.25, 0.2, 0.35, 0.12, 0.08]
        for age_range_key, weights in MARITAL_WEIGHTS_BY_AGE.items():
            if age_range_key[0] <= age <= age_range_key[1]:
                marital_weights = weights
                break
        marital_status = self.rng.choices(MARITAL_STATUS_POOL, weights=marital_weights, k=1)[0]

        # 职业
        occupation = self.rng.choice(OCCUPATION_POOL)

        return Demographics(
            age=age,
            gender=gender,
            city=city,
            city_tier=tier,
            monthly_income=round(income, 0),
            education=education,
            marital_status=marital_status,
            occupation=occupation,
        )

    def _pick_city_tier(self, profile: dict) -> int:
        """根据画像选择城市等级"""
        tier1 = profile.get("tier_1_ratio", 0.3)
        tier2 = profile.get("tier_2_ratio", 0.4)
        tier3 = profile.get("tier_3_ratio", 0.3)
        r = self.rng.random()
        if r < tier1:
            return 1
        elif r < tier1 + tier2:
            return 2
        else:
            return 3

    def _pick_city(self, tier: int, region: str) -> str:
        """选择具体城市"""
        cities = CITY_TIERS.get(tier, CITY_TIERS[3])
        if region != "全国":
            # 简化：根据区域筛选
            region_mapping = {
                "华东": ["上海", "杭州", "南京", "苏州", "合肥", "青岛", "连云港"],
                "华南": ["深圳", "广州", "东莞", "佛山", "湛江"],
                "华北": ["北京", "天津", "秦皇岛", "承德"],
                "西南": ["成都", "重庆", "昆明", "遵义", "绵阳", "曲靖", "桂林"],
                "华中": ["武汉", "长沙", "郑州", "岳阳", "常德", "荆州"],
                "西北": ["西安", "咸阳"],
                "东北": [],
            }
            region_cities = region_mapping.get(region, [])
            if region_cities:
                cities = [c for c in cities if c in region_cities] or cities
        return self.rng.choice(cities)

    def _generate_consumption(self, profile: dict, demographics: Demographics) -> ConsumptionProfile:
        """生成消费画像"""
        habits = profile.get("consumption_habits", {})

        # 月消费 = 收入的一定比例（恩格尔系数逻辑）
        income = demographics.monthly_income
        spending_ratio = self.rng.uniform(0.4, 0.8)
        monthly_spending = income * spending_ratio

        top_categories = habits.get("categories", ["服饰鞋包", "餐饮外卖"])
        channels = habits.get("preferred_channels", ["天猫", "京东"])

        return ConsumptionProfile(
            monthly_spending=round(monthly_spending, 0),
            top_categories=top_categories[:5],
            preferred_channels=channels[:4],
            brand_loyalty=self._jitter(habits.get("brand_loyalty", 0.5), 0.15),
            price_sensitivity=self._jitter(habits.get("price_sensitivity", 0.5), 0.15),
            impulse_buying=self._jitter(habits.get("impulse_buying", 0.5), 0.15),
            research_before_buy=self._jitter(habits.get("research_before_buy", 0.5), 0.15),
        )

    def _generate_personality(self, profile: dict, demographics: Demographics) -> Personality:
        """生成人格特征"""
        age = demographics.age
        # 年龄对人格的影响
        openness = self.rng.gauss(0.5, 0.15)
        if age < 30:
            openness += 0.1
        conscientiousness = self.rng.gauss(0.5, 0.15)
        if age > 40:
            conscientiousness += 0.1
        extraversion = self.rng.gauss(0.5, 0.2)
        agreeableness = self.rng.gauss(0.6, 0.15)
        neuroticism = self.rng.gauss(0.4, 0.15)

        return Personality(
            openness=self._clamp(openness),
            conscientiousness=self._clamp(conscientiousness),
            extraversion=self._clamp(extraversion),
            agreeableness=self._clamp(agreeableness),
            neuroticism=self._clamp(neuroticism),
            trend_follower=self._clamp(self.rng.gauss(0.5, 0.2)),
            risk_averse=self._clamp(self.rng.gauss(0.5, 0.2)),
            social_buyer=self._clamp(self.rng.gauss(0.5, 0.2)),
        )

    def _generate_purchase_history(self, demographics: Demographics,
                                    consumption: ConsumptionProfile) -> List[PurchaseRecord]:
        """生成购买历史"""
        history = []
        n_records = self.rng.randint(10, 80)
        today = datetime.now()

        for _ in range(n_records):
            days_ago = self.rng.randint(0, 365)
            date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # 选择品类
            category = self.rng.choice(consumption.top_categories)
            products = CONSUMPTION_CATEGORIES.get(category, ["未知商品"])
            product = self.rng.choice(products)

            # 价格（与品类和收入相关）
            base_price = self.rng.uniform(10, demographics.monthly_income * 0.1)
            price = round(base_price, 2)

            channel = self.rng.choice(consumption.preferred_channels)
            satisfaction = self._clamp(self.rng.gauss(0.7, 0.2)) * 5

            history.append(PurchaseRecord(
                date=date,
                category=category,
                product=product,
                price=price,
                channel=channel,
                satisfaction=round(satisfaction, 1),
            ))

        history.sort(key=lambda r: r.date, reverse=True)
        return history

    def _jitter(self, value: float, amount: float) -> float:
        """在值附近添加随机抖动"""
        return self._clamp(value + self.rng.uniform(-amount, amount))

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        """将值限制在范围内"""
        return round(max(low, min(high, value)), 3)

    def export(self, consumers: List[VirtualConsumer], path: str = "population.json"):
        """导出虚拟人群数据"""
        data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_consumers": len(consumers),
            "consumers": [c.to_dict() for c in consumers],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📁 已导出 {len(consumers):,} 位虚拟消费者到 {path}")

    def statistics(self, consumers: List[VirtualConsumer]) -> dict:
        """统计人群基本信息"""
        if not consumers:
            return {}

        ages = [c.demographics.age for c in consumers]
        incomes = [c.demographics.monthly_income for c in consumers]
        cities = {}
        tiers = {1: 0, 2: 0, 3: 0}

        for c in consumers:
            cities[c.demographics.city] = cities.get(c.demographics.city, 0) + 1
            tiers[c.demographics.city_tier] = tiers.get(c.demographics.city_tier, 0) + 1

        return {
            "total": len(consumers),
            "age": {
                "avg": round(sum(ages) / len(ages), 1),
                "min": min(ages),
                "max": max(ages),
            },
            "income": {
                "avg": round(sum(incomes) / len(incomes), 0),
                "median": round(sorted(incomes)[len(incomes) // 2], 0),
                "min": min(incomes),
                "max": max(incomes),
            },
            "city_tiers": tiers,
            "top_cities": sorted(cities.items(), key=lambda x: -x[1])[:10],
        }


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    region = sys.argv[2] if len(sys.argv) > 2 else "全国"

    generator = PopulationGenerator(seed=42)
    population = generator.generate(n=n, region=region)

    # 打印统计信息
    stats = generator.statistics(population)
    print(f"\n📊 人群统计:")
    print(f"   总人数: {stats['total']:,}")
    print(f"   平均年龄: {stats['age']['avg']}岁")
    print(f"   平均月收入: ¥{stats['income']['avg']:,.0f}")
    print(f"   城市等级分布: 一线{stats['city_tiers'][1]} / 二线{stats['city_tiers'][2]} / 三线{stats['city_tiers'][3]}")
    print(f"   Top 5 城市: {', '.join(f'{c}({n})' for c, n in stats['top_cities'][:5])}")

    # 导出
    output_path = sys.argv[3] if len(sys.argv) > 3 else "population.json"
    generator.export(population, output_path)
