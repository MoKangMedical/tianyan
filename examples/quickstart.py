"""
Quick Start — 天眼平台快速体验
"""

from tianyan import ConsumerEye, SyntheticPopulation

# 1. 创建合成人群（一线城市25-35岁女性，5000人）
population = SyntheticPopulation(
    region="一线城市",
    age_range=(25, 35),
    gender="female",
    size=5000,
    seed=42,
)

print("📊 合成人群统计：")
summary = population.summary()
print(f"  人数: {summary['size']}")
print(f"  平均年龄: {summary['avg_age']:.1f}")
print(f"  平均月收入: ¥{summary['avg_income']:.0f}")
print(f"  数字素养: {summary['avg_digital_literacy']:.1%}")
print(f"  消费画像分布: {summary['top_archetypes']}")

# 2. 创建消费眼
eye = ConsumerEye(model_provider="mimo")

# 3. 模拟GLP-1减重产品上市
result = eye.predict_product_launch(
    product_name="纤姿GLP-1减重胶囊",
    price=299,
    category="健康消费品",
    selling_point="国产GLP-1，每日一粒，6周见效",
    channels=["小红书", "抖音", "京东健康"],
    target_population=population,
)

print(f"\n🎯 预测结果：")
print(f"  购买意愿: {result.key_metrics['purchase_intent']:.1%}")
print(f"  预测置信度: {result.confidence:.1%}")
print(f"  社交传播率: {result.key_metrics.get('social_influence_rate', 0):.1%}")

print(f"\n💡 建议：")
for rec in result.recommendations:
    print(f"  • {rec}")

print(f"\n📈 分群洞察：")
for segment, metrics in result.segments.items():
    intent = metrics.get("purchase_intent", 0)
    print(f"  {segment}: 购买意愿 {intent:.1%}")
