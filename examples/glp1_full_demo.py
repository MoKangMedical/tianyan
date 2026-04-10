#!/usr/bin/env python3
"""
GLP-1减重产品上市 — 天眼端到端预测演示

使用天眼平台完成GLP-1减重产品上市的完整预测流程：
1. 创建合成人群（25-45岁都市白领，BMI超标）
2. 消费眼预测（产品上市反应）
3. 小红书种草预测
4. 直播带货预测
5. 生成麦肯锡级报告

运行：python3 examples/glp1_full_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    ChineseScenarioEngine,
    McKinseyReportGenerator,
    ScenarioEngine,
    Scenario,
    get_template,
)


def main():
    print("=" * 70)
    print("👁️  天眼 Tianyan — GLP-1减重产品上市预测")
    print("=" * 70)

    # ===== 第一步：创建合成人群 =====
    print("\n📊 第一步：创建合成人群")
    print("-" * 40)

    population = SyntheticPopulation(
        region="一线城市",
        age_range=(25, 45),
        gender="all",
        size=1000,
        seed=42,
    )
    summary = population.summary()
    print(f"  人群规模: {summary['size']} 人")
    print(f"  平均年龄: {summary['avg_age']:.1f} 岁")
    print(f"  平均月收入: ¥{summary['avg_income']:,.0f}")
    print(f"  数字素养: {summary['avg_digital_literacy']:.2f}")
    print(f"  主要画像: {', '.join(summary['top_archetypes'][:3])}")

    # ===== 第二步：消费眼预测 =====
    print("\n👁️ 第二步：消费眼 — 产品上市预测")
    print("-" * 40)

    eye = ConsumerEye()
    launch_result = eye.predict_product_launch(
        product_name="SlimGuard GLP-1减重针",
        price=399,
        category="消费医疗",
        selling_point="一周一次，科学减重，平均减重15%",
        channels=["抖音", "小红书", "微信"],
        target_population=population,
    )

    print(f"  场景: {launch_result.scenario_name}")
    for metric, value in launch_result.key_metrics.items():
        if isinstance(value, float):
            print(f"  {metric}: {value:.1%}" if value <= 1 else f"  {metric}: {value:.2f}")
        else:
            print(f"  {metric}: {value}")

    if launch_result.recommendations:
        print("\n  📌 建议:")
        for r in launch_result.recommendations[:5]:
            print(f"    • {r}")

    # ===== 第三步：定价优化 =====
    print("\n💰 第三步：消费眼 — 定价优化")
    print("-" * 40)

    pricing_result = eye.optimize_pricing(
        product_name="SlimGuard GLP-1减重针",
        price_low=199,
        price_high=799,
        target_population=population,
    )
    print(f"  场景: {pricing_result.scenario_name}")
    for metric, value in pricing_result.key_metrics.items():
        if isinstance(value, float):
            print(f"  {metric}: {value:.2f}")
        else:
            print(f"  {metric}: {value}")

    # ===== 第四步：小红书种草预测 =====
    print("\n📕 第四步：小红书种草预测")
    print("-" * 40)

    engine = ChineseScenarioEngine(population)
    xhs_result = engine.predict_xiaohongshu_seeding(
        product_name="SlimGuard GLP-1减重针",
        product_price=399,
        content_style="种草笔记",
        num_notes=200,
    )
    print(f"  预计曝光: {xhs_result['predicted_impressions']:,}")
    print(f"  预计互动: {xhs_result['predicted_interactions']:,}")
    print(f"  预计互动率: {xhs_result['predicted_engagement_rate']:.2%}")
    print(f"  内容建议:")
    for s in xhs_result["content_suggestions"][:5]:
        print(f"    • {s}")

    # ===== 第五步：KOL预测 =====
    print("\n🌟 第五步：KOL带货效果预测")
    print("-" * 40)

    for kol_type in ["头部美妆博主", "垂类健康博主", "素人种草号"]:
        kol_result = engine.predict_kol_effect(
            product_name="SlimGuard GLP-1减重针",
            product_price=399,
            kol_type=kol_type,
        )
        print(f"  [{kol_type}]")
        print(f"    预计触达: {kol_result.predicted_reach:,}")
        print(f"    预计互动: {kol_result.predicted_engagement:,.0f}")
        print(f"    预计转化: {kol_result.predicted_conversion:.2%}")
        print(f"    最佳平台: {kol_result.best_platform}")

    # ===== 第六步：直播带货预测 =====
    print("\n📺 第六步：直播带货预测")
    print("-" * 40)

    for platform in ["抖音", "抖音电商"]:
        ls_result = engine.predict_livestream(
            product_name="SlimGuard GLP-1减重针",
            product_price=399,
            platform=platform,
            discount_rate=0.15,
        )
        print(f"  [{platform}]")
        print(f"    预计观众: {ls_result.predicted_viewers:,}")
        print(f"    预计GMV: ¥{ls_result.predicted_gmv:,.0f}")
        print(f"    预计转化率: {ls_result.predicted_conversion_rate:.2%}")
        print(f"    最佳时段: {ls_result.best_time_slot}")

    # ===== 第七步：渠道优化 =====
    print("\n🛒 第七步：电商渠道优化")
    print("-" * 40)

    channel_result = engine.optimize_ecommerce_channel(
        product_name="SlimGuard GLP-1减重针",
        product_price=399,
        product_category="消费医疗",
    )
    print(f"  最佳平台: {channel_result['best_platform']}")
    print(f"  平台排名:")
    for p in channel_result["platform_ranking"]:
        print(f"    {p['rank']}. {p['platform']} — 预计GMV: ¥{p['predicted_gmv']:,.0f}")

    # ===== 第八步：麦肯锡级报告 =====
    print("\n📋 第八步：生成麦肯锡级报告")
    print("-" * 40)

    # 用ScenarioEngine生成SimulationResult（报告生成器需要的类型）
    scenario_engine = ScenarioEngine(population)
    scenario = Scenario(
        name="SlimGuard GLP-1减重针上市",
        description="定价399元的GLP-1减重产品，一周一次注射，目标25-45岁都市白领",
        category="general",
    )
    sim_result = scenario_engine.run(scenario, rounds=3, social_propagation=True)

    report_gen = McKinseyReportGenerator()
    report = report_gen.generate_product_launch_report(
        product_name="SlimGuard GLP-1减重针",
        simulation_result=sim_result,
    )

    md = report.to_markdown()
    print(f"\n{md}")

    # ===== 保存报告 =====
    report_path = "/root/tianyan/examples/glp1_report.md"
    with open(report_path, "w") as f:
        f.write(md)
    print(f"\n📄 完整报告已保存: {report_path}")

    print("\n" + "=" * 70)
    print("✅ GLP-1减重产品上市预测完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
