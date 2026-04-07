#!/usr/bin/env python3
"""
天眼 (Tianyan) 综合预测演示

展示完整的预测流程：
1. 创建多场景合成人群
2. 消费眼：产品上市 + 定价 + 广告
3. KOL效果预测
4. 直播带货预测
5. 电商渠道优化
6. 小红书种草预测
7. 政策眼：民生政策评估
8. 输出格式化报告
"""

import json
import sys
import time
from pathlib import Path

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    PolicyEye,
    ChineseScenarioEngine,
    ComplianceChecker,
)


def divider(title: str):
    """打印分隔线。"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_json(data: dict, indent: int = 2):
    """打印JSON（中文不转义）。"""
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def main():
    start = time.time()

    # ================================================================
    # Step 1: 创建多场景合成人群
    # ================================================================
    divider("📊 Step 1: 创建合成人群")

    # 全国通用人群
    pop_national = SyntheticPopulation(size=500, region="全国", seed=42)
    summary = pop_national.summary()
    print(f"🌍 全国人群: {summary['size']}人")
    print(f"   平均年龄: {summary['avg_age']:.1f}岁")
    print(f"   性别比: 男{summary['gender_dist']['男']:.0%} / 女{summary['gender_dist']['女']:.0%}")
    print(f"   平均月收入: ¥{summary['avg_income']:,.0f}")
    print(f"   数字素养: {summary['avg_digital_literacy']:.2f}")
    print(f"   消费画像分布: {summary['top_archetypes']}")

    # 一线城市年轻女性（美妆核心人群）
    pop_young_female = SyntheticPopulation(
        size=200, region="一线城市", age_range=(18, 30),
        gender="female", seed=42,
    )
    print(f"\n👩 一线城市年轻女性: {pop_young_female.summary()['size']}人")

    # 下沉市场人群
    pop_lower = SyntheticPopulation(
        size=200, region="三线及以下", seed=42,
    )
    print(f"🏘️  下沉市场人群: {pop_lower.summary()['size']}人")

    # ================================================================
    # Step 2: 消费眼 — 产品上市预测
    # ================================================================
    divider("🛒 Step 2: 消费眼 — 新品上市预测")

    eye = ConsumerEye()

    result = eye.predict_product_launch(
        product_name="玻尿酸精华液",
        price=199,
        category="美妆护肤",
        selling_point="医美级玻尿酸，28天可见淡纹效果",
        channels=["小红书", "抖音", "天猫"],
        target_population=pop_young_female,
    )

    print(f"产品: {result.scenario_name}")
    print(f"购买意愿: {result.key_metrics['purchase_intent']:.1%}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"建议:")
    for rec in result.recommendations:
        print(f"  → {rec}")

    # ================================================================
    # Step 3: 消费眼 — 定价优化
    # ================================================================
    divider("💰 Step 3: 消费眼 — 定价策略优化")

    pricing = eye.optimize_pricing(
        product_name="玻尿酸精华液",
        price_low=99,
        price_high=399,
        target_population=pop_national,
    )

    print(f"定价优化结果:")
    print(f"  置信度: {pricing.confidence:.2f}")
    for rec in pricing.recommendations:
        print(f"  → {rec}")

    # 分群价格敏感度
    if pricing.segments:
        print(f"  分群洞察:")
        for seg, metrics in pricing.segments.items():
            pi = metrics.get("purchase_intent", 0)
            print(f"    {seg}: 购买意愿 {pi:.1%}")

    # ================================================================
    # Step 4: 消费眼 — 广告创意测试
    # ================================================================
    divider("🎯 Step 4: 消费眼 — 广告创意测试")

    ad_result = eye.test_ad_creative(
        ad_theme="医美级护肤，28天焕新",
        channel="抖音",
        style="种草风",
        target_population=pop_young_female,
    )

    print(f"广告: {ad_result.scenario_name}")
    print(f"点击意愿: {ad_result.key_metrics.get('click_intent', 0):.1%}")

    # ================================================================
    # Step 5: KOL效果预测
    # ================================================================
    divider("🔥 Step 5: KOL效果预测")

    engine = ChineseScenarioEngine(pop_young_female)

    kol_types = ["头部美妆博主", "素人种草号"]
    for kol_type in kol_types:
        kol = engine.predict_kol_effect(
            product_name="玻尿酸精华液",
            product_price=199,
            kol_type=kol_type,
        )
        print(f"  KOL类型: {kol.kol_type}")
        print(f"  预估触达: {kol.predicted_reach:,}人")
        print(f"  互动率: {kol.predicted_engagement:.1%}")
        print(f"  转化率: {kol.predicted_conversion:.2%}")
        print(f"  最佳平台: {kol.best_platform}")
        print(f"  ROI预估: {kol.roi_estimate:.1f}")
        print()

    # ================================================================
    # Step 6: 直播带货预测
    # ================================================================
    divider("📺 Step 6: 直播带货预测")

    platforms = ["抖音", "快手"]
    for platform in platforms:
        live = engine.predict_livestream(
            product_name="玻尿酸精华液",
            product_price=199,
            platform=platform,
            discount_rate=0.25,
        )
        print(f"  平台: {live.platform}")
        print(f"  预估观众: {live.predicted_viewers:,}人")
        print(f"  预估GMV: ¥{live.predicted_gmv:,.0f}")
        print(f"  转化率: {live.predicted_conversion_rate:.2%}")
        print(f"  最佳时段: {live.best_time_slot}")
        print()

    # ================================================================
    # Step 7: 电商渠道优化
    # ================================================================
    divider("🏪 Step 7: 电商渠道优化")

    channel_result = engine.optimize_ecommerce_channel(
        product_name="玻尿酸精华液",
        product_price=199,
        product_category="美妆",
    )

    print(f"最佳渠道: {channel_result['best_platform']}")
    print(f"渠道排名:")
    for p in channel_result["platform_ranking"]:
        print(f"  {p['platform']}: 得分 {p['score']:.3f} — {p['recommendation']}")

    # ================================================================
    # Step 8: 小红书种草预测
    # ================================================================
    divider("📕 Step 8: 小红书种草预测")

    seeding = engine.predict_xiaohongshu_seeding(
        product_name="玻尿酸精华液",
        product_price=199,
        content_style="种草笔记",
        num_notes=200,
    )

    print(f"内容风格: {seeding['content_style']}")
    print(f"笔记数量: {seeding['num_notes']}")
    print(f"预估曝光: {seeding['predicted_impressions']:,}")
    print(f"预估互动: {seeding['predicted_interactions']:,}")
    print(f"互动率: {seeding['predicted_engagement_rate']:.2%}")
    print(f"最佳受众: {seeding['best_audience']}")
    print(f"内容建议:")
    for s in seeding["content_suggestions"]:
        print(f"  → {s}")

    # ================================================================
    # Step 9: 政策眼 — 医保政策评估
    # ================================================================
    divider("🏛️ Step 9: 政策眼 — 医保政策评估")

    policy_eye = PolicyEye()

    policy_result = policy_eye.assess_policy_impact(
        policy_name="个人医保账户改革",
        scope="全国",
        changes="门诊报销比例从50%提高到70%，个人账户划入比例适当降低",
        target_population=pop_national,
        policy_category="healthcare",
    )

    print(f"政策: {policy_result.scenario_name}")
    print(f"支持率: {policy_result.key_metrics.get('approval_rate', 0):.1%}")
    print(f"置信度: {policy_result.confidence:.2f}")

    # ================================================================
    # Step 10: 合规检查演示
    # ================================================================
    divider("🛡️ Step 10: 合规检查")

    checker = ComplianceChecker()

    # 正常场景
    try:
        checker.check_scenario("product_launch", {"product": "洗发水"})
        print("✅ 正常商业场景：通过")
    except Exception as e:
        print(f"❌ 异常: {e}")

    # 红线测试
    red_lines = [
        ("election", {"type": "投票"}),
        ("product_launch", {"name": "选举投票器"}),
    ]
    for category, params in red_lines:
        try:
            checker.check_scenario(category, params)
            print(f"❌ 红线场景 '{category}' 未被拦截!")
        except Exception:
            print(f"✅ 红线场景 '{category}' 已正确拦截")

    # ================================================================
    # 总结
    # ================================================================
    elapsed = time.time() - start
    divider("📋 综合预测报告总结")
    print(f"产品: 玻尿酸精华液 ¥199")
    print(f"核心人群: 一线城市18-30岁女性")
    print(f"购买意愿: {result.key_metrics['purchase_intent']:.1%}")
    print(f"最佳渠道: {channel_result['best_platform']}")
    print(f"直播预估GMV: ¥{engine.predict_livestream('玻尿酸精华液', 199, '抖音', 0.25).predicted_gmv:,.0f}")
    print(f"小红书预估曝光: {seeding['predicted_impressions']:,}")
    print(f"政策支持率: {policy_result.key_metrics.get('approval_rate', 0):.1%}")
    print(f"\n⏱️  总耗时: {elapsed:.1f}秒")
    print(f"\n{'='*60}")
    print(f"  天眼 Tianyan — 用数据洞察中国消费市场")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
