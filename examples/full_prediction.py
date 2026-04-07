"""
天眼平台完整示例 — 展示中国特色商业预测能力

场景：一款国产GLP-1减重产品的上市全链路预测
"""

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    ChineseScenarioEngine,
)

print("=" * 60)
print("👁️ 天眼 (Tianyan) — 完整商业预测演示")
print("场景：纤姿GLP-1减重胶囊 上市全链路预测")
print("=" * 60)

# ═══════════════════════════════════════════════
# Step 1: 创建目标人群
# ═══════════════════════════════════════════════
print("\n📊 Step 1: 创建合成人群")

population = SyntheticPopulation(
    region="一线城市",
    age_range=(25, 45),
    gender="all",
    size=3000,
    seed=42,
)

summary = population.summary()
print(f"  ✅ 合成人群：{summary['size']}人")
print(f"  平均年龄：{summary['avg_age']:.1f}岁")
print(f"  平均月收入：¥{summary['avg_income']:.0f}")
print(f"  数字素养：{summary['avg_digital_literacy']:.1%}")
print(f"  消费画像TOP3：{list(summary['top_archetypes'].keys())[:3]}")

# ═══════════════════════════════════════════════
# Step 2: 产品上市预测（消费眼）
# ═══════════════════════════════════════════════
print("\n🎯 Step 2: 产品上市预测（消费眼）")

eye = ConsumerEye()
result = eye.predict_product_launch(
    product_name="纤姿GLP-1减重胶囊",
    price=299,
    category="健康消费品",
    selling_point="国产GLP-1，每日一粒，6周见效",
    channels=["小红书", "抖音", "京东健康"],
    target_population=population,
)

print(f"  购买意愿：{result.key_metrics['purchase_intent']:.1%}")
print(f"  预测置信度：{result.confidence:.1%}")
print(f"  社交传播率：{result.key_metrics.get('social_influence_rate', 0):.1%}")

print(f"\n  📈 分群洞察：")
for segment, metrics in sorted(result.segments.items()):
    intent = metrics.get("purchase_intent", 0)
    print(f"    {segment}: 购买意愿 {intent:.1%}")

print(f"\n  💡 建议：")
for rec in result.recommendations:
    print(f"    • {rec}")

# ═══════════════════════════════════════════════
# Step 3: KOL效果预测
# ═══════════════════════════════════════════════
print("\n🌟 Step 3: KOL效果预测")

cn_engine = ChineseScenarioEngine(population)

for kol_type in ["头部美妆博主", "垂类健康博主", "素人种草号"]:
    kol_result = cn_engine.predict_kol_effect(
        product_name="纤姿GLP-1减重胶囊",
        product_price=299,
        kol_type=kol_type,
    )
    print(f"\n  [{kol_type}]")
    print(f"    预估触达：{kol_result.predicted_reach:,}人")
    print(f"    互动率：{kol_result.predicted_engagement:.1%}")
    print(f"    转化率：{kol_result.predicted_conversion:.2%}")
    print(f"    ROI预估：{kol_result.roi_estimate:.1f}x")
    print(f"    最佳平台：{kol_result.best_platform}")

# ═══════════════════════════════════════════════
# Step 4: 直播带货预测
# ═══════════════════════════════════════════════
print("\n📺 Step 4: 直播带货预测")

for platform in ["抖音", "小红书"]:
    live_result = cn_engine.predict_livestream(
        product_name="纤姿GLP-1减重胶囊",
        product_price=299,
        platform=platform,
        discount_rate=0.15,
    )
    print(f"\n  [{platform}直播]")
    print(f"    预估观众：{live_result.predicted_viewers:,}人")
    print(f"    预估GMV：¥{live_result.predicted_gmv:,.0f}")
    print(f"    转化率：{live_result.predicted_conversion_rate:.2%}")
    print(f"    最佳时段：{live_result.best_time_slot}")
    print(f"    价格敏感人群影响：{live_result.price_sensitivity_impact:.1%}")

# ═══════════════════════════════════════════════
# Step 5: 电商渠道优化
# ═══════════════════════════════════════════════
print("\n🛒 Step 5: 电商渠道优化")

channel_result = cn_engine.optimize_ecommerce_channel(
    product_name="纤姿GLP-1减重胶囊",
    product_price=299,
    product_category="美妆",
)

print(f"  最佳平台：{channel_result['best_platform']}")
print(f"\n  平台排名：")
for item in channel_result["platform_ranking"]:
    print(f"    {item['platform']}: 得分 {item['score']:.3f} — {item['recommendation']}")

# ═══════════════════════════════════════════════
# Step 6: 小红书种草预测
# ═══════════════════════════════════════════════
print("\n📕 Step 6: 小红书种草预测")

seeding_result = cn_engine.predict_xiaohongshu_seeding(
    product_name="纤姿GLP-1减重胶囊",
    product_price=299,
    content_style="种草笔记",
    num_notes=200,
)

print(f"  内容数量：{seeding_result['num_notes']}篇")
print(f"  预估曝光：{seeding_result['predicted_impressions']:,}")
print(f"  预估互动：{seeding_result['predicted_interactions']:,}")
print(f"  互动率：{seeding_result['predicted_engagement_rate']:.2%}")
print(f"  最佳受众：{seeding_result['best_audience']}")
print(f"\n  内容建议：")
for s in seeding_result["content_suggestions"]:
    print(f"    • {s}")

# ═══════════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════════
print("\n" + "=" * 60)
print("📊 全链路预测汇总")
print("=" * 60)
print(f"""
产品：纤姿GLP-1减重胶囊（¥299）
目标：一线城市25-45岁人群

┌─────────────────┬───────────────────────────────┐
│ 维度            │ 预测结果                       │
├─────────────────┼───────────────────────────────┤
│ 产品购买意愿    │ {result.key_metrics['purchase_intent']:.1%}                         │
│ KOL最优选择     │ 垂类健康博主（信任度最高）      │
│ 直播GMV（抖音） │ ¥{cn_engine.predict_livestream('产品', 299, '抖音').predicted_gmv:>10,.0f}             │
│ 电商最优渠道    │ {channel_result['best_platform']:<10}                      │
│ 小红书种草曝光  │ {seeding_result['predicted_impressions']:>10,}                      │
└─────────────────┴───────────────────────────────┘

💡 核心建议：
  1. 首发渠道：京东健康（信任度高）+ 小红书（种草先行）
  2. KOL策略：垂类健康博主 > 素人种草 > 头部美妆
  3. 直播策略：抖音20:00-22:00时段，15%折扣
  4. 定价策略：¥299可接受，一线城市可尝试¥349
""")
